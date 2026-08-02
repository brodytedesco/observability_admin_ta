import json
import logging
import time
from datetime import datetime, timezone
import requests
import import_declare_test
from solnlib import conf_manager, log
from solnlib.modular_input.checkpointer import KVStoreCheckpointer
from splunklib import modularinput as smi

# Reuse the generic account/logging helpers from the existing object input
# helper so account conf lookup and per-input logger naming stay consistent
# across the add-on (these are not object-specific).
from observability_object_helper import (
    get_key_name,
    logger_for_input,
    get_account_realm_token,
)


ADDON_NAME = "observability_admin_TA"
SOURCETYPE = "observability:audit_event_api:json"
CHECKPOINT_COLLECTION = "observability_admin_ta_audit_event_checkpoints"

# Constants
DEFAULT_BACKFILL_MS = 7 * 24 * 60 * 60 * 1000  # 7 days, matches API default startTime
PAGE_LIMIT = 1000
OFFSET_CAP = 10000  # API caps queryable results at offset+limit <= 10000


def _parse_timestamp_ms(value):
    """Coerce an audit event ``timestamp`` to integer milliseconds.

    The Audit Events API documents ``timestamp`` as an int64 of milliseconds
    since the Unix epoch, but live responses frequently serialize it as a JSON
    string (e.g. ``"1733443200000"``). Treating only true numbers as valid
    left ``_time`` unset for those events, so Splunk fell back to the ingestion
    ("now") time instead of the event's actual creation time. This helper
    normalizes ints, floats, and numeric strings (epoch-ms, or −10³ fall-back to
    epoch-seconds) and ISO-8601 strings to epoch ms, returning None only when
    the value is genuinely missing or unparseable.
    """
    if value is None or isinstance(value, bool):
        return None

    # Numeric (int or float). The API uses epoch-milliseconds, but tolerate
    # epoch-seconds (10-digit) and epoch-microseconds (≥19 digits) too.
    if isinstance(value, (int, float)):
        ms = int(value)
        return _ms_from_numeric(ms)

    # String: could be a quoted epoch number or an ISO-8601 datetime.
    s = str(value).strip().strip('"').strip("'").strip()
    if not s:
        return None

    # Pure numeric string.
    try:
        return _ms_from_numeric(int(float(s)))
    except ValueError:
        pass

    # ISO-8601 (e.g. 2024-12-01T12:00:00Z or with fractional/offset).
    iso = s
    # strptime handles Z only on 3.11+; normalize to +00:00 for portability.
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            dt = datetime.strptime(iso, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue

    return None


def _ms_from_numeric(ms: int) -> int:
    """Normalize a numeric epoch value to milliseconds, guarded for sanity."""
    # epoch-seconds (10 digits) → ms; epoch-ms (13 digits) → as-is;
    # epoch-microseconds/nanoseconds also plausible but we only scale seconds.
    if ms <= 0:
        return None
    if ms < 10_000_000_000:          # before ~2286 in seconds, i.e. epoch-seconds
        ms = ms * 1000
    return ms


def get_checkpointer(session_key: str, logger: logging.Logger) -> KVStoreCheckpointer:
    """Instantiate a KVStore-backed checkpointer dedicated to audit events."""
    return KVStoreCheckpointer(
        CHECKPOINT_COLLECTION,
        session_key,
        ADDON_NAME,
        owner="nobody",
    )


def get_audit_events_endpoint(realm: str) -> str:
    return f"https://api.{realm}.signalfx.com/v2/audit/events"


def get_sourcetype() -> str:
    return SOURCETYPE


def fetch_audit_events(
    realm: str,
    token: str,
    sf_event_category: str,
    sf_event_type: str,
    start_time_ms: int,
    end_time_ms: int,
    logger: logging.Logger,
):
    """Query the /v2/audit/events API for one [start, end] time window.

    Paginates with offset/limit (ascending by timestamp so the checkpoint
    advances monotonically). Honors the API's 10,000 offset+limit cap and
    tolerates 429/503 by returning what was collected without claiming the
    window was fully drained.

    Returns a dict with:
      - events: list of audit event objects collected
      - max_timestamp: highest ``timestamp`` seen (ms) or None if none
      - drained: True iff the window was fully consumed (no truncation)
      - success: True iff no transport error interrupted the fetch
    """
    endpoint = get_audit_events_endpoint(realm)
    headers = {"Content-Type": "application/json", "X-SF-TOKEN": token}

    offset = 0
    limit = PAGE_LIMIT
    events = []
    max_timestamp = None
    drained = False
    success = True
    process_start = time.time()

    while True:
        params = {
            "sf_eventCategory": sf_event_category,
            "startTime": start_time_ms,
            "endTime": end_time_ms,
            "sortBy": "timestamp",  # ascending: oldest first
            "limit": limit,
            "offset": offset,
        }
        # Only send sf_eventType when the user provided one.
        if sf_event_type:
            params["sf_eventType"] = sf_event_type

        try:
            response = requests.get(
                endpoint, headers=headers, params=params, timeout=60
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # 429 / 503 (and any transport error): do not claim success and do
            # not let the caller advance the checkpoint past this failure. The
            # next scheduled interval retries the same start_time.
            log.log_exception(
                logger,
                e,
                "AuditEventsRequestError",
                msg_before=(
                    f"Error fetching audit events at offset={offset} "
                    f"for window [{start_time_ms},{end_time_ms}]:"
                ),
            )
            success = False
            break

        data = response.json()
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("results", [])
        else:
            logger.error("Unexpected response format from /v2/audit/events")
            success = False
            break

        for evt in results:
            ts = _parse_timestamp_ms(evt.get("timestamp"))
            if ts is not None and (max_timestamp is None or ts > max_timestamp):
                max_timestamp = ts

        events.extend(results)
        logger.info(
            f"audit events pagination: fetched={len(results)} "
            f"offset={offset} limit={limit} total={len(events)}"
        )

        if len(results) < limit:
            # Fewer than a full page => window fully consumed.
            drained = True
            break

        if offset >= OFFSET_CAP - limit:
            # Next page would exceed the 10,000 offset+limit cap. The window
            # still has data we cannot reach, so do not mark drained; do not
            # advance the checkpoint past the unread data.
            logger.warning(
                "Hit the 10,000 result offset cap for audit events window "
                f"[{start_time_ms},{end_time_ms}]; events were likely missed "
                "in this window and will be re-queried on the next poll."
            )
            break

        offset += limit

    time_taken = str(round((time.time() - process_start) * 1000))
    log.log_event(
        logger,
        {
            "message": "audit events fetch finished",
            "time_taken": f"{time_taken}ms",
            "fetched": len(events),
            "drained": drained,
            "success": success,
        },
    )
    return {
        "events": events,
        "max_timestamp": max_timestamp,
        "drained": drained,
        "success": success,
    }


def validate_input(definition: smi.ValidationDefinition):
    # Minimal, consistent with the existing observability_object helper.
    return False


def stream_events(inputs: smi.InputDefinition, event_writer: smi.EventWriter):
    for input_name, input_item in inputs.inputs.items():
        normalized_input_name = get_key_name(input_name)
        logger = logger_for_input(normalized_input_name)
        try:
            session_key = inputs.metadata["session_key"]
            account = input_item.get("account")
            sf_event_category = input_item.get("sf_event_category")
            sf_event_type = input_item.get("sf_event_type") or ""
            index = input_item.get("index")
            source_type = get_sourcetype()

            realm, token = get_account_realm_token(session_key, account, logger)

            log.modular_input_start(logger, normalized_input_name)

            # Capture the end of the window once per run so it stays bounded
            # across pagination.
            now_ms = int(time.time() * 1000)
            end_time_ms = now_ms

            # Resolve checkpoint: 7-day backfill on first run (no checkpoint).
            # Older versions of this helper persisted a bare int timestamp;
            # the current format is {"state": <timestamp_ms>}. Handle both
            # so a legacy checkpoint does not break the input.
            checkpointer = get_checkpointer(session_key, logger)
            checkpoint_state = checkpointer.get(normalized_input_name)
            if isinstance(checkpoint_state, dict):
                saved = checkpoint_state.get("state")
            else:
                # Older versions of the input wrote the timestamp directly.
                # KVStoreCheckpointer deserializes that value as an int (or,
                # for some older records, a numeric string).
                saved = checkpoint_state
            try:
                start_time_ms = int(saved)
            except (TypeError, ValueError):
                start_time_ms = None
            if start_time_ms is not None and start_time_ms > 0:
                logger.info(
                    f"Resuming audit events from checkpoint start_time={start_time_ms}"
                )
            else:
                start_time_ms = now_ms - DEFAULT_BACKFILL_MS
                logger.info(
                    f"No checkpoint for audit events; using 7-day backfill "
                    f"start_time={start_time_ms}"
                )

            # Guard against clock skew / stale checkpoints ahead of now.
            if start_time_ms > end_time_ms:
                start_time_ms = end_time_ms

            result = fetch_audit_events(
                realm,
                token,
                sf_event_category,
                sf_event_type,
                start_time_ms,
                end_time_ms,
                logger,
            )

            if not result["success"]:
                # Transport error mid-fetch: do not write partial results and
                # do not advance the checkpoint, so the next poll cleanly
                # retries the same window (no data gap, no duplicates).
                logger.warning(
                    "Audit events fetch did not complete successfully; "
                    "checkpoint not advanced. Next interval will retry."
                )
                log.modular_input_end(logger, normalized_input_name)
                continue

            events = result["events"]
            for evt in events:
                # Use the event's own ``timestamp`` field (epoch ms) as the
                # Splunk _time so each record is indexed at the moment it was
                # created (user logged in, dashboard created, ...) rather than
                # the moment we polled the API. The API may return the value
                # as a JSON string, so coerce it robustly.
                ms = _parse_timestamp_ms(evt.get("timestamp"))
                evt_time = ms / 1000.0 if ms is not None else None
                if ms is None:
                    logger.warning(
                        "Audit event has no parseable timestamp; indexing "
                        f"event id={evt.get('id')!r} with the current time."
                    )
                event_writer.write_event(
                    smi.Event(
                        data=json.dumps(evt, ensure_ascii=False, default=str),
                        index=index,
                        sourcetype=source_type,
                        time=evt_time,
                    )
                )

            log.events_ingested(
                logger, input_name, source_type, len(events), index
            )

            # Advance the checkpoint. If the window was fully drained, jump to
            # end_time_ms so the next poll starts fresh from "now". If the
            # 10k cap truncated the window, advance just past the newest event
            # we actually saw so the next poll continues from there.
            if result["drained"] and result["max_timestamp"] is None:
                new_checkpoint = end_time_ms
            elif result["max_timestamp"] is not None:
                # Advance from the last event, rather than jumping to the
                # request end.  The API can return events late, and jumping
                # to end_time_ms would permanently skip those events on the
                # next poll.  +1 keeps the normal inclusive API window from
                # re-ingesting the boundary event.
                new_checkpoint = int(result["max_timestamp"]) + 1
            else:
                # No events returned and not truncated => nothing happened;
                # still advance to end_time_ms to avoid re-querying the empty
                # window.
                new_checkpoint = end_time_ms

            if not events:
                logger.info(
                    f"no events newer than {start_time_ms}; "
                    f"advancing checkpoint to {new_checkpoint}"
                )

            # Persist as {"state": <ts_ms>} for self-describing, forward-
            # compatible serialization.
            checkpointer.update(
                normalized_input_name, {"state": new_checkpoint}
            )
            logger.info(
                f"Checkpoint advanced to {new_checkpoint} "
                f"(drained={result['drained']}, "
                f"max_timestamp={result['max_timestamp']})"
            )

            log.modular_input_end(logger, normalized_input_name)
        except Exception as e:
            log.log_exception(
                logger,
                e,
                "IngestionError",
                msg_before="Error processing audit events input:",
            )