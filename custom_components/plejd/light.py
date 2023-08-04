import logging
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import pyplejd
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    devices = hass.data[DOMAIN]["devices"].get(config_entry.entry_id, [])

    entities = []
    for dev in devices:
        if dev.outputType == pyplejd.LIGHT:
            coordinator = Coordinator(hass, dev)
            dev.subscribe_state(coordinator.async_set_updated_data)
            light = PlejdLight(coordinator, dev)
            entities.append(light)
    async_add_entities(entities, False)


class Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, device):
        super().__init__(hass, _LOGGER, name="Plejd Coordinator")
        self.device = device


class PlejdLight(LightEntity, CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device):
        CoordinatorEntity.__init__(self, coordinator)
        LightEntity.__init__(self)
        self.device = device

    @property
    def _data(self):
        return self.coordinator.data or {}

    @property
    def available(self):
        return self._data.get("available", False)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.device.BLEaddress}")},
            "name": self.device.room,
            "manufacturer": "Plejd",
            "model": self.device.hardware,
            # "connections": ???,
            "suggested_area": self.device.room,
            "sw_version": f"{self.device.firmware}",
        }

    @property
    def name(self):
        return self.device.name

    @property
    def unique_id(self):
        return f"{self.device.BLEaddress}:{self.device.address}"

    @property
    def is_on(self):
        return self._data.get("state", False)

    @property
    def brightness(self):
        return self._data.get("dim", 0)

    @property
    def supported_color_modes(self):
        if self.device.dimmable:
            return {ColorMode.BRIGHTNESS}
        return {ColorMode.ONOFF}

    @property
    def color_mode(self):
        if self.device.dimmable:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    async def async_turn_on(self, brightness=None, **_):
        await self.device.turn_on(brightness)
        pass

    async def async_turn_off(self, **_):
        await self.device.turn_off()
        pass
