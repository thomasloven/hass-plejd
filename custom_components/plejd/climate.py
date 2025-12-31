"""Support for Plejd climate devices."""

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    const as ClimateConst,
    ATTR_TEMPERATURE,
    HVACMode,
    HVACAction,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTemperature

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
    def async_add_climate(device: dt.PlejdThermostat, site: PlejdSite) -> None:
        """Add light from Plejd."""
        entity = PlejdClimate(device)
        async_add_entities([entity])

    site.register_platform_add_device_callback(
        async_add_climate, dt.PlejdDeviceType.CLIMATE
    )


class PlejdClimate(PlejdDeviceBaseEntity, ClimateEntity):

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [
        ClimateConst.PRESET_AWAY,
        ClimateConst.PRESET_BOOST,
        "frost",
        ClimateConst.PRESET_SLEEP,
        ClimateConst.PRESET_ECO,
        ClimateConst.PRESET_HOME,
    ]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
    ]

    def __init__(self, device: dt.PlejdThermostat) -> None:
        """Set up climate entity."""
        ClimateEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)
        self.device: dt.PlejdThermostat

        self.min_temp = self.device.limits.get("min", 7)
        self.max_temp = self.device.limits.get("max", 35)

    @property
    def is_on(self) -> bool:
        return not self._data.get("mode", 7) == dt.PlejdThermostat.MODE_SERVICE

    async def async_turn_on(self):
        await self.device.turn_on()

    async def async_turn_off(self):
        await self.device.turn_off()

    @property
    def hvac_action(self) -> HVACAction | None:
        if not self.is_on:
            return HVACAction.OFF
        return (
            HVACAction.HEATING if self._data.get("heating", False) else HVACAction.IDLE
        )

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT if self.is_on else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.HEAT:
            await self.async_turn_on()
        else:
            await self.async_turn_off()

    @property
    def target_temperature(self) -> float:
        return self._data.get("target", None)

    @property
    def current_temperature(self) -> float:
        return self._data.get("current", None)

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            await self.device.set_target_temp(kwargs[ATTR_TEMPERATURE])

    @property
    def preset_mode(self) -> str | None:
        match self.device.preset:
            case None:
                return None
            case self.device.MODE_SERVICE:
                return ClimateConst.PRESET_NONE
            case self.device.MODE_VACATION:
                return ClimateConst.PRESET_AWAY
            case self.device.MODE_BOOST:
                return ClimateConst.PRESET_BOOST
            case self.device.MODE_FROST:
                return "frost"
            case self.device.MODE_NIGHT:
                return ClimateConst.PRESET_SLEEP
            case self.device.MODE_LOW:
                return ClimateConst.PRESET_ECO
            case _:
                return ClimateConst.PRESET_NONE

    async def async_set_preset_mode(self, preset_mode):
        mode = {
            ClimateConst.PRESET_AWAY: self.device.MODE_VACATION,
            ClimateConst.PRESET_BOOST: self.device.MODE_BOOST,
            "frost": self.device.MODE_FROST,
            ClimateConst.PRESET_SLEEP: self.device.MODE_NIGHT,
            ClimateConst.PRESET_ECO: self.device.MODE_LOW,
        }.get(preset_mode, None)
        await self.device.set_mode(mode)
