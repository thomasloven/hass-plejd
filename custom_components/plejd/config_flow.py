import voluptuous as vol
import logging
from homeassistant.config_entries import ConfigFlow
from homeassistant.components import bluetooth

from pyplejd import api
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PlejdConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._discovered = False

    async def async_step_bluetooth(self, discovery_info):
        self._discovered = True
        return await self.async_step_user()

    async def async_step_user(self, info=None):
        if info is None:
            if self._async_current_entries():
                return self.async_abort(reason="single_instance_allowed")
            if not bluetooth.async_scanner_count(self.hass, connectable=True):
                return self.async_abort(reason="bluetooth_not_available")
            if not self._discovered:
                return self.async_abort(reason="no_device_discovered")
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
            sites = await api.get_sites(
                self.credentials["username"], self.credentials["password"]
            )
            self.sites = {
                site["site"]["siteId"]: site["site"]["title"] for site in sites
            }
            return self.async_show_form(
                step_id="picksite",
                data_schema=vol.Schema({vol.Required("site"): vol.In(self.sites)}),
            )

        siteTitle = self.sites[info["site"]]
        data = {
            "username": self.credentials["username"],
            "password": self.credentials["password"],
            "siteId": info["site"],
            "siteTitle": siteTitle,
        }
        return self.async_create_entry(title=siteTitle, data=data)
