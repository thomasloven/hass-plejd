"""Plejd entity helpers."""

from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, MANUFACTURER
from .plejd_site import PlejdDevice

class PlejdDeviceBaseEntity(Entity):
    """Representation of a Plejd device."""
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device: PlejdDevice):
        """Set up entity."""
        self.device: PlejdDevice = device
        self.listener = None
        self._data = {}

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return {
            "identifiers": {
                (DOMAIN, str(self.device.BLEaddress), str(self.device.address))
            },
            "name": self.device.name,
            "manufacturer": MANUFACTURER,
            "model": self.device.hardware,
            "suggested_area": self.device.room,
            "sw_version": str(self.device.firmware)
        }

    @property
    def unique_id(self):
        """Return unique identifier for the entity."""
        return f"{self.device.BLEaddress}:{self.device.address}"

    @callback
    def _handle_state_update(self, data) -> None:
          """When device state is updated from Plejd"""
          self._data = data
          self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
          """When entity is added to hass."""
          self.listener = self.device.subscribe_state(self._handle_state_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self.listener:
            self.listener()
        return await super().async_will_remove_from_hass()

def register_unknown_device(hass: HomeAssistant, device: PlejdDevice, config_entry_id: str):
    """Add a empty device to the device registry for unknown devices."""
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry_id,
        identifiers={(DOMAIN, str(device.BLEaddress), str(device.address))},
        manufacturer=MANUFACTURER,
        name=device.name,
        model=device.hardware,
        suggested_area=device.room,
        sw_version=str(device.firmware),
    )