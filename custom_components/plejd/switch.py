"""Support for Plejd switches."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory

from .plejd_site import dt, get_plejd_site_from_config_entry, PlejdSite
from .plejd_entity import PlejdDeviceBaseEntity, PlejdDeviceDiagnosticEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Plejd switches from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_switch(device: dt.PlejdRelay, site: PlejdSite) -> None:
        """Add light from Plejd."""
        entity = PlejdSwitch(device)
        async_add_entities([entity])

    site.register_platform_add_device_callback(
        async_add_switch, dt.PlejdDeviceType.SWITCH
    )

    @callback
    def async_add_diagnostic_switch(device: dt.PlejdDevice, site: PlejdSite) -> None:
        """Add diagnostic switches from Plejd."""
        entity = PlejdConnectableSwitch(device, site)
        if device.hw._powered:
            async_add_entities([entity])

    site.register_platform_add_device_callback(async_add_diagnostic_switch, "HW")


class PlejdSwitch(PlejdDeviceBaseEntity, SwitchEntity):
    """Representation of a Plejd switch."""

    def __init__(self, device: dt.PlejdRelay) -> None:
        """Set up switch."""
        SwitchEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)
        self.device: dt.PlejdRelay

    @property
    def is_on(self) -> bool:
        """Returns true if switch is on."""
        return self._data.get("state", False)

    async def async_turn_on(self, **_) -> None:
        """Turn the switch on."""
        await self.device.turn_on()

    async def async_turn_off(self, **_) -> None:
        """Turn the switch off."""
        await self.device.turn_off()


class PlejdConnectableSwitch(PlejdDeviceDiagnosticEntity, SwitchEntity):
    """Switch to select whether device should be connected to."""

    # _attr_entity_category = EntityCategory.CONFIG
    _attr_name = "May be gateway"
    _id_suffix = "may_be_gateway"

    def __init__(self, device: dt.PlejdDevice, site: PlejdSite):
        """Set up switch."""
        SwitchEntity.__init__(self)
        PlejdDeviceDiagnosticEntity.__init__(self, device)
        self.device: dt.PlejdDevice
        self.site = site

    @property
    def is_on(self) -> bool:
        """Returns true if switch is on."""
        return not self.device.ble_mac in self.site.blacklist

    async def async_turn_on(self, **_) -> None:
        """Blacklist the device"""
        self.site.blacklist.discard(self.device.ble_mac)
        await self.site.update_blacklist()
        self.async_write_ha_state()

    async def async_turn_off(self, **_) -> None:
        """Un-blacklist the device"""
        self.site.blacklist.add(self.device.ble_mac)
        await self.site.update_blacklist()
        self.async_write_ha_state()
