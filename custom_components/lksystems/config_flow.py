import voluptuous as vol
import requests
import logging
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class LkSystemsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(self._validate_input, user_input)
                return self.async_create_entry(title="LK Systems", data=user_input)
            except Exception as e:
                _LOGGER.exception("Connection failed: %s", e)
                errors["base"] = "connection_error"

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    def _validate_input(self, data):
        url = f"http://{data[CONF_HOST]}/main.json"
        auth = (data[CONF_USERNAME], data[CONF_PASSWORD])
        response = requests.get(url, auth=auth, timeout=10)
        response.raise_for_status()
