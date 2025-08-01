from homeassistant import config_entries
import voluptuous as vol
import requests
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN, CONF_SENSORS, CONF_HOST, CONF_USERNAME, CONF_PASSWORD

class LkSystemsOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._rooms = []

    async def async_step_init(self, user_input=None):
        sensors = self.config_entry.options.get(
            CONF_SENSORS, self.config_entry.data.get(CONF_SENSORS, [])
        )
        try:
            self._rooms = await self.hass.async_add_executor_job(self._fetch_rooms)
        except Exception:
            self._rooms = sensors

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_SENSORS, default=self._rooms): vol.All(cv.ensure_list, [vol.In(self._rooms)])

            })
        )

    def _fetch_rooms(self):
        url = f"http://{self.config_entry.data[CONF_HOST]}/main.json"
        auth = (
            self.config_entry.data[CONF_USERNAME],
            self.config_entry.data[CONF_PASSWORD]
        )
        response = requests.get(url, auth=auth, timeout=10)
        data = response.json()
        decoded = []

        for hex_name in data.get("name", []):
            try:
                name = bytes.fromhex(hex_name).decode("ascii").strip()
                if name not in decoded:
                    decoded.append(name)
            except Exception:
                continue

        return decoded

def async_get_options_flow(config_entry):
    return LkSystemsOptionsFlowHandler(config_entry)
