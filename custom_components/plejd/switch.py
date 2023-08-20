from builtins import property
import pyplejd

from homeassistant.core import callback
from homeassistant.components.switch import SwitchEntity


from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    if config_entry.entry_id not in hass.data[DOMAIN]:
        return
    devices = hass.data[DOMAIN][config_entry.entry_id]["devices"]

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
        self.device = device
        self.listener = None
        self._data = {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.device.BLEaddress}")},
            "name": self.device.name,
            "manufacturer": "Plejd",
            "model": self.device.hardware,
            # "connections": ???,
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
