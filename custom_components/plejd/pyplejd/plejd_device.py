
from builtins import property
from collections import namedtuple
import logging

_LOGGER = logging.getLogger(__name__)

Device = namedtuple("Device", ["model", "type", "dimmable"])

LIGHT = "light"
SENSOR = "sensor"
SWITCH = "switch"
UNKNOWN = "unknown"

HARDWARE_TYPES = {
    "0": Device("-unknown-", UNKNOWN, False),
    "1": Device("DIM-01", LIGHT, True),
    "2": Device("DIM-02", LIGHT, True),
    "3": Device("CTR-01", LIGHT, False),
    "4": Device("GWY-01", SENSOR, False),
    "5": Device("LED-10", LIGHT, True),
    "6": Device("WPH-01", SWITCH, False),
    "7": Device("REL-01", SWITCH, False),
    "8": Device("SPR-01", SWITCH, False),
    "10": Device("WRT-01", SWITCH, False),
    "11": Device("DIM-01-2P", LIGHT, True),
    "13": Device("Generic", LIGHT, False),
    "14": Device("DIM-01-LC", LIGHT, True),
    "15": Device("DIM-02-LC", LIGHT, True),
    "17": Device("REL-01-2P", SWITCH, False),
    "18": Device("REL-02", SWITCH, False),
    "20": Device("SPR-01", SWITCH, False),
    "36": Device("LED-75", LIGHT, True),
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

    def __repr__(self):
        return f"<PlejdDevice(<manager>, {self.address}, {self.BLE_address}, {self.data}>"
        pass

    @property
    def available(self):
        return self._state is not None

    @property
    def state(self):
        return self._state if self.available else False

    @property
    def dim(self):
        return self._dim/255 if self.available else 0

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
                self.updateCallback({"state": self._state, "dim": self._dim})

    async def turn_on(self, dim=0):
        await self.manager.mesh.set_state(self.address, True, dim)

    async def turn_off(self):
        await self.manager.mesh.set_state(self.address, False)
