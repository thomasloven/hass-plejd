"""Support for Plejd binary sensors."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import (
    dt,
    get_plejd_site_from_config_entry,
)
from .plejd_entity import PlejdDeviceBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Plejd events from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_motion_sensor(device: PlejdMotionSensor):
        """Add motion sensor from Plejd."""
        entity = PlejdMotionSensor(device, hass)
        async_add_entities([entity])

    site.register_platform_add_device_callback(
        async_add_motion_sensor, dt.PlejdDeviceType.MOTION
    )


class PlejdMotionSensor(PlejdDeviceBaseEntity, BinarySensorEntity):
    """Motion sensors in Plejd."""

    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(self, device: dt.PlejdMotionSensor, hass) -> None:
        """Set up motion sensor."""
        BinarySensorEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)
        self.device: dt.PlejdMotionSensor

        self.is_on = False

    @callback
    def _handle_update(self, state) -> None:
        """When motion is detected from Plejd."""
        if state.get("motion", False) is not None:
            self.is_on = state.get("motion", False)
