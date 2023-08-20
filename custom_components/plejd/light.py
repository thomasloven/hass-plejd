import logging
from homeassistant.core import callback
from homeassistant.components.light import LightEntity, ColorMode

import pyplejd
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    if config_entry.entry_id not in hass.data[DOMAIN]:
        return
    devices = hass.data[DOMAIN][config_entry.entry_id]["devices"]

    entities = []
    for dev in devices:
        if dev.outputType == pyplejd.LIGHT:
            light = PlejdLight(dev)
            entities.append(light)
    async_add_entities(entities, False)


class PlejdLight(LightEntity):
    _attr_has_entity_name = True

    def __init__(self, device):
        LightEntity.__init__(self)
        self.device = device
        self.listener = None
        self._data = {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.device.BLEaddress}")},
            "name": self.device.room,
            "manufacturer": "Plejd",
            "model": self.device.hardware,
            "suggested_area": self.device.room,
            "sw_version": f"{self.device.firmware}",
        }

    @property
    def unique_id(self):
        return f"{self.device.BLEaddress}:{self.device.address}"

    @property
    def name(self):
        return self.device.name

    @property
    def supported_color_modes(self):
        if self.device.dimmable:
            return {ColorMode.BRIGHTNESS}
        return {ColorMode.ONOFF}

    @property
    def available(self):
        return self._data.get("available", False)

    @property
    def is_on(self):
        return self._data.get("state", False)

    @property
    def brightness(self):
        return self._data.get("dim", 0)

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

    @callback
    def _handle_state_update(self, data):
        self._data = data
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.listener = self.device.subscribe_state(self._handle_state_update)

    async def async_will_remove_from_hass(self) -> None:
        if self.listener:
            self.listener()
        return await super().async_will_remove_from_hass()
