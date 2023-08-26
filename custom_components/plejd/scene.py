import pyplejd
from pyplejd.interface import PlejdScene
from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    if not (data := hass.data[DOMAIN].get(config_entry.entry_id)):
        return
    scenes: list[PlejdScene] = data["scenes"]

    entities = []
    for s in scenes:
        button = PlejdSceneEntity(s, config_entry.entry_id)
        entities.append(button)
    async_add_entities(entities, False)


class PlejdSceneEntity(Scene):
    _attr_has_entity_name = True

    def __init__(self, device, entry_id):
        super().__init__()
        self.device: PlejdScene = device
        self.entry_id = entry_id

    @property
    def name(self):
        return self.device.title

    @property
    def unique_id(self):
        return f"{self.entry_id}:{self.device.index}"

    async def async_activate(self, **kwargs):
        await self.device.activate()
