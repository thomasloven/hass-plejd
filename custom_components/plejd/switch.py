from builtins import property
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

import pyplejd
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    if config_entry.entry_id not in hass.data[DOMAIN]:
        return
    devices = hass.data[DOMAIN][config_entry.entry_id]["devices"]

    entities = []
    for dev in devices:
        if dev.outputType == pyplejd.SWITCH:
            coordinator = Coordinator(hass, dev)
            dev.subscribe_state(coordinator.async_set_updated_data)
            switch = PlejdSwitch(coordinator, dev)
            entities.append(switch)
    async_add_entities(entities, False)


class Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, device):
        super().__init__(hass, _LOGGER, name="Plejd Coordinator")
        self.device = device


class PlejdSwitch(SwitchEntity, CoordinatorEntity):
    _attr_has_entity_name = True
    _attr_name = None

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
            "identifiers": {(DOMAIN, f"{self.device.BLEaddress}")},
            "name": self.device.name,
            "manufacturer": "Plejd",
            "model": self.device.hardware,
            # "connections": ???,
            "suggested_area": self.device.room,
            "sw_version": f"{self.device.firmware}",
        }

    @property
    def available(self):
        return self._data.get("available", False)

    @property
    def unique_id(self):
        return f"{self.device.BLEaddress}:{self.device.address}"

    @property
    def is_on(self):
        return self._data.get("state", False)

    async def async_turn_on(self, **_):
        await self.device.turn_on(None)
        pass

    async def async_turn_off(self, **_):
        await self.device.turn_off()
        pass
