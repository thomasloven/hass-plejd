import voluptuous as vol
import logging
from homeassistant.config_entries import ConfigFlow, ConfigEntry
from homeassistant.components import bluetooth

from pyplejd import get_sites
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PlejdConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    reauth_entry: ConfigEntry|None = None

    async def async_step_bluetooth(self, discovery_info):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self._async_in_progress():
            return self.async_abort(reason="single_instance_allowed")
        return await self.async_step_user()

    async def async_step_reauth(self, user_input=None):
        """Perform reauth if login failed."""
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Dialog to inform user that reauthorization is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
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
        if self.reauth_entry:
            self.hass.config_entries.async_update_entry(
                self.reauth_entry,
                title = self.reauth_entry.data["siteTitle"],
                data = {
                    "username": self.credentials["username"],
                    "password": self.credentials["password"],
                    "siteId": self.reauth_entry.data["siteId"],
                    "siteTitle": self.reauth_entry.data["siteTitle"],
                }
                )
            await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        if info is None:
            sites = await get_sites(
                self.credentials["username"], self.credentials["password"]
            )
            self.sites = {
                site.siteId: site.title for site in sites
            }
            options = {
                site.siteId: f"{site.title} ({site.deviceCount} devices)"
                for site in sites
            }
            return self.async_show_form(
                step_id="picksite",
                data_schema=vol.Schema({vol.Required("site"): vol.In(options)}),
            )

        await self.async_set_unique_id(info["site"])
        self._abort_if_unique_id_configured()

        siteId = info["site"]
        siteTitle = self.sites[siteId]

        data = {
            "username": self.credentials["username"],
            "password": self.credentials["password"],
            "siteId": siteId,
            "siteTitle": siteTitle,
        }
        return self.async_create_entry(title=siteTitle, data=data)
