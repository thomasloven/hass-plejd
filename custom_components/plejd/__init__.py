import logging
from datetime import timedelta

from home_assistant_bluetooth.models import BluetoothServiceInfoBleak

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import BluetoothCallbackMatcher
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

import pyplejd

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.SCENE, Platform.EVENT]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a Plejd mesh for a config entry."""
    hass.data.setdefault(DOMAIN, {})

    plejdManager = pyplejd.PlejdManager(config_entry.data)
    # TODO: Catch errors
    await plejdManager.init()

    devices = plejdManager.devices
    scenes = plejdManager.scenes

    # Add a service entries for unknown or unhandled device types
    device_registry = dr.async_get(hass)
    for dev in devices:
        if dev.outputType in [pyplejd.UNKNOWN, pyplejd.SENSOR]:
            device_registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                identifiers={(DOMAIN, f"{dev.BLEaddress}", f"{dev.address}")},
                manufacturer="Plejd",
                name=dev.name,
                model=dev.hardware,
                suggested_area=dev.room,
                sw_version=f"{dev.firmware}",
                entry_type=dr.DeviceEntryType.SERVICE,
            )

    data = hass.data[DOMAIN].setdefault(config_entry.entry_id, {})
    data.update(
        {
            "manager": plejdManager,
            "devices": devices,
            "scenes": scenes,
            "stopping": False,
        }
    )

    # Close any stale connections that may be open
    for dev in devices:
        ble_device = bluetooth.async_ble_device_from_address(hass, dev.BLEaddress, True)
        if ble_device:
            await plejdManager.close_stale(ble_device)

    # Search for devices in the mesh
    def _discovered_plejd(service_info: BluetoothServiceInfoBleak, *_):
        """Register any discovered plejd devices with the manager."""
        plejdManager.add_mesh_device(service_info.device, service_info.rssi)
        hass.async_create_task(plejdManager.ping())

    config_entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _discovered_plejd,
            BluetoothCallbackMatcher(
                connectable=True, service_uuid=pyplejd.const.PLEJD_SERVICE.lower()
            ),
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )

    # Run through already discovered devices and add plejds to the mesh
    for service_info in bluetooth.async_discovered_service_info(hass, True):
        if pyplejd.PLEJD_SERVICE.lower() in service_info.advertisement.service_uuids:
            plejdManager.add_mesh_device(service_info.device, service_info.rssi)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    async def _ping(timestamp):
        """Ping the plejd mesh periodically to keep the connection alive."""
        if data["stopping"]:
            return
        if not await plejdManager.ping():
            _LOGGER.debug("Ping failed")

    config_entry.async_on_unload(
        async_track_time_interval(
            hass, _ping, plejdManager.ping_interval, name="Plejd keep-alive"
        )
    )

    async def _broadcast_time(timestamp):
        """Check that the mesh clock is in sync once per hour."""
        if data["stopping"]:
            return
        await plejdManager.broadcast_time()

    config_entry.async_on_unload(
        async_track_time_interval(
            hass, _broadcast_time, timedelta(hours=1), name="Plejd sync time"
        )
    )

    async def _stop(ev):
        """Mark integration as stopping before disconnecting to avoid untimely reconnections by the periodic ping."""
        data["stopping"] = True
        await plejdManager.disconnect()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _stop)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        if entry.entry_id in hass.data[DOMAIN]:
            del hass.data[DOMAIN][entry.entry_id]
    return unload_ok
