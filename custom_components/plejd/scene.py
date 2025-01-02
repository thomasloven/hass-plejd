from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from .plejd_site import dt, get_plejd_site_from_config_entry
from .plejd_entity import PlejdDeviceBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Plejd scenes from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_scene(scene: dt.PlejdScene) -> None:
        """Add light from Plejd."""
        if scene.hidden:
            return
        entity = PlejdSceneEntity(scene)
        async_add_entities([entity])

    site.register_platform_add_device_callback(
        async_add_scene, dt.PlejdDeviceType.SCENE
    )


class PlejdSceneEntity(PlejdDeviceBaseEntity, Scene):
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

    async def async_activate(self, **_) -> None:
        """Activate the scene"""
        await self.device.activate()
