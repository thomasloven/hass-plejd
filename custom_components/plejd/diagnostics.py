import pyplejd
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


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

def redact(data: dict | list, keys: dict):
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
    """Return the plejd site configureation from the cloud"""
    plejdManager = pyplejd.PlejdManager(config_entry.data)
    sitedata = await plejdManager.get_raw_sitedata()
    return redact(sitedata, REDACT_KEYS)
