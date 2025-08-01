import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from .lk_api import LkSystemsAPI

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    config = entry.data

    api = LkSystemsAPI(config["host"], config["username"], config["password"])

    coordinator = LkSystemsCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    rooms = api.get_rooms()
    _LOGGER.info("LK Systems rooms detected: %s", rooms)

    sensors = [LkSystemSensor(coordinator, room) for room in rooms]
    async_add_entities(sensors, True)

class LkSystemsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api):
        super().__init__(
            hass,
            _LOGGER,
            name="LK Systems API Coordinator",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self):
        await self.api.async_update(self.hass)

class LkSystemSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: LkSystemsCoordinator, room: str):
        super().__init__(coordinator)
        self._api = coordinator.api
        self._room = room

        self._attr_name = room
        self._attr_unique_id = f"lksystems_{room.lower().replace(' ', '_')}"
        self._attr_icon = "mdi:thermometer"
        self._attr_native_unit_of_measurement = "°C"

    @property
    def native_value(self):
        return self._api.get_temperature(self._room)
