import pyplejd


async def async_get_config_entry_diagnostics(hass, config_entry):
    plejdManager = pyplejd.PlejdManager(config_entry.data)

    return await plejdManager.get_site_data()
