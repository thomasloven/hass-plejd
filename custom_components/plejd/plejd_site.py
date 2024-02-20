"""Plejd site mesh controller."""

from datetime import timedelta
import logging
from typing import cast, Callable
from enum import Enum

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from home_assistant_bluetooth import BluetoothServiceInfoBleak

import pyplejd
from pyplejd import ConnectionError, AuthenticationError
from pyplejd.interface import PlejdDevice, PlejdScene
from .const import DOMAIN
from .plejd_entity import register_unknown_device


class OUTPUT_TYPE(str, Enum):
    LIGHT = pyplejd.LIGHT
    SWITCH = pyplejd.SWITCH
    BUTTON = pyplejd.SENSOR
    MOTION = pyplejd.MOTION
    SCENE = "scene"
    SCENE_EVENT = "scene_event"
    UNKNOWN = pyplejd.UNKNOWN


_LOGGER = logging.getLogger(__name__)

SITE_DATA_STORE_KEY = "plejd_site_data"
SITE_DATA_STORE_VERSION = 1

class PlejdSite:
    """Controller for a Plejd site mesh."""

    def __init__(self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        username: str,
        password: str,
        siteId: str
     ) -> None:
        """Initialize plejd site mesh."""
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = config_entry

        self.credentials: pyplejd.PlejdCloudCredentials = {
            "username": username,
            "password": password,
            "siteId": siteId,
        }

        self.store = Store(hass, SITE_DATA_STORE_VERSION, SITE_DATA_STORE_KEY)

        self.manager: pyplejd.PlejdManager = pyplejd.PlejdManager(self.credentials)

        self.devices: list[PlejdDevice] = []
        self.scenes: list[PlejdScene] = []

        self.stopping = False

        self.add_device_callbacks = {}

    def register_platform_add_device_callback(
        self,
        callback: Callable[[PlejdDevice | PlejdScene], None],
        output_type: OUTPUT_TYPE
    ) -> None:
        self.add_device_callbacks[output_type] = callback

    async def start(self) -> None:
        """Setup and connect to plejd site."""
        if not(site_data_cache := await self.store.async_load()) or not isinstance(site_data_cache, dict):
            site_data_cache = {}

        cached_site_data = site_data_cache.get(self.credentials["siteId"])

        await self.manager.init(cached_site_data)

        self.devices = self.manager.devices
        self.scenes = self.manager.scenes

        for device in self.devices:
            if device.hidden:
                continue
            if (adder := self.add_device_callbacks.get(device.outputType)):
                adder(device)
            else:
                register_unknown_device(self.hass, device, self.config_entry.entry_id)

        for scene in self.scenes:
            if (adder := self.add_device_callbacks.get(OUTPUT_TYPE.SCENE_EVENT)):
                adder(scene)
            if scene.hidden:
                continue
            if (adder := self.add_device_callbacks.get(OUTPUT_TYPE.SCENE)):
                adder(scene)


        # Close any stale connections that may be open
        for dev in self.devices:
            ble_device = bluetooth.async_ble_device_from_address(self.hass, dev.BLEaddress, True)
            if ble_device:
                await self.manager.close_stale(ble_device)

        # Register callback for bluetooth discover
        self.config_entry.async_on_unload(
            bluetooth.async_register_callback(
                self.hass,
                self._discovered,
                bluetooth.match.BluetoothCallbackMatcher(
                    connectable = True, service_uuid=pyplejd.PLEJD_SERVICE.lower()
                ),
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )

        # Run through already discovered devices and add plejds to the manager
        for service_info in bluetooth.async_discovered_service_info(self.hass, True):
            if pyplejd.PLEJD_SERVICE.lower() in service_info.advertisement.service_uuids:
                self._discovered(service_info, connect=False)

        # Ping the mesh periodically to maintain the connection
        self.config_entry.async_on_unload(
            async_track_time_interval(
                self.hass, self._ping, self.manager.ping_interval, name="Plejd keep-alive"
            )
        )

        # Check that the mesh clock is in sync once per hour
        self.config_entry.async_on_unload(
            async_track_time_interval(
                self.hass, self._broadcast_time, timedelta(hours=1), name="Plejd sync time"
            )
        )

        self.hass.async_create_task(self._ping())
        self.hass.async_create_task(self._broadcast_time())

    async def stop(self, *_) -> None:
        """Disconnect mesh and tear down site configuration."""
        self.stopping = True

        if not(site_data_cache := await self.store.async_load()) or not isinstance(site_data_cache, dict):
            site_data_cache = {}
        site_data_cache[self.credentials["siteId"]] = await self.manager.get_raw_sitedata()
        await self.store.async_save(site_data_cache)

        await self.manager.disconnect()


    def _discovered(self, service_info: BluetoothServiceInfoBleak, *_, connect: bool = True) -> None:
        """Register any discovered plejd device with the manager."""
        self.manager.add_mesh_device(service_info.device, service_info.rssi)
        if connect:
            self.hass.async_create_task(self._ping())

    async def _ping(self, *_) -> None:
        """Ping the plejd mesh to connect or maintain the connection."""
        if self.stopping:
            return
        if not await self.manager.ping():
            _LOGGER.debug("Ping failed")

    async def _broadcast_time(self, *_) -> None:
        """Check that the mesh clock is in sync."""
        if self.stopping:
            return
        await self.manager.broadcast_time()


def get_plejd_site_from_config_entry(
        hass: HomeAssistant, config_entry: ConfigEntry
) -> PlejdSite:
    """Get the Plejd site corresponding to a config entry."""
    return cast(PlejdSite, hass.data[DOMAIN].get(config_entry.entry_id))