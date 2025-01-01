"""Support for Plejd events."""
from datetime import timedelta

from homeassistant.components.event import EventEntity, EventDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.util import Throttle
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import  PlejdDevice, PlejdScene, get_plejd_site_from_config_entry, OUTPUT_TYPE, PlejdButton
from .plejd_entity import PlejdDeviceBaseEntity

import logging
_LOGGER = logging.getLogger(__name__)

SCENE_ACTIVATION_RATE_LIMIT = timedelta(seconds=2)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Plejd events from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_button_event(device: PlejdButton):
        """Add button events from Plejd."""
        entity = PlejdButtonEvent(device, device.button_id)
        async_add_entities([entity])
    site.register_platform_add_device_callback(async_add_button_event, OUTPUT_TYPE.BUTTON)

    @callback
    def async_add_scene_event(scene: PlejdScene):
        entity = PlejdSceneEvent(scene, config_entry.entry_id)
        async_add_entities([entity])
    site.register_platform_add_device_callback(async_add_scene_event, OUTPUT_TYPE.SCENE)


class PlejdSceneEvent(PlejdDeviceBaseEntity, EventEntity):
    """Event for scenes triggered in Plejd."""
    _attr_has_entity_name = True
    _attr_event_types = ["activated"]
    device_info = None

    def __init__(self, device: PlejdScene, entry_id: str) -> None:
        """Set up event."""
        super().__init__(device)
        self.device: PlejdScene = device
        self.entry_id: str = entry_id
        self.listener = None
        self._data = {}

    @property
    def name(self) -> str:
        """Return name of the event entity."""
        return self.device.name + " activated"

    @property
    def unique_id(self) -> str:
        """Return unique identifier for the event entity."""
        return super().unique_id + ":activated"

    @property
    def available(self) -> bool:
        """Returns whether the light is avaiable."""
        return self._data.get("available", False)

    @Throttle(SCENE_ACTIVATION_RATE_LIMIT)
    @callback
    def _handle_update(self, event) -> None:
        """When scene is activated from Plejd."""
        self._data = event
        if event.get("triggered", False):
            self._trigger_event("activated")
        self.async_write_ha_state()


class PlejdButtonEvent(PlejdDeviceBaseEntity, EventEntity):
    """Event for button presses in Plejd."""
    _attr_has_entity_name = True
    _attr_event_types = ["press", "release"]
    _attr_device_class = EventDeviceClass.BUTTON

    def __init__(self, device: PlejdDevice, button_id: int) -> None:
        """Set up event."""
        super().__init__(device)
        self.button_id = button_id
        self.listener = None
        self._data = {}

    @property
    def name(self) -> str:
        """Return the name of the event entity."""
        return f"{self.button_id+1} pressed"

    @property
    def unique_id(self) -> str:
        """Return unique identifier for the event entity."""
        return super().unique_id + ":press"

    @property
    def available(self) -> bool:
        """Returns whether the light is avaiable."""
        return self._data.get("available", False)

    # @Throttle(SCENE_ACTIVATION_RATE_LIMIT)
    @callback
    def _handle_update(self, event) -> None:
        """When a button is pushed from Plejd."""
        self._data = event
        if event.get("button") == self.button_id:
            action = event.get("action")
            if action == "press":
                self._trigger_event("press")
            elif action == "release":
                self._trigger_event("release")
        self.async_write_ha_state()
