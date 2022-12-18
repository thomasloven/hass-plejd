import logging

from homeassistant.components.button import ButtonEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    scenes = hass.data[DOMAIN]["scenes"].get(config_entry.entry_id, []).values()

    entities = []
    for s in scenes:
        s.updateCallback = lambda d: hass.bus.fire("plejd_scene_event", d)
        if not s.visible: continue
        button = PlejdSceneButton(s, config_entry.entry_id)
        entities.append(button)
    async_add_entities(entities, False)

class PlejdSceneButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, device, entry_id):
        super().__init__()
        self.device = device
        self.entry_id = entry_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self.entry_id}")},
            "name": "Plejd Scene",
            "manufacturer": "Plejd",
            #"connections": ???,
        }

    # @property
    # def available(self):
    #     return self.device.available

    @property
    def has_entity_name(self):
        return True
    
    @property
    def name(self):
        return self.device.name

    @property
    def unique_id(self):
        return f"{self.entry_id}:{self.device.index}"

    async def async_press(self):
        await self.device.activate()
