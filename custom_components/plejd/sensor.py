"""Helper sensors for plejd devices."""

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory

from .plejd_site import (
    dt,
    get_plejd_site_from_config_entry,
)
from .plejd_entity import PlejdDeviceDiagnosticEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Plejd events from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_diagnostic_sensors(device: dt.PlejdDevice):
        """Add diagnostic sensors from Plejd."""
        last_seen = PlejdLastSeenSensor(device, hass)
        rssi = PlejdRSSISensor(device, hass)
        async_add_entities([last_seen, rssi])

    site.register_platform_add_device_callback(async_add_diagnostic_sensors, "HW")


class PlejdLastSeenSensor(PlejdDeviceDiagnosticEntity, SensorEntity):
    """Device last seen in the mesh"""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_name = "Last seen"
    _id_suffix = "last_seen"

    def __init__(self, device: dt.PlejdDevice, hass) -> None:
        """Set up last seen sensor."""
        SensorEntity.__init__(self)
        PlejdDeviceDiagnosticEntity.__init__(self, device)
        self.device: dt.PlejdDevice

    @property
    def state(self):
        return self._data.get("last_seen", None)

    @callback
    def _handle_update(self) -> None:
        """When device is seen."""
        self._data["last_seen"] = self.device.hw.last_seen


class PlejdRSSISensor(PlejdDeviceDiagnosticEntity, SensorEntity):
    """Device last rssi in the mesh"""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_unit_of_measurement = "dB"
    _attr_name = "RSSI"
    _id_suffix = "rssi"

    def __init__(self, device: dt.PlejdDevice, hass) -> None:
        """Set up rssi sensor."""
        SensorEntity.__init__(self)
        PlejdDeviceDiagnosticEntity.__init__(self, device)
        self.device: dt.PlejdDevice

    @property
    def state(self):
        return self._data.get("rssi", None)

    @callback
    def _handle_update(self) -> None:
        """When device is seen."""
        self._data["rssi"] = self.device.hw.rssi
