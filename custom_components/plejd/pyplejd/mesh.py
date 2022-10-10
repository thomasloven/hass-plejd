import asyncio
import binascii
import logging
import os
import struct
from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection

from .const import PLEJD_AUTH, PLEJD_LASTDATA, PLEJD_LIGHTLEVEL, PLEJD_PING, PLEJD_DATA
from .crypto import auth_response, encrypt_decrypt

_LOGGER = logging.getLogger(__name__)

class PlejdMesh():

    def __init__(self):
        self._connected = False
        self.client = None
        self.connected_node = None
        self.crypto_key = None
        self.mesh_nodes = []

        self.pollonWrite = True
        self.statecallback = None

    def add_mesh_node(self, device):
        self.mesh_nodes.append(device)

    def set_crypto_key(self, key):
        self.crypto_key = binascii.a2b_hex(key.replace("-", ""))

    @property
    def connected(self):
        if self._connected and self.client and self.client.is_connected:
            return True
        return False

    async def disconnect(self):
        if self.connected and self.client:
            try:
                await self.client.stop_notify(PLEJD_LASTDATA)
                await self.client.stop_notify(PLEJD_LIGHTLEVEL)
                await self.client.disconnect()
            except BleakError:
                pass
            self._connected = False
            self.client = None
    
    async def connect(self, disconnect_callback=None, key=None):
        await self.disconnect()
        _LOGGER.info("Trying to connect")

        client = None

        def _disconnect(arg):
            if not self.connected: return
            _LOGGER.error("_disconnect %s", arg)
            self.client = None
            self._connected = False
            if disconnect_callback:
                disconnect_callback()

        self.mesh_nodes.sort(key = lambda a: a.rssi, reverse = True)
        for plejd in self.mesh_nodes:
            try:
                _LOGGER.warning("Connecting to %s", plejd)
                client = await establish_connection(BleakClient, plejd, "plejd", _disconnect)
                address = plejd.address
                self._connected = True
                break
            except (BleakError, asyncio.TimeoutError) as e:
                _LOGGER.error("Error connecting to plejd: %s", str(e))
        else:
            return False

        self.client = client
        self.connected_node = binascii.a2b_hex(address.replace(":", ""))[::-1]

        await asyncio.sleep(2)

        if not await self._authenticate():
            await self.disconnect()
            return False
        
        async def _lastdata(_, lastdata):
            self.pollonWrite = False
            data = encrypt_decrypt(self.crypto_key, self.connected_node, lastdata)
            deviceState = decode_state(data)
            _LOGGER.debug("Lastdata %s", deviceState)
            if self.statecallback and deviceState is not None:
                await self.statecallback(deviceState)

        async def _lightlevel(_, lightlevel):
            deviceState = {
                "address": int(lightlevel[0]),
                "state": bool(lightlevel[1]),
                "dim": int.from_bytes(lightlevel[5:7], "little"),
            }
            _LOGGER.debug("Lightlevel %s", deviceState)
            if self.statecallback and deviceState is not None:
                await self.statecallback(deviceState)

        await client.start_notify(PLEJD_LASTDATA, _lastdata)
        await client.start_notify(PLEJD_LIGHTLEVEL, _lightlevel)
        
        return True

    async def write(self, payload):
        try:
            data = encrypt_decrypt(self.crypto_key, self.connected_node, payload)
            await self.client.write_gatt_char(PLEJD_DATA, data, response=True)
        except (BleakError, asyncio.TimeoutError) as e:
            _LOGGER.error("Write failed: %s", str(e))
            return False
        return True

    async def set_state(self, address, state, dim=0):
        payload = encode_state(address, state, dim)
        retval = await self.write(payload)
        if self.pollonWrite:
            await self.poll()
        return retval

    async def ping(self):
        if self.client is None:
            return False
        try:
            ping = bytearray(os.urandom(1))
            _LOGGER.debug("Ping(%s)", int.from_bytes(ping, "little"))
            await self.client.write_gatt_char(PLEJD_PING, ping, response=True)
            pong = await self.client.read_gatt_char(PLEJD_PING)
            _LOGGER.debug("Pong(%s)", int.from_bytes(pong, "little"))
            if (ping[0] + 1) & 0xFF == pong[0]:
                return True
        except (BleakError, asyncio.TimeoutError) as e:
            _LOGGER.warning("Error sending ping: %s", str(e))
        self.pollonWrite = True
        return False

    async def poll(self):
        if self.client is None:
            return
        await self.client.write_gatt_char(PLEJD_LIGHTLEVEL, b"\x01", response=True)

    async def _authenticate(self):
        if self.client is None:
            return False
        try:
            _LOGGER.debug("Authenticating")
            await self.client.write_gatt_char(PLEJD_AUTH, [0], response=True)
            challenge = await self.client.read_gatt_char(PLEJD_AUTH)
            response = auth_response(self.crypto_key, challenge)
            await self.client.write_gatt_char(PLEJD_AUTH, response, response=True)
            _LOGGER.debug("Authenticated")
            return True
        except (BleakError, asyncio.TimeoutError) as e:
            _LOGGER.warning("Plejd authentication failed: %s", str(e))
            return False


def decode_state(data):
    address = int(data[0])
    cmd = data[3:5]
    if address == 1 and cmd == b"\x00\x1b":
        _LOGGER.debug("Got time data?")
        ts = struct.unpack_from("<I", data, 5)[0]
        _LOGGER.debug("Timestamp: %s", ts)
        return None

    dim, state = None, None
    if cmd == b"\x00\xc8" or cmd == b"\x00\x98":
        state = bool(data[5])
        dim = int.from_bytes(data[6:8], "little")
    elif cmd == b"\x00\x97":
        state = bool(data[5])

    return {
        "address": address,
        "state": state,
        "dim": dim,
    }


def encode_state(address, state, dim):
    if state:
        if dim is None:
            return binascii.a2b_hex(f"{address:02x}0110009701")
        brightness = dim << 8 | dim
        return binascii.a2b_hex(f"{address:02x}0110009801{brightness:04x}")
    else:
        return binascii.a2b_hex(f"{address:02x}0110009700")
