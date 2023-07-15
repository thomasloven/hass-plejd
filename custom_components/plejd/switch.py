from builtins import property
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from . import pyplejd
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    devices = hass.data[DOMAIN]["devices"].get(config_entry.entry_id, [])

    entities = []
    for d in devices:
        dev = devices[d]
        if dev.type == pyplejd.SWITCH:
            coordinator = Coordinator(hass, dev)
            dev.updateCallback = coordinator.async_set_updated_data
            switch = PlejdSwitch(coordinator, dev)
            entities.append(switch)
    async_add_entities(entities, False)

class Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, device):
        super().__init__(hass, _LOGGER, name="Plejd Coordinator")
        self.device = device

class PlejdSwitch(SwitchEntity, CoordinatorEntity):

    _attr_has_entity_name = True

    def __init__(self, coordinator, device):
        CoordinatorEntity.__init__(self, coordinator)
        SwitchEntity.__init__(self)
        self.device = device

    @property
    def _data(self):
        return self.coordinator.data or {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.device.BLE_address}")},
            "name": self.device.name,
            "manufacturer": "Plejd",
            "model": self.device.model,
            #"connections": ???,
            "suggested_area": self.device.room,
            "sw_version": f"{self.device.firmware} ({self.device.hardwareId})",
        }

    @property
    def available(self):
        return self.device.available
    
    @property
    def unique_id(self):
        return f"{self.device.BLE_address}:{self.device.address}"

    @property
    def is_on(self):
        return self._data.get("state")

    async def async_turn_on(self, **_):
        await self.device.turn_on(None)
        pass

    async def async_turn_off(self, **_):
        await self.device.turn_off()
        pass

    
