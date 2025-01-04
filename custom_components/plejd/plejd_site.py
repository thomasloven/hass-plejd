"""Plejd site mesh controller."""

from datetime import timedelta
import logging
from typing import cast, Callable
from collections import defaultdict

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from home_assistant_bluetooth import BluetoothServiceInfoBleak

from pyplejd import (
    PlejdManager,
    ConnectionError,
    AuthenticationError,
    PLEJD_SERVICE,
    DeviceTypes as dt,
)

from .const import DOMAIN
from .plejd_entity import register_unknown_device


_LOGGER = logging.getLogger(__name__)

SITE_DATA_STORE_KEY = "plejd_site_data"
SITE_DATA_STORE_VERSION = 1


class PlejdSite:
    """Controller for a Plejd site mesh."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        username: str,
        password: str,
        siteId: str,
    ) -> None:
        """Initialize plejd site mesh."""
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = config_entry

        self.credentials = {
            "username": username,
            "password": password,
            "siteId": siteId,
        }

        self.store = Store(hass, SITE_DATA_STORE_VERSION, SITE_DATA_STORE_KEY)

        self.manager: PlejdManager = PlejdManager(**self.credentials)

        self.devices: list[dt.PlejdDevice] = []

        self.started = False
        self.stopping = False

        self.add_device_callbacks = defaultdict(list)

    def register_platform_add_device_callback(
        self,
        callback: Callable[[dt.PlejdDevice], None],
        output_type: dt.PlejdDeviceType,
    ) -> None:
        self.add_device_callbacks[output_type].append(callback)

    async def start(self) -> None:
        """Setup and connect to plejd site."""
        if not (site_data_cache := await self.store.async_load()) or not isinstance(
            site_data_cache, dict
        ):
            site_data_cache = {}

        cached_site_data = site_data_cache.get(self.credentials["siteId"])

        await self.manager.init(cached_site_data)

        self.devices = self.manager.devices

        for device in self.devices:
            if adders := self.add_device_callbacks.get(device.outputType):
                for adder in adders:
                    adder(device)
            else:
                if device.outputType:
                    register_unknown_device(
                        self.hass, device, self.config_entry.entry_id
                    )

        # Close any stale connections that may be open
        for dev in self.devices:
            if dev.BLEaddress:
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, dev.BLEaddress, True
                )
                if ble_device:
                    await self.manager.close_stale(ble_device)

        # Register callback for bluetooth discover
        self.config_entry.async_on_unload(
            bluetooth.async_register_callback(
                self.hass,
                self._discovered,
                bluetooth.match.BluetoothCallbackMatcher(
                    connectable=True, service_uuid=PLEJD_SERVICE.lower()
                ),
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )

        # Run through already discovered devices and add plejds to the manager
        for service_info in bluetooth.async_discovered_service_info(self.hass, True):
            if PLEJD_SERVICE.lower() in service_info.advertisement.service_uuids:
                self._discovered(service_info, connect=False)

        # Ping the mesh periodically to maintain the connection
        self.config_entry.async_on_unload(
            async_track_time_interval(
                self.hass,
                self._ping,
                self.manager.ping_interval,
                name="Plejd keep-alive",
            )
        )

        # Check that the mesh clock is in sync once per hour
        self.config_entry.async_on_unload(
            async_track_time_interval(
                self.hass,
                self._broadcast_time,
                timedelta(hours=1),
                name="Plejd sync time",
            )
        )

        self.started = True

        self.hass.async_create_task(self._ping())
        self.hass.async_create_task(self._broadcast_time())

    async def stop(self, *_) -> None:
        """Disconnect mesh and tear down site configuration."""
        self.stopping = True

        if not (site_data_cache := await self.store.async_load()) or not isinstance(
            site_data_cache, dict
        ):
            site_data_cache = {}
        site_data_cache[self.credentials["siteId"]] = (
            await self.manager.get_raw_sitedata()
        )
        await self.store.async_save(site_data_cache)

        await self.manager.disconnect()

    def _discovered(
        self, service_info: BluetoothServiceInfoBleak, *_, connect: bool = True
    ) -> None:
        """Register any discovered plejd device with the manager."""
        new_device = self.manager.add_mesh_device(
            service_info.device, service_info.rssi
        )
        if connect and new_device:
            self.hass.async_create_task(self._ping())

    async def _ping(self, *_) -> None:
        """Ping the plejd mesh to connect or maintain the connection."""
        if self.stopping or not self.started:
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
