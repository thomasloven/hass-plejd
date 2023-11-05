from datetime import timedelta

import pyplejd
from pyplejd.interface import PlejdScene, PlejdDevice

from homeassistant.components.event import EventEntity, EventDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.util import Throttle
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

SCENE_ACTIVATION_RATE_LIMIT = timedelta(seconds=2)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    if not (data := hass.data[DOMAIN].get(config_entry.entry_id)):
        return
    devices: list[PlejdDevice] = data["devices"]
    scenes: list[PlejdScene] = data["scenes"]

    entities = []

    for s in scenes:
        event = PlejdSceneEvent(s, config_entry.entry_id)
        entities.append(event)

    for dev in devices:
        if dev.outputType in pyplejd.SENSOR:
            for i, _ in enumerate(dev.inputAddress):
                event = PlejdButtonEvent(dev, i, config_entry.entry_id)
                entities.append(event)

    async_add_entities(entities, False)


class PlejdSceneEvent(EventEntity):
    _attr_has_entity_name = True
    _attr_event_types = ["activated"]

    def __init__(self, device: PlejdScene, entry_id):
        super().__init__()
        self.device: PlejdScene = device
        self.entry_id = entry_id
        self.listener = None

    @property
    def name(self):
        return self.device.title + " activated"

    @Throttle(SCENE_ACTIVATION_RATE_LIMIT)
    @callback
    def _handle_scene_activated(self):
        self._trigger_event("activated")
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.listener = self.device.subscribe_activate(self._handle_scene_activated)

    @property
    def unique_id(self):
        return f"{self.entry_id}:{self.device.index}:activated"

    async def async_will_remove_from_hass(self) -> None:
        if self.listener:
            self.listener()
        return await super().async_will_remove_from_hass()


class PlejdButtonEvent(EventEntity):
    _attr_has_entity_name = True
    _attr_event_types = ["press"]
    _attr_device_class = EventDeviceClass.BUTTON

    def __init__(self, device: PlejdDevice, button_id, entry_id):
        self.device: PlejdDevice = device
        self.entry_id = entry_id
        self.button_id = button_id
        self.listener = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.device.BLEaddress}", f"{self.device.address}")},
            "name": self.device.name,
            "manufacturer": "Plejd",
            "model": self.device.hardware,
            "suggested_area": self.device.room,
            "sw_version": f"{self.device.firmware}",
            "entry_type": dr.DeviceEntryType.SERVICE,
        }

    @property
    def name(self):
        return f"{self.button_id} pressed"

    # @Throttle(SCENE_ACTIVATION_RATE_LIMIT)
    @callback
    def _handle_button_press(self, event):
        if event["button"] == self.button_id:
            self._trigger_event("press")
            self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.listener = self.device.subscribe_event(self._handle_button_press)

    @property
    def unique_id(self):
        return f"{self.device.BLEaddress}:{self.device.address}:{self.button_id}:press"

    async def async_will_remove_from_hass(self) -> None:
        if self.listener:
            self.listener()
        return await super().async_will_remove_from_hass()
