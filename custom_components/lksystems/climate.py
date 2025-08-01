import logging
from datetime import timedelta
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from .lk_api import LkSystemsAPI

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config = entry.data

    api = LkSystemsAPI(config["host"], config["username"], config["password"])
    coordinator = LkSystemsCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    rooms = api.get_rooms()
    active_flags = api._jsondata.get("active", []) if api._jsondata else []
    _LOGGER.info("LK Systems climate rooms detected: %s", rooms)

    entities = []
    tid = 1
    room_index = 0
    for i in range(len(active_flags)):
        if tid - 1 < len(active_flags):
            if room_index < len(rooms):
                room = rooms[room_index]
                if active_flags[tid - 1] == "1":
                    entities.append(LkSystemsClimate(coordinator, tid - 1, room, tid))
                    room_index += 1
            tid += 1

    async_add_entities(entities, True)

class LkSystemsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: LkSystemsAPI):
        super().__init__(
            hass,
            _LOGGER,
            name="LK Systems Climate Coordinator",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self):
        await self.api.async_update(self.hass)

class LkSystemsClimate(CoordinatorEntity, ClimateEntity):
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 7.0
    _attr_max_temp = 40.0
    _attr_hvac_mode = HVACMode.HEAT
    _attr_should_poll = False

    def __init__(self, coordinator: LkSystemsCoordinator, index: int, room_name: str, tid: int):
        super().__init__(coordinator)
        self._api = coordinator.api
        self._index = index  # index in set_room_deg
        self._room_name = room_name
        self._tid = tid

        self._attr_name = f"{room_name} Thermostat"
        self._attr_unique_id = f"lksystems_climate_{room_name.lower().replace(' ', '_')}"

    @property
    def current_temperature(self):
        return self._api.get_temperature(self._room_name)

    @property
    def target_temperature(self):
        room_data = self._api._jsondata
        if room_data:
            try:
                return float(room_data["set_room_deg"][self._index]) / 100
            except Exception as e:
                _LOGGER.warning("Failed to get set temperature for %s: %s", self._room_name, e)
        return None

    @property
    def extra_state_attributes(self):
        return {"tid": self._tid}

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self.hass.async_add_executor_job(
            self._api.set_room_temperature,
            self._tid - 1,
            temperature
        )
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()  # Safe here because we're in async context
