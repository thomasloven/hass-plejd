"""Support for Plejd climate devices."""

from homeassistant.components.number import (
    NumberEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import dt, get_plejd_site_from_config_entry, PlejdSite
from .plejd_entity import PlejdDeviceBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Plejd lights from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_number(device: dt.PlejdThermostat, site: PlejdSite) -> None:
        """Add light from Plejd."""
        entity = PlejdClimate(device)
        async_add_entities([entity])

    site.register_platform_add_device_callback(async_add_number, dt.PlejdDeviceType.PWM)


class PlejdClimate(PlejdDeviceBaseEntity, NumberEntity):

    _attr_unit_of_measurement = "%"

    def __init__(self, device: dt.PlejdThermostat) -> None:
        """Set up climate entity."""
        NumberEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)
        self.device: dt.PlejdThermostat

        self.min_value = self.device.limits.get("min", 0)
        self.max_value = self.device.limits.get("max", 100)
        self.step = self.device.limits.get("step", 5)

    @property
    def value(self) -> float | None:
        return self._data.get("target", None)

    async def async_set_value(self, value: float):
        await self.device.set_target_temp(value)
