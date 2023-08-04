import voluptuous as vol
import logging
from homeassistant.config_entries import ConfigFlow
from homeassistant.components import bluetooth

from pyplejd import get_sites
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PlejdConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._discovered = False

    async def async_step_bluetooth(self, discovery_info):
        self._discovered = True
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self._async_in_progress():
            return self.async_abort(reason="single_instance_allowed")
        return await self.async_step_user()

    async def async_step_user(self, info=None):
        if info is None:
            if not bluetooth.async_scanner_count(self.hass, connectable=True):
                return self.async_abort(reason="bluetooth_not_available")
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {vol.Required("username"): str, vol.Required("password"): str}
                ),
            )
        self.credentials = info
        return await self.async_step_picksite()

    async def async_step_picksite(self, info=None):
        if info is None:
            sites = await get_sites(
                self.credentials["username"], self.credentials["password"]
            )
            self.sites = {
                site.siteId: f"{site.title} ({site.deviceCount} devices)"
                for site in sites
            }
            return self.async_show_form(
                step_id="picksite",
                data_schema=vol.Schema({vol.Required("site"): vol.In(self.sites)}),
            )

        await self.async_set_unique_id(info["site"])
        self._abort_if_unique_id_configured()

        siteTitle = self.sites[info["site"]]
        data = {
            "username": self.credentials["username"],
            "password": self.credentials["password"],
            "siteId": info["site"],
            "siteTitle": siteTitle,
        }
        return self.async_create_entry(title=siteTitle, data=data)
