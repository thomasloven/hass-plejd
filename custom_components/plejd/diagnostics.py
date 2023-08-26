import pyplejd
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
):
    """Return the plejd site configureation from the cloud"""
    plejdManager = pyplejd.PlejdManager(config_entry.data)
    return await plejdManager.get_raw_sitedata()
