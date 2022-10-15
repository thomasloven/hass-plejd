import logging

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import BluetoothCallbackMatcher
from homeassistant import config_entries
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
import homeassistant.util.dt as dt_util

from . import pyplejd

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    _LOGGER.error("Setting up plejd")
    if not hass.config_entries.async_entries("plejd"):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                "plejd", context={"source": config_entries.SOURCE_IMPORT}, data={}
            )
        )

    return True


BLE_UUID_SUFFIX = '6085-4726-be45-040c957391b5'
PLEJD_SERVICE = f'31ba0001-{BLE_UUID_SUFFIX}'

DEVICE_ADDR = "fc:f8:73:37:78:0e"

DOMAIN = "plejd"

async def async_setup_entry(hass, config_entry):

    _LOGGER.info(config_entry.data)

    plejdManager = pyplejd.PlejdManager(config_entry.data)
    devices = await plejdManager.get_devices()
    for dev in devices.values():
        ble_device = bluetooth.async_ble_device_from_address(
            hass, dev.BLE_address, True
        )
        if ble_device:
            await plejdManager.close_stale(ble_device)

    hass.data.setdefault(DOMAIN, {}).update(
        {
            "stopping": False,
            "manager": plejdManager,
            "devices": devices,
        }
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, ["light", "switch"])

    async def _ping(now=None):
        if hass.data[DOMAIN]["stopping"]: return
        if not await plejdManager.keepalive():
            _LOGGER.debug("Ping failed")
        else:
            await plejdManager.poll() # TODO: Remove when not needed
        hass.data[DOMAIN]["ping_timer"] = async_track_point_in_utc_time(
                hass,
                _ping,
                dt_util.utcnow() + plejdManager.keepalive_interval
            )
        # TODO: Pinging often now because that's how to get updates with an ESP repeater
        # Once that's been fixed and the esp gets the LASTDATA announcements this can be
        # increased significantly to like 5-10 minutes

    hass.async_create_task(_ping())

    bluetooth.async_register_callback(
            hass,
            plejdManager.discover_plejd,
            BluetoothCallbackMatcher(
                    connectable=True,
                    service_uuid=pyplejd.const.PLEJD_SERVICE.lower()
                ),
            bluetooth.BluetoothScanningMode.PASSIVE
        )

    

    async def _stop(ev):
        hass.data[DOMAIN]["stopping"] = True
        if "ping_timer" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["ping_timer"]()
        await plejdManager.disconnect()
    
    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _stop)
    )

    for service_info in bluetooth.async_discovered_service_info(hass, True):
        if PLEJD_SERVICE.lower() in service_info.advertisement.service_uuids:
            plejdManager.discover_plejd(service_info)

    
    _LOGGER.error("async_setup_entry done")

    
    return True

    
    
