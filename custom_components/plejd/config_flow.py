"""Config flow for Plejd integration

Provides user initiated configuration flow.
Discovery of Plejd mesh devices through Bluetooth.
Reauthentication when issues with cloud api credentials are reported.
"""
import voluptuous as vol
import logging
from typing import Any
from homeassistant.config_entries import ConfigFlow, ConfigEntry
from homeassistant.components import bluetooth

from pyplejd import get_sites, verify_credentials, AuthenticationError, ConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PlejdConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Plejd config flow."""
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Plejd config flow"""
        self.config: dict[str, Any] = {}
        self.reauth_config_entry: ConfigEntry | None = None
        self.sites: dict[str, str] = {}

    async def async_step_bluetooth(self, discovery_info):
        """Handle a discovered Plejd mesh."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if self._async_in_progress():
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_user()

    async def async_step_reauth(self, user_input=None):
        """Trigger a reauthentication flow."""

        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        assert config_entry
        self.reauth_config_entry = config_entry

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        if user_input is not None:
            return await self.async_step_user()

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({})
        )

    async def async_step_user(self, info=None):
        """Handle a flow initiated by user."""

        if not bluetooth.async_scanner_count(self.hass, connectable=True):
                return self.async_abort(reason="bluetooth_not_available")

        errors = {}

        if info is not None:
            self.config = {
                "username": info["username"],
                "password": info["password"],
            }

            try:
                await verify_credentials(username=self.config["username"], password=self.config["password"])
            except AuthenticationError:
                errors["base"] = "faulty_credentials"
            except ConnectionError:
                return self.async_abort(reason="no_cloud_connection")
            else:
                return await self.async_step_picksite()

        return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {vol.Required("username"): str, vol.Required("password"): str}
                ),
                errors=errors
            )

    async def async_step_picksite(self, info=None):
        """Select Plejd site to control."""

        if self.reauth_config_entry:
            self.config.update({
                "siteId": self.reauth_config_entry.data["siteId"],
                "siteTitle": self.reauth_config_entry.data["siteTitle"],
            })

            self.hass.config_entries.async_update_entry(
                self.reauth_config_entry,
                data = self.config,
            )
            await self.hass.config_entries.async_reload(self.reauth_config_entry.entry_id)

            return self.async_abort(reason="reauth_successful")
        elif info is not None:
            siteId = info["site"]

            await self.async_set_unique_id(siteId)
            self._abort_if_unique_id_configured()

            self.config.update({
                "siteId": siteId,
                "siteTitle": self.sites[siteId],
            })

            return self.async_create_entry(title=self.sites[siteId], data=self.config)

        sites = await get_sites(username=self.config["username"], password=self.config["password"])

        options = {}
        for site in sites:
            self.sites[site.siteId] = site.title

        return self.async_show_form(
                step_id="picksite",
                data_schema=vol.Schema({vol.Required("site"): vol.In(self.sites)}),
            )

