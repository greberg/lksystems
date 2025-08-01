import logging
import requests
from urllib.parse import urlencode


_LOGGER = logging.getLogger(__name__)

class LkSystemsAPI:
    def __init__(self, host, username, password):
        self.url = f"http://{host}/main.json"
        self.auth_values = (username, password)
        self._jsondata = None

    async def async_update(self, hass):
        try:
            self._jsondata = await hass.async_add_executor_job(self._fetch_json)
            _LOGGER.debug("LK API data keys: %s", list(self._jsondata.keys()))
        except Exception as e:
            _LOGGER.warning("LK API fetch failed. Keeping previous data. Error: %s", e)

    def _fetch_json(self):
        response = requests.get(self.url, auth=self.auth_values, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_temperature(self, room_name):
        if not self._jsondata:
            return None
        try:
            for i, raw_name in enumerate(self._jsondata.get("name", [])):
                decoded = bytes.fromhex(raw_name).decode("ascii").strip()
                if decoded == room_name:
                    return float(self._jsondata["get_room_deg"][i]) / 100
        except Exception as e:
            _LOGGER.warning("Failed to decode temperature for %s: %s", room_name, e)
        return None

    def set_room_temperature(self, room_id, temperature):
        temp_value = int(round(temperature * 100))
        params = {
            "tid": room_id + 1,
            "set_room_deg": temp_value

        }
        try:
            base_url = self.url.replace("/main.json", "")
            full_url = f"{base_url}/update.cgi?{urlencode(params)}"
            _LOGGER.debug("Full request URL: %s", full_url)
            requests.get(f"{base_url}/update.cgi", auth=self.auth_values, params=params, timeout=5)
        except Exception as e:
            raise RuntimeError(f"Failed to set temperature: {e}")

    def get_room(self, room_id):
        return next((r for r in self.rooms if r["id"] == room_id), None)

    def get_rooms(self):
        if not self._jsondata:
            _LOGGER.warning("No JSON data when trying to get rooms")
            return []
        try:
            raw_names = self._jsondata.get("name", [])
            decoded = []
            for hex_str in raw_names:
                try:
                    name = bytes.fromhex(hex_str).decode("ascii").strip()
                    if not name or name.lower() == "thermostat":
                        continue  # Skip placeholders
                    if name not in decoded:
                        decoded.append(name)
                except Exception as e:
                    _LOGGER.warning("Failed to decode hex string '%s': %s", hex_str, e)
            return decoded
        except Exception as e:
            _LOGGER.error("Error in get_rooms: %s", e)
            return []
