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
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1

    def __init__(self, device: dt.PlejdThermostat) -> None:
        NumberEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)
        self.device: dt.PlejdThermostat

        self._attr_native_min_value = self.device.limits.get("min", 0)
        self._attr_native_max_value = self.device.limits.get("max", 100)
        self._attr_native_step = self.device.limits.get("step", 5)

    @property
    def native_value(self) -> float | None:
        return self._data.get("target", None)

    async def async_set_native_value(self, value: float) -> None:
        await self.device.set_target_temp(value)
