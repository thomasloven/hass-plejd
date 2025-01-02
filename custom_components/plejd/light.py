"""Support for Plejd lights."""

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import (
    dt,
    get_plejd_site_from_config_entry,
)
from .plejd_entity import PlejdDeviceBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Plejd lights from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_light(device: dt.PlejdLight) -> None:
        """Add light from Plejd."""
        entity = PlejdLight(device)
        async_add_entities([entity])

    site.register_platform_add_device_callback(
        async_add_light, dt.PlejdDeviceType.LIGHT
    )


class PlejdLight(PlejdDeviceBaseEntity, LightEntity):
    """Representation of a Plejd light."""

    def __init__(self, device: dt.PlejdLight) -> None:
        """Set up light."""
        LightEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)
        self.device: dt.PlejdLight

        self._attr_supported_color_modes: set[ColorMode] = set()
        if device.colortemp:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
            self._attr_min_color_temp_kelvin = device.colortemp[0]
            self._attr_max_color_temp_kelvin = device.colortemp[1]
        elif device.dimmable:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        else:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

    @property
    def is_on(self) -> bool:
        """Returns true if light is on."""
        if self.device.outputType == "COVERABLE":
            return True
        return self._data.get("state", False)

    @property
    def brightness(self) -> int | None:
        """Returns the current brightness of the light."""
        return self._data.get("dim", 0)

    @property
    def color_temp_kelvin(self) -> int | None:
        """Returns the current color temperature of the light."""
        return self._data.get("colortemp", None)

    @property
    def color_mode(self) -> str:
        """Returns the current color mode of the light."""
        if self.device.colortemp:
            return ColorMode.COLOR_TEMP
        if self.device.dimmable:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    async def async_turn_on(
        self, brightness: int | None = None, color_temp: int | None = None, **_
    ) -> None:
        """Turn the light on."""
        await self.device.turn_on(brightness, color_temp)

    async def async_turn_off(self, **_) -> None:
        """Turn the light off."""
        await self.device.turn_off()
