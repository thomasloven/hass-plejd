from builtins import property
import pyplejd
from pyplejd.interface import PlejdDevice

from homeassistant.core import callback
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    if not (data := hass.data[DOMAIN].get(config_entry.entry_id)):
        return
    devices: list[PlejdDevice] = data["devices"]

    entities = []
    for dev in devices:
        if dev.outputType == pyplejd.SWITCH:
            switch = PlejdSwitch(dev)
            entities.append(switch)
    async_add_entities(entities, False)


class PlejdSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device):
        SwitchEntity.__init__(self)
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
    def available(self):
        return self._data.get("available", False)

    @property
    def is_on(self):
        return self._data.get("state", False)

    async def async_turn_on(self, **_):
        await self.device.turn_on(None)
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
