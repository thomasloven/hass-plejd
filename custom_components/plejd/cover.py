"""Support for Plejd covers."""

from typing import Any
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .plejd_site import (
    PlejdDevice,
    get_plejd_site_from_config_entry,
    OUTPUT_TYPE,
    PlejdCover,
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
    def async_add_cover(device: PlejdCover) -> None:
        """Add light from Plejd."""
        entity = PlejdCover(device)
        async_add_entities([entity])

    site.register_platform_add_device_callback(async_add_cover, OUTPUT_TYPE.COVER)


class PlejdCover(PlejdDeviceBaseEntity, CoverEntity):

    def __init__(self, device: PlejdCover) -> None:
        """Set up light."""
        CoverEntity.__init__(self)
        PlejdDeviceBaseEntity.__init__(self, device)

        self.device: PlejdCover

        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
            # | CoverEntityFeature.SET_TILT_POSITION
        )

    @property
    def available(self) -> bool:
        """Returns whether the light is avaiable."""
        return self._data.get("available", False)

    @property
    def current_cover_position(self) -> int | None:
        return self._data.get("position", 0)

    @property
    def current_cover_tilt_position(self) -> int | None:
        return None
        return self._data.get("angle", None)

    @property
    def is_closed(self) -> bool | None:
        return self.current_cover_position == 0

    @property
    def is_closing(self) -> bool | None:
        if not self._data.get("moving"):
            return False
        return not self._data.get("opening")

    @property
    def is_opening(self) -> bool | None:
        if not self._data.get("moving"):
            return False
        return self._data.get("opening")

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.device.open()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.device.close()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.device.stop()

    async def async_set_cover_position(
        self, position: int | None = None, **kwargs: Any
    ) -> None:
        await self.device.set_position(position)
