from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant

from .plejd_site import PlejdScene, get_plejd_site_from_config_entry, OUTPUT_TYPE
from .plejd_entity import PlejdDeviceBaseEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Plejd scenes from a config entry."""
    site = get_plejd_site_from_config_entry(hass, config_entry)

    @callback
    def async_add_scene(scene: PlejdScene) -> None:
        """Add light from Plejd."""
        if scene.hidden:
            return
        entity = PlejdSceneEntity(scene, config_entry.entry_id)
        async_add_entities([entity])

    site.register_platform_add_device_callback(async_add_scene, OUTPUT_TYPE.SCENE)


class PlejdSceneEntity(PlejdDeviceBaseEntity, Scene):
    """Representation of a Plejd scene."""

    _attr_has_entity_name = True
    device_info = None

    def __init__(self, scene: PlejdScene, entry_id: str) -> None:
        """Set up scene."""
        super().__init__(scene)
        self.scene: PlejdScene = scene
        self.entry_id = entry_id

    @property
    def name(self) -> str:
        """Return the name of the scene entity."""
        return self.scene.name

    async def async_activate(self, **_) -> None:
        """Activate the scene"""
        await self.scene.activate()

    @property
    def available(self) -> bool:
        """Returns whether the light is avaiable."""
        return self._data.get("available", False)
