import logging
import pyplejd
from pyplejd.interface import PlejdDevice

from homeassistant.core import callback
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    if not (data := hass.data[DOMAIN].get(config_entry.entry_id)):
        return
    devices: list[PlejdDevice] = data["devices"]

    entities = []
    for dev in devices:
        if dev.outputType == pyplejd.LIGHT:
            light = PlejdLight(dev)
            entities.append(light)
    async_add_entities(entities, False)


class PlejdLight(LightEntity):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device):
        LightEntity.__init__(self)
        self.device: PlejdDevice = device
        self.listener = None
        self._data = {}

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, f"{self.device.BLEaddress}", f"{self.device.address}")
            },
            "name": self.device.name,
            "manufacturer": "Plejd",
            "model": self.device.hardware,
            "suggested_area": self.device.room,
            "sw_version": f"{self.device.firmware}",
        }

    @property
    def unique_id(self):
        return f"{self.device.BLEaddress}:{self.device.address}"

    @property
    def supported_color_modes(self):
        modes = {ColorMode.ONOFF}
        if self.device.colortemp:
            modes.add(ColorMode.COLOR_TEMP)
        if self.device.dimmable:
            modes.add(ColorMode.BRIGHTNESS)
        return modes

    @property
    def min_color_temp_kelvin(self) -> int:
        if self.device.colortemp:
            return self.device.colortemp[0]
        return None

    @property
    def max_color_temp_kelvin(self) -> int:
        if self.device.colortemp:
            return self.device.colortemp[1]
        return None

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
    def color_temp_kelvin(self):
        return self._data.get("colortemp", None)

    @property
    def color_mode(self):
        if self.device.colortemp:
            return ColorMode.COLOR_TEMP
        if self.device.dimmable:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    async def async_turn_on(self, brightness=None, color_temp=None, **_):
        await self.device.turn_on(brightness, color_temp)
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
