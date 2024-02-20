"""Support for Plejd mesh devices."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN, CONF_SITE_ID
from .plejd_site import PlejdSite, ConnectionError, AuthenticationError

PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.SCENE, Platform.EVENT, Platform.BINARY_SENSOR]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a Plejd mesh for a config entry."""

    hass.data.setdefault(DOMAIN, {})

    site = hass.data[DOMAIN][config_entry.entry_id] = PlejdSite(
            hass,
            config_entry,
            username=config_entry.data.get(CONF_USERNAME),
            password=config_entry.data.get(CONF_PASSWORD),
            siteId=config_entry.data.get(CONF_SITE_ID)
        )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    try:
        await site.start()
    except ConnectionError as err:
        raise ConfigEntryNotReady from err
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed from err

    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, site.stop)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if not unload_ok:
        return unload_ok

    site: PlejdSite = hass.data[DOMAIN][entry.entry_id]
    await site.stop()
    del hass.data[DOMAIN][entry.entry_id]

    return unload_ok
