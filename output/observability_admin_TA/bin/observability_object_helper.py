import json
import logging
import time
import requests
import import_declare_test
from solnlib import conf_manager, log, credentials
from splunklib import modularinput as smi


ADDON_NAME = "observability_admin_TA"

def get_key_name(input_name: str) -> str:
    # `input_name` is a string like "example://<input_name>".
    return input_name.split("/")[-1]


def logger_for_input(input_name: str) -> logging.Logger:
    return log.Logs().get_logger(f"{ADDON_NAME.lower()}_{input_name}")

# Returns realm/token for the account currently ingesting data
def get_account_realm_token(session_key: str, account_name: str, logger: logging.Logger):
    cfm = conf_manager.ConfManager(
        session_key,
        ADDON_NAME,
        realm=f"__REST_CREDENTIAL__#{ADDON_NAME}#configs/conf-observability_admin_ta_account",
    )
    account_conf_file = cfm.get_conf("observability_admin_ta_account")

    return (account_conf_file.get(account_name).get("realm"),account_conf_file.get(account_name).get("token"))


def get_data_from_api(logger: logging.Logger, api_key: str):
    logger.info("Getting data from an external API")
    dummy_data = [
        {"line1": "hello"},
        {"line2": "world"},
    ]
    return dummy_data

def splunk_observability_get_endpoint(type, realm):
    BASE_URL = f"https://api.{realm}.signalfx.com"
    ENDPOINT = ""
    types = {
        "chart": f"{BASE_URL}/v2/chart",
        "dashboard": f"{BASE_URL}/v2/dashboard",
        "detector": f"{BASE_URL}/v2/detector",
        "heartbeat": f"{BASE_URL}/v2/detector",
        "synthetic": f"{BASE_URL}/v2/synthetics/tests",
        "alert": f"{BASE_URL}/v2/incident",
        "token": f"{BASE_URL}/v2/token",
    }
    for type_key in types:
        if type.lower() == type_key.lower():
            ENDPOINT = types.get(type_key)
    return ENDPOINT

def splunk_observability_get_sourcetype(type):
    sourcetypes = {
        "alert": "observability:alert_api:json",
        "chart": "observability:chart_api:json",
        "dashboard": "observability:dashboard_api:json",
        "detector": "observability:detector_api:json",
        "synthetic": "observability:synthetic_api:json",
        "synthetic_detailed": "observability:synthetic_detailed_api:json",
        "token": "observability:token_api:json",
    }
    for type_key in sourcetypes:
        if type.lower() == type_key.lower():
            return sourcetypes.get(type_key)

def splunk_observability_get_objects(type, realm, token, logger):
    TOKEN = token
    ENDPOINT_URL = splunk_observability_get_endpoint(type, realm)
    limit = 200
    offset = 0
    pagenation = True
    headers = {"Content-Type": "application/json", "X-SF-TOKEN": TOKEN}
    processStart = time.time()
    objects = []

    while pagenation:
        params = {"limit": limit, "offset": offset}
        try:
            response = requests.get(ENDPOINT_URL, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.log_exception(logger, e, "RequestError", msg_before="Error fetching data:")
            return []

        data = response.json()

        if isinstance(data, list):
            results = data
        elif isinstance(data, dict):
            results = data.get("results", [])
        else:
            logger.error("Unexpected response format")

        objects.extend(results)

        logger.info(f"pagenating {type} result 'length': {len(results)} , offset: {offset}, limit {limit}")
        if len(results) < limit:
            pagenation = False
            
        # too many objects to query, splunk will max out at 10,000
        elif (offset >= 10000-limit):
            pagenation = False
            logger.warn("Cannot ingest more than 10,000 objects")
        else:
            offset += limit

    count = offset+len(results)
    timeTakenProcess = str(round((time.time() - processStart) * 1000))
    log.log_event(logger, {"message": f"{type} ingest finished", "time_taken": f"{timeTakenProcess}ms", "ingested": count})
    return objects

def splunk_observability_get_objects_synthetics(type, realm, token, logger):
    processStart = time.time()
    BASE_URL = f"https://api.{realm}.signalfx.com"
    ENDPOINT_URL = f"{BASE_URL}/v2/synthetics/tests"
    page = 1
    pagenating = True
    headers = {"Content-Type": "application/json", "X-SF-TOKEN": token}
    synthetics_objects = []

    while pagenating:
        params = {"perPage": 100, "page": page}
        try:
            response = requests.get(ENDPOINT_URL, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.log_exception(logger, e, "RequestError", msg_before="Error fetching synthetic data:")
            return []

        data = response.json()
        tests = data["tests"]
        for test in tests:
            synthetic = {"id": test["id"], "type": test["type"]}
            SYNTHETIC_TYPE = synthetic["type"]
            SYNTHETIC_ID = synthetic["id"]
            detail_url = f"{BASE_URL}/v2/synthetics/tests/{SYNTHETIC_TYPE}/{SYNTHETIC_ID}"
            if type=="synthetic_detailed":
                try:
                    detail_response = requests.get(detail_url, headers=headers)
                    detail_response.raise_for_status()
                    synthetics_objects.append(detail_response.json())
                except requests.exceptions.RequestException as e:
                    log.log_exception(logger, e, "RequestError", msg_before=f"Error fetching synthetic details for ID: {SYNTHETIC_ID}")
            else:
                synthetics_objects.append(test)
        pagenating = data.get("nextPageLink") is not None
        page += 1

    timeTakenProcess = str(round((time.time() - processStart) * 1000))
    log.log_event(logger, {"message": "synthetic ingest finished", "time_taken": f"{timeTakenProcess}ms", "ingested": len(synthetics_objects)})

    return synthetics_objects

def validate_input(definition: smi.ValidationDefinition):
    return False

def stream_events(inputs: smi.InputDefinition, event_writer: smi.EventWriter):
    for input_name, input_item in inputs.inputs.items():
        normalized_input_name = input_name.split("/")[-1]
        logger = logger_for_input(normalized_input_name)
        try:
            session_key = inputs.metadata["session_key"]
            observability_realm = input_item.get("realm")
            observability_type = input_item.get("object_type")
            observability_account = input_item.get("account")
            observability_realm, observability_token = get_account_realm_token(session_key, observability_account, logger)

            
            log.modular_input_start(logger, normalized_input_name)

            if observability_type.lower() == "synthetic_detailed" or observability_type.lower() == "synthetic":
                objects = splunk_observability_get_objects_synthetics(observability_type, observability_realm, observability_token, logger)
            else:
                objects = splunk_observability_get_objects(observability_type, observability_realm, observability_token, logger)
            
            source_type = splunk_observability_get_sourcetype(observability_type)
            for obj in objects:
                logger.debug(f"DEBUG EVENT {observability_type} :{json.dumps(obj)}")
                event_writer.write_event(
                    smi.Event(
                        data=json.dumps(obj, ensure_ascii=False, default=str),
                        index=input_item.get("index"),
                        sourcetype=source_type,
                    )
                )
            log.events_ingested(logger, input_name, source_type, len(objects), input_item.get("index"))
            log.modular_input_end(logger, normalized_input_name)
        except Exception as e:
            log.log_exception(logger, e, "IngestionError", msg_before="Error processing input:")
