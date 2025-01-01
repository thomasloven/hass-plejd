"""Support for Plejd switches."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import PlejdDevice, get_plejd_site_from_config_entry, OUTPUT_TYPE
from .plejd_entity import PlejdDeviceBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Plejd switches from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_switch(device: PlejdDevice) -> None:
        """Add light from Plejd."""
        entity = PlejdSwitch(device)
        async_add_entities([entity])

    site.register_platform_add_device_callback(async_add_switch, OUTPUT_TYPE.SWITCH)


class PlejdSwitch(PlejdDeviceBaseEntity, SwitchEntity):
    """Representation of a Plejd switch."""

    def __init__(self, device: PlejdDevice) -> None:
        """Set up switch."""
        SwitchEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)

    @property
    def available(self) -> bool:
        """Returns whether the switch is avaiable."""
        return self._data.get("available", False)

    @property
    def is_on(self) -> bool:
        """Returns true if switch is on."""
        return self._data.get("state", False)

    async def async_turn_on(self, **_) -> None:
        """Turn the switch on."""
        await self.device.turn_on(None)
        pass

    async def async_turn_off(self, **_) -> None:
        """Turn the switch off."""
        await self.device.turn_off()
        pass
