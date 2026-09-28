from datetime import timedelta

from homeassistant.components.scene import BaseScene
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import Throttle
from homeassistant.core import callback, HomeAssistant

from .plejd_site import dt, get_plejd_site_from_config_entry, PlejdSite
from .plejd_entity import PlejdDeviceBaseEntity

SCENE_ACTIVATION_RATE_LIMIT = timedelta(seconds=2)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Plejd scenes from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_scene(scene: dt.PlejdScene, site: PlejdSite) -> None:
        """Add light from Plejd."""
        if scene.hidden:
            return
        entity = PlejdSceneEntity(scene)
        async_add_entities([entity])

    site.register_platform_add_device_callback(
        async_add_scene, dt.PlejdDeviceType.SCENE
    )


class PlejdSceneEntity(PlejdDeviceBaseEntity, BaseScene):
    """Representation of a Plejd scene."""

    _attr_has_entity_name = True
    device_info = None

    def __init__(self, scene: dt.PlejdScene) -> None:
        """Set up scene."""
        super().__init__(scene)
        self.device: dt.PlejdScene

    @property
    def name(self) -> str:
        """Return the name of the scene entity."""
        return self.device.name

    async def _async_activate(self, **_) -> None:
        """Activate the scene"""
        await self.device.activate()

    @Throttle(SCENE_ACTIVATION_RATE_LIMIT)
    @callback
    def _handle_update(self, event) -> None:
        """When scene is activated from Plejd."""
        if event.get("triggered", False):
            self._async_record_activation()
            self.async_write_ha_state()
