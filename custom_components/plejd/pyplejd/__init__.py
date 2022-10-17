import logging
from datetime import timedelta

from bleak_retry_connector import close_stale_connections

from .mesh import PlejdMesh
from .api import get_cryptokey, get_devices, get_site_data
from .plejd_device import PlejdDevice

from .const import PLEJD_SERVICE

_LOGGER = logging.getLogger(__name__)

class PlejdManager:

    def __init__(self, credentials):
        self.credentials = credentials
        self.mesh = PlejdMesh()
        self.mesh.statecallback = self._update_device
        self.devices = { }
        self.credentials = credentials

    def add_mesh_device(self, device):
        _LOGGER.debug("Adding plejd %s", device)
        # for d in self.devices.values():
        #     addr = device.address.replace(":","").replace("-","").upper()
        #     if d.BLE_address.upper() == addr or addr in device.name:
        return self.mesh.add_mesh_node(device)
        # _LOGGER.debug("Device was not expected in current mesh")

    async def close_stale(self, device):
        _LOGGER.info("Closing stale connections for %s", device)
        await close_stale_connections(device)

    @property
    def connected(self):
        return self.mesh is not None and self.mesh.connected

    async def get_site_data(self):
        return await get_site_data(**self.credentials)

    async def get_devices(self):
        devices = await get_devices(**self.credentials)
        self.devices = {k: PlejdDevice(self, **v) for (k,v) in devices.items()}
        _LOGGER.info("Devices")
        _LOGGER.info(self.devices)
        return self.devices

    async def _update_device(self, deviceState):
        address = deviceState["address"]
        if address in self.devices:
            await self.devices[address].new_state(deviceState["state"], deviceState["dim"])

    @property
    def keepalive_interval(self):
        if self.mesh.pollonWrite:
            return timedelta(seconds=10)
        else:
            return timedelta(minutes=10)

    async def keepalive(self):
        if self.mesh.crypto_key is None:
            self.mesh.set_crypto_key(await get_cryptokey(**self.credentials))
        if not self.mesh.connected:
            if not await self.mesh.connect():
                return False
        return await self.mesh.ping()

    async def disconnect(self):
        _LOGGER.debug("DISCONNECT")
        await self.mesh.disconnect()

    async def poll(self):
        await self.mesh.poll()

    async def ping(self):
        retval = await self.mesh.ping()
        if self.mesh.pollonWrite:
            await self.poll()
        return retval
