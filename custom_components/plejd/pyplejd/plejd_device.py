
from builtins import property


class PlejdDevice:

    def __init__(self, manager, address, BLE_address, name, type, model, dimmable, room, firmware):
        self.manager = manager
        self.address = address
        self._BLE_address = BLE_address
        self.name = name
        self.type = type
        self.model = model
        self.dimmable = dimmable
        self.room = room
        self.firmware = firmware

        self.updateCallback = None

        self._state = None
        self._dim = None

    @property
    def state(self):
        return self._state

    @property
    def dim(self):
        return self._dim

    @property
    def BLE_address(self):
        return self._BLE_address

    async def new_state(self, state, dim):
        update = False
        if state != self._state:
            update = True
            self._state = state
        if dim != self._dim:
            update = True
            self._dim = dim
        if update:
            if self.updateCallback:
                await self.updateCallback({"state": self._state, "dim": self._dim})

    async def turn_on(self, dim=0):
        await self.manager.mesh.set_state(self.address, True, dim)

    async def turn_off(self):
        await self.manager.mesh.set_state(self.address, False)

    
