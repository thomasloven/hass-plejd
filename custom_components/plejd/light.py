from builtins import property
import logging
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)

DOMAIN = "plejd"

async def async_setup_entry(hass, config_entry, async_add_entities):
    devices = hass.data[DOMAIN]["devices"]

    entities = []
    for d in devices:
        dev = devices[d]
        if dev.type == "light":
            coordinator = Coordinator(hass, dev)
            async def updateCallback(data):
                coordinator.async_set_updated_data(data)
            dev.updateCallback = updateCallback
            light = PlejdLight(coordinator, dev)
            entities.append(light)
    async_add_entities(entities, False)

class Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, device):
        super().__init__(hass, _LOGGER, name="Plejd Coordinator")
        self.device = device

class PlejdLight(LightEntity, CoordinatorEntity):
    def __init__(self, coordinator, device):
        CoordinatorEntity.__init__(self, coordinator)
        LightEntity.__init__(self)
        self.device = device

    @property
    def _data(self):
        return self.coordinator.data or {}

    @property
    def available(self):
        return self._data.get("state", None) is not None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.BLE_address)},
            "name": self.device.name,
            "manufacturer": "Plejd",
            "model": f"{self.device.model} ({self.device.hardwareId})",
            #"connections": ???,
            "suggested_area": self.device.room,
            "sw_version": self.device.firmware,
        }

    @property
    def has_entity_name(self):
        return True
    
    @property
    def name(self):
        return None

    @property
    def unique_id(self):
        return self.device.BLE_address

    @property
    def is_on(self):
        return self._data.get("state")

    @property
    def brightness(self):
        return self._data.get("dim",0)

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

    
