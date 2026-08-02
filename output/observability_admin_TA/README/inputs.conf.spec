[observability_object://<name>]
account = 
index = (Default: observability_admin)
interval = Time interval of the data input, in seconds. (Default: 300)
object_type = The type of object to be ingested

[observability_audit_event://<name>]
account = The Observability account (realm/token) to authenticate against the Audit Events API.
index = (Default: observability_admin)
interval = Time interval of the data input, in seconds. (Default: 300)
sf_event_category = The audit event category to retrieve (maps to the API's sf_eventCategory parameter).
sf_event_type = Optional event type filter (maps to the API's sf_eventType). Example values: AUDIT -> HttpRequest, SessionLog, DetectorLog; CUSTOMER_AUDIT -> DASHBOARD, DETECTOR, DASHBOARD_GROUP, ORG_MEMBER, INTEGRATION, SLO. Leave blank to retrieve all event types for the selected category.
