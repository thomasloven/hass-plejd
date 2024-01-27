"""Diagnostic support for Plejd."""
from typing import TypeVar
from pyplejd import PlejdManager
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .plejd_site import get_plejd_site_from_config_entry, PlejdSite


REDACT_KEYS = {
    "site": {
        "previousOwners": True,
        "siteId": True,
        "astroTable": True,
        "city": True,
        "coordinates": True,
        "country": True,
        "deviceAstroTable": True,
        "zipCode": True,
    },
    "plejdMesh": {
        "siteId": True,
        "plejdMeshId": True,
        "meshKey": True,
        "cryptoKey": True,
    },
    "rooms": {
        "siteId": True,
    },
    "scenes": {
        "siteId": True,
    },
    "devices": {
        "siteId": True,
    },
    "plejdDevices": {
        "siteId": True,
        "installer": True,
        "coordinates": True,
    },
    "gateways": True,
    "resourceSets": True,
    "timeEvents": True,
    "sceneSteps": True,
    "astroEvents": True,
    "inputSettings": {
        "siteId": True,
    },
    "outputSettings": {
        "siteId": True,
    },
    "motionSensors": {
        "siteId": True,
    },
    "sitePermission": {
        "siteId": True,
        "userId": True,
        "user": True,
        "site": True,
    }
}

T = TypeVar('T', dict, list)

def redact(data: T, keys: dict) -> T:
    """Recursively redact potentially sensitive information from Plejd Site data."""
    if isinstance(data, list):
        return [redact(item, keys) for item in data]
    for key,value in keys.items():
        if key in data:
            if value is True:
                data[key] = "<REDACTED>"
            else:
                data[key] = redact(data[key], value)
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
):
    """Return the plejd site configuration from the cloud."""

    site: PlejdSite = get_plejd_site_from_config_entry(hass, config_entry)
    plejdManager: PlejdManager = site.manager
    sitedata = await plejdManager.get_raw_sitedata()
    return redact(sitedata, REDACT_KEYS)
