import import_declare_test
import requests
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler
from splunktaucclib.rest_handler.error import RestError


def _validate_token_realm(token: str, realm: str):
    # Some code to validate the API key.
    # Should return nothing if the configuration is valid.
    # Should raise an exception splunktaucclib.rest_handler.error.RestError if the configuration is not valid.
    BASE_URL = f"https://api.{realm}.signalfx.com"
    endpoint = f"{BASE_URL}/v2/detector"
    headers = {"Content-Type": "application/json", "X-SF-TOKEN": token}
    params = {"limit": 1, "offset": 0}
    try:
        response = requests.get(endpoint, headers=headers, params=params)
    except:
        raise RestError(400, "Realm was not recognized")
    
    if not (200 <= response.status_code < 300):
        raise RestError(400, "Account details are incorrect, could not successfully authenticate with the Observability API, re-check your Token and Realm")


class observability_account_validator(AdminExternalHandler):
    def __init__(self, *args, **kwargs):
        AdminExternalHandler.__init__(self, *args, **kwargs)

    def handleList(self, confInfo):
        AdminExternalHandler.handleList(self, confInfo)

    def handleEdit(self, confInfo):
        _validate_token_realm(
            self.payload.get("token"), self.payload.get("realm"),
        )
        AdminExternalHandler.handleEdit(self, confInfo)

    def handleCreate(self, confInfo):
        _validate_token_realm(
            self.payload.get("token"), self.payload.get("realm"),
        )
        AdminExternalHandler.handleCreate(self, confInfo)

    def handleRemove(self, confInfo):
        AdminExternalHandler.handleRemove(self, confInfo)