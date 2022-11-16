import asyncio
import binascii
import logging
import os
import struct
from datetime import datetime
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
        self.scenecallback = None
        self.buttoncallback = None

        self._ble_lock = asyncio.Lock()

    def add_mesh_node(self, device):
        if device not in self.mesh_nodes:
            self.mesh_nodes.append(device)
        else:
            _LOGGER.debug("Plejd already added")

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
        _LOGGER.debug("Trying to connect to mesh")

        client = None

        def _disconnect(arg):
            if not self.connected: return
            _LOGGER.debug("_disconnect %s", arg)
            self.client = None
            self._connected = False
            if disconnect_callback:
                disconnect_callback()

        self.mesh_nodes.sort(key = lambda a: a.rssi, reverse = True)
        for plejd in self.mesh_nodes:
            try:
                _LOGGER.debug("Connecting to %s", plejd)
                client = await establish_connection(BleakClient, plejd, "plejd", _disconnect)
                address = plejd.address
                self._connected = True
                self.client = client
                _LOGGER.debug("Connected to Plejd mesh")
                if not await self._authenticate():
                    await self.client.disconnect()
                    self._connected = False
                    continue
                break
            except (BleakError, asyncio.TimeoutError) as e:
                _LOGGER.warning("Error connecting to Plejd device: %s", str(e))
        else:
            if len(self.mesh_nodes) == 0:
                _LOGGER.debug("Failed to connect to plejd mesh - no devices discovered")
            else:
                _LOGGER.warning("Failed to connect to plejd mesh - %s", self.mesh_nodes)
            return False

        self.connected_node = binascii.a2b_hex(address.replace(":", "").replace("-", ""))[::-1]

        async def _lastdata(_, lastdata):
            self.pollonWrite = False
            data = encrypt_decrypt(self.crypto_key, self.connected_node, lastdata)
            _LOGGER.debug("Received LastData %s", data.hex())
            deviceState = decode_message(data)
            _LOGGER.debug("Decoded LastData %s", deviceState)
            if deviceState is None:
                return
            if self.statecallback and "state" in deviceState:
                await self.statecallback(deviceState)
            if self.scenecallback and "scene" in deviceState:
                await self.scenecallback(deviceState)
            if self.buttoncallback and "button" in deviceState:
                await self.buttoncallback(deviceState)

        async def _lightlevel(_, lightlevel):
            _LOGGER.debug("Received LightLevel %s", lightlevel.hex())
            for i in range(0, len(lightlevel), 10):
                ll = lightlevel[i:i+10]
                deviceState = {
                    "address": int(ll[0]),
                    "state": bool(ll[1]),
                    "dim": int.from_bytes(ll[5:7], "little"),
                }
                _LOGGER.debug("Decoded LightLevel %s", deviceState)
                if self.statecallback and deviceState is not None:
                    await self.statecallback(deviceState)

        await client.start_notify(PLEJD_LASTDATA, _lastdata)
        await client.start_notify(PLEJD_LIGHTLEVEL, _lightlevel)
        
        await self.poll()

        return True

    async def write(self, payload):
        try:
            # TODO:
            async with self._ble_lock:
                _LOGGER.debug("Writing data to Plejd mesh CT: %s", payload.hex())
                data = encrypt_decrypt(self.crypto_key, self.connected_node, payload)
                await self.client.write_gatt_char(PLEJD_DATA, data, response=True)
        except (BleakError, asyncio.TimeoutError) as e:
            _LOGGER.warning("Plejd mesh write command failed: %s", str(e))
            return False
        return True

    async def set_state(self, address, state, dim=0):
        payload = encode_state(address, state, dim)
        retval = await self.write(payload)
        if self.pollonWrite:
            await self.poll()
        return retval

    async def activate_scene(self, index):
        payload = binascii.a2b_hex(f"0201100021{index:02x}")
        retval = await self.write(payload)
        if self.pollonWrite:
            await self.poll()
        return retval

    async def ping(self):
        async with self._ble_lock:
            return await self._ping()
                
    async def _ping(self):
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
            _LOGGER.warning("Plejd mesh keepalive signal failed: %s", str(e))
        self.pollonWrite = True
        return False

    async def poll(self):
        if self.client is None:
            return
        _LOGGER.debug("Polling Plejd mesh for current state")
        async with self._ble_lock:
            await self.client.write_gatt_char(PLEJD_LIGHTLEVEL, b"\x01", response=True)

    async def _authenticate(self):
        if self.client is None:
            return False
        try:
            async with self._ble_lock:
                _LOGGER.debug("Authenticating to plejd mesh")
                await self.client.write_gatt_char(PLEJD_AUTH, b"\0x00", response=True)
                challenge = await self.client.read_gatt_char(PLEJD_AUTH)
                response = auth_response(self.crypto_key, challenge)
                await self.client.write_gatt_char(PLEJD_AUTH, response, response=True)
                if not await self._ping():
                    _LOGGER.debug("Authenticion failed")
                    return False
                _LOGGER.debug("Authenticated successfully")
                return True
        except (BleakError, asyncio.TimeoutError) as e:
            _LOGGER.warning("Plejd authentication failed: %s", str(e))
        return False


def decode_message(data):
    address = int(data[0])
    cmdtype = data[1:3]
    if not cmdtype == b"\x01\x10":
        _LOGGER.debug("Got non-command data: %s", cmdtype)
        return None
    cmd = data[3:5]

    if address == 0:
        # Broadcast
        if cmd == b"\x00\x21":
            # Scene triggered
            sceneIndex = data[5] % 128
            state = data[5] < 128
            _LOGGER.debug(f"id: {sceneIndex} state: {state}")
            return {
                "sceneIndex": sceneIndex,
                "state": state,
            }
        return None
    if address == 1 and cmd == b"\x00\x1b":
        _LOGGER.debug("Got time data")
        ts = struct.unpack_from("<I", data, 5)[0]
        dt = datetime.fromtimestamp(ts)
        _LOGGER.debug("Timestamp: %s (%s)", ts, dt)
        return None
    # if address == 2:
    #     # Scene update?
    #     pass

    retval = {"address": address}

    if cmd == b"\x00\xc8" or cmd == b"\x00\x98":
        retval["state"] = bool(data[5])
        retval["dim"] = int.from_bytes(data[6:8], "little")        
    elif cmd == b"\x00\x97":
        retval["state"] = bool(data[5])
    elif cmd == b"\x00\x16":
        retval["address"] = int(data[5])
        retval["button"] = int(data[6])
        _LOGGER.info("Button pressed: %s", retval)
    elif cmd == b"\x00\x21":
        del retval["address"]
        retval["scene"] = int(data[5])
        _LOGGER.info("Scene triggered: %s", retval)
    else:
        _LOGGER.debug("Unknown command %s", cmd)
        return None

    return retval


def encode_state(address, state, dim):
    if state:
        if dim is None:
            return binascii.a2b_hex(f"{address:02x}0110009701")
        brightness = dim << 8 | dim
        return binascii.a2b_hex(f"{address:02x}0110009801{brightness:04x}")
    else:
        return binascii.a2b_hex(f"{address:02x}0110009700")
