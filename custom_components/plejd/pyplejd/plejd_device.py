
from builtins import property
from collections import namedtuple

Device = namedtuple("Device", ["model", "type", "dimmable"])

LIGHT = "light"
SENSOR = "sensor"
SWITCH = "switch"


HARDWARE_TYPES = {
    "0": Device("-unknown-", LIGHT, False),
    "1": Device("DIM-01", LIGHT, True),
    "2": Device("DIM-02", LIGHT, True),
    "3": Device("CTR-01", LIGHT, False),
    "4": Device("GWY-01", SENSOR, False),
    "5": Device("LED-10", LIGHT, True),
    "6": Device("WPH-01", SWITCH, False),
    "7": Device("REL-01", SWITCH, False),
    "8": Device("SPR-01?", SWITCH, False),
    "9": Device("-unknown-", LIGHT, False),
    "10": Device("WRT-01", SWITCH, False),
    "11": Device("DIM-01", LIGHT, True),
    "12": Device("-unknown-", LIGHT, False),
    "13": Device("Generic", LIGHT, False),
    "14": Device("DIM-01", LIGHT, True),
    "15": Device("-unknown-", LIGHT, False),
    "16": Device("-unknown-", LIGHT, False),
    "17": Device("REL-01", SWITCH, False),
    "18": Device("REL-02", SWITCH, False),
    "19": Device("-unknown-", LIGHT, False),
    "20": Device("SPR-01", SWITCH, False),
}

class PlejdDevice:

    def __init__(self, manager, address, BLE_address, data):
        self.manager = manager
        self.address = address
        self._BLE_address = BLE_address
        self.data = data #{name, hardwareId, dimmable, room, firmware}

        self.updateCallback = None

        self._state = None
        self._dim = None

    @property
    def state(self):
        return self._state

    @property
    def dim(self):
        return self._dim/255

    @property
    def BLE_address(self):
        return self._BLE_address

    @property
    def name(self):
        return self.data["name"]
    @property
    def room(self):
        return self.data["room"]
    @property
    def firmware(self):
        return self.data["firmware"]
    @property
    def hardwareId(self):
        return self.data["hardwareId"]

    @property
    def type(self):
        return self.hardware_data.type
    @property
    def model(self):
        return self.hardware_data.model
    @property
    def dimmable(self):
        return self.hardware_data.dimmable and self.data["dimmable"] != False
    
    @property
    def hardware_data(self):
        deviceType = HARDWARE_TYPES.get(self.data["hardwareId"], HARDWARE_TYPES["0"])
        return deviceType

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

    
