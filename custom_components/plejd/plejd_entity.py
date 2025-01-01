"""Plejd entity helpers."""

from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, MANUFACTURER
from .plejd_site import PlejdDevice


@callback
def make_identifier(device: PlejdDevice):
    return (DOMAIN, str(device.BLEaddress), str(device.address))


class PlejdDeviceBaseEntity(Entity):
    """Representation of a Plejd device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device: PlejdDevice):
        """Set up entity."""
        super().__init__()
        self.device: PlejdDevice = device
        self.listener = None
        self._data = {}

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return {
            "identifiers": {(DOMAIN, *self.device.device_identifier)},
            "name": self.device.name,
            "manufacturer": MANUFACTURER,
            "model": self.device.hardware,
            "suggested_area": self.device.room,
            "sw_version": str(self.device.firmware),
        }

    @property
    def unique_id(self):
        """Return unique identifier for the entity."""
        return ":".join(self.device.identifier)

    @property
    def entity_registry_visible_default(self):
        """Return if the device should be visible by default"""
        return not self.device.hidden

    @callback
    def _handle_update(self, data) -> None:
        """When device state is updated from Plejd"""
        self._data = data
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.listener = self.device.subscribe(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self.listener:
            self.listener()
        return await super().async_will_remove_from_hass()


@callback
def register_unknown_device(
    hass: HomeAssistant, device: PlejdDevice, config_entry_id: str
):
    """Add a empty device to the device registry for unknown devices."""
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry_id,
        identifiers={(DOMAIN, *device.device_identifier)},
        manufacturer=MANUFACTURER,
        name=device.name,
        model=device.hardware,
        suggested_area=device.room,
        sw_version=str(device.firmware),
    )
