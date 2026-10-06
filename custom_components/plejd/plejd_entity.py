"""Plejd entity helpers."""

import logging

from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import device_registry as dr
from homeassistant.const import EntityCategory

from .const import DOMAIN, MANUFACTURER
from .plejd_site import dt

_LOGGER = logging.getLogger(__name__)


def device_info(hass: HomeAssistant, device: dt.PlejdDevice, config_entry_id: str):
    info = {
        "identifiers": {(DOMAIN, device.device_identifier)},
        "name": device.name,
        "manufacturer": MANUFACTURER,
        "model": device.hardware,
        "suggested_area": device.room,
        "sw_version": str(device.firmware),
    }
    if not device.parent_identifier == device.device_identifier:
        parent = dr.async_get(hass).async_get_device_by_identifier(
            (DOMAIN, device.parent_identifier),
            config_entry_id,
        )

        if parent is not None:
            info["via_device_id"] = parent.id
    else:
        info["connections"] = {(dr.CONNECTION_BLUETOOTH, device.ble_mac)}

    return info


class PlejdDeviceBaseEntity(Entity):
    """Representation of a Plejd device."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, device: dt.PlejdDevice):
        """Set up entity."""
        super().__init__()
        self.device = device
        self.listener = None
        self._data = {}

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return device_info(self.hass, self.device, self.platform.config_entry.entry_id)

    @property
    def unique_id(self):
        """Return unique identifier for the entity."""
        return ":".join(self.device.identifier)

    @property
    def entity_registry_visible_default(self):
        """Return if the device should be visible by default"""
        return not self.device.hidden

    @property
    def available(self) -> bool:
        """Returns whether the switch is avaiable."""
        return self._data.get("available", False)

    @callback
    def _handle_update(self, data) -> None:
        """When device state is updated from Plejd"""
        pass

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""

        def _listener(data):
            self._data = data
            self._handle_update(data)
            self.async_write_ha_state()

        self.listener = self.device.subscribe(_listener)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self.listener:
            self.listener()
        return await super().async_will_remove_from_hass()


class PlejdDeviceDiagnosticEntity(PlejdDeviceBaseEntity):
    """Base class for a diagnostic entity"""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = False
    _id_suffix = "diagnostic"

    @property
    def unique_id(self):
        """Return unique identifier for the entity."""
        return ":".join(self.device.identifier) + self._id_suffix

    @property
    def available(self):
        return True

    @callback
    def _handle_update(self) -> None:
        """When device state is updated from Plejd"""
        pass

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""

        def _listener():
            self._handle_update()
            self.async_write_ha_state()

        self.listener = self.device.hw.subscribe(_listener)


@callback
def register_unknown_device(
    hass: HomeAssistant, device: dt.PlejdDevice, config_entry_id: str
):
    """Add a empty device to the device registry for unknown devices."""
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry_id,
        **device_info(hass, device, config_entry_id),
    )


@callback
def migrate_device_registry(
    hass: HomeAssistant, devices: list[dt.PlejdDevice], config_entry_id: str
):
    """Make sure the Bluetooth connection belongs to the primary device.

    Earlier versions attached the Bluetooth connection of a multi-output unit
    (DIM-02, REL-02, ...) to whichever output happened to carry the
    diagnostic entities. The connection is now always registered on the
    primary output's device, and Home Assistant refuses to register the same
    connection twice within one config entry. Move it before the platforms
    try to register their devices, instead of failing the whole setup.
    """
    registry = dr.async_get(hass)
    for device in devices:
        if not getattr(device, "is_primary", False):
            continue
        if not (ble_mac := getattr(device, "ble_mac", None)):
            continue
        connection = (dr.CONNECTION_BLUETOOTH, ble_mac)
        owner = registry.async_get_device(connections={connection})
        if owner is None:
            continue
        if (DOMAIN, device.device_identifier) in owner.identifiers:
            continue
        if config_entry_id not in owner.config_entries:
            continue
        _LOGGER.info(
            "Moving Bluetooth connection %s from device '%s' to the primary device '%s'",
            ble_mac,
            owner.name_by_user or owner.name,
            device.name,
        )
        registry.async_update_device(
            owner.id, new_connections=owner.connections - {connection}
        )
