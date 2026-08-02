# Observability Admin TA

Developed using the Splunk UCC Framework with support from the UCC Framework Team (UCC Framework Documentation), this Splunk Technology Add-on (TA) bridges platform data from Splunk Observability into Splunk Core.

The primary objective is to enable administrators to monitor their platforms from a single, unified tool (Splunk Core), leveraging its superior data transformation and customizable alerting capabilities. The app includes modular inputs and dashboards for seamless integration and functionality.

## Popular Use Cases
- Alerting on Token Expiry: Provides custom alerting options for token expiration, overcoming the limitations of non-configurable default alerting in Splunk Observability.
- Monitoring Synthetic Status: Offers visibility into the health and performance of synthetic monitoring.
- Change Auditing: Simplifies the process of retrieving and auditing changes to objects within Splunk Observability, making this data point readily accessible.

## How to build
- When a new commit is made, the Github action will package and build the app using the latest UCC version

## Deploy locally
Build the add-on first, then deploy the generated app with root privileges:

```bash
ucc-gen build -v --ta-version 1.2.3
sudo ./deploy.sh
```

`deploy.sh` installs `output/observability_admin_TA` into
`/opt/splunk/etc/apps/observability_admin_TA`. Use `--destination` or the
`SPLUNK_APPS_DIR` environment variable for a non-default Splunk path.

## Audit event checkpoints
The `observability_audit_event` input stores one checkpoint per input in the
Splunk KV Store collection `observability_admin_ta_audit_event_checkpoints`.
The checkpoint is advanced only after a complete API fetch and successful event
writing. A failed request (including rate limiting) leaves it unchanged so the
same window is retried. The first run backfills seven days. Checkpoints are
timestamps in milliseconds; if events appear late, the next window starts just
after the newest event actually returned rather than jumping to the poll time.
