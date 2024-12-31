"""Support for Plejd events."""
from datetime import timedelta

from homeassistant.components.event import EventEntity, EventDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.util import Throttle
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import  PlejdDevice, PlejdScene, get_plejd_site_from_config_entry, OUTPUT_TYPE, PlejdButton
from .plejd_entity import PlejdDeviceBaseEntity

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


class PlejdSceneEvent(EventEntity):
    """Event for scenes triggered in Plejd."""
    _attr_has_entity_name = True
    _attr_event_types = ["activated"]

    def __init__(self, device: PlejdScene, entry_id: str) -> None:
        """Set up event."""
        super().__init__()
        self.device: PlejdScene = device
        self.entry_id: str = entry_id
        self.listener = None

    @property
    def name(self) -> str:
        """Return name of the event entity."""
        return self.device.title + " activated"

    @property
    def unique_id(self) -> str:
        """Return unique identifier for the event entity."""
        return f"{self.entry_id}:{self.device.index}:activated"

    @Throttle(SCENE_ACTIVATION_RATE_LIMIT)
    @callback
    def _handle_scene_activated(self) -> None:
        """When scene is activated from Plejd."""
        self._trigger_event("activated")
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.listener = self.device.subscribe_activate(self._handle_scene_activated)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self.listener:
            self.listener()
        return await super().async_will_remove_from_hass()


class PlejdButtonEvent(PlejdDeviceBaseEntity, EventEntity):
    """Event for button presses in Plejd."""
    _attr_has_entity_name = True
    _attr_event_types = ["press"]
    _attr_device_class = EventDeviceClass.BUTTON

    def __init__(self, device: PlejdDevice, button_id: int) -> None:
        """Set up event."""
        PlejdDeviceBaseEntity.__init__(self, device)
        self.button_id = button_id
        self.listener = None

    @property
    def name(self) -> str:
        """Return the name of the event entity."""
        return f"{self.button_id+1} pressed"

    @property
    def unique_id(self) -> str:
        """Return unique identifier for the event entity."""
        return super().unique_id + ":press"

    # @Throttle(SCENE_ACTIVATION_RATE_LIMIT)
    @callback
    def _handle_update(self, event) -> None:
        """When a button is pushed from Plejd."""
        if "button" in event and event["button"] == self.button_id:
            self._trigger_event("press")
            self.async_write_ha_state()
