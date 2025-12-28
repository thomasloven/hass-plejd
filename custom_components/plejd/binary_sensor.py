"""Support for Plejd binary sensors."""

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import dt, get_plejd_site_from_config_entry, PlejdSite
from .plejd_entity import PlejdDeviceBaseEntity, PlejdDeviceDiagnosticEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Plejd events from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_motion_sensor(device: dt.PlejdMotionSensor, site: PlejdSite):
        """Add motion sensor from Plejd."""
        entity = PlejdMotionSensor(device, hass)
        async_add_entities([entity])

    site.register_platform_add_device_callback(
        async_add_motion_sensor, dt.PlejdDeviceType.MOTION
    )

    @callback
    def async_add_diagnostic_sensors(device: dt.PlejdDevice, site: PlejdSite):
        """Add diagnostic sensors from Plejd."""
        gateway = PlejdGatewaySensor(device, hass)
        connectable = PlejdConnectableSensor(device, hass)
        async_add_entities([gateway, connectable])

    site.register_platform_add_device_callback(async_add_diagnostic_sensors, "HW")


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


class PlejdGatewaySensor(PlejdDeviceDiagnosticEntity, BinarySensorEntity):
    """Device gateway status in the mesh"""

    # _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Is gateway"
    _id_suffix = "is_gateway"

    def __init__(self, device: dt.PlejdDevice, hass) -> None:
        """Set up gateway sensor."""
        BinarySensorEntity.__init__(self)
        PlejdDeviceDiagnosticEntity.__init__(self, device)
        self.device: dt.PlejdDevice
        self.is_on = False

    @callback
    def _handle_update(self) -> None:
        """When device is seen."""
        self.is_on = self.device.hw.is_gateway


class PlejdConnectableSensor(PlejdDeviceDiagnosticEntity, BinarySensorEntity):
    """Device gateway status in the mesh"""

    # _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_name = "Is connectable"
    _id_suffix = "connectable"

    def __init__(self, device: dt.PlejdDevice, hass) -> None:
        """Set up connecatable sensor."""
        BinarySensorEntity.__init__(self)
        PlejdDeviceDiagnosticEntity.__init__(self, device)
        self.device: dt.PlejdDevice
        self.is_on = False

    @callback
    def _handle_update(self) -> None:
        """When device is seen."""
        self.is_on = self.device.hw._powered
