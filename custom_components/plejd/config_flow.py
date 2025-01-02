"""Config flow for Plejd integration

Provides user initiated configuration flow.
Discovery of Plejd mesh devices through Bluetooth.
Reauthentication when issues with cloud api credentials are reported.
"""

import voluptuous as vol
import logging
from typing import Any
from homeassistant.config_entries import ConfigFlow, ConfigEntry, FlowResult
from homeassistant.components import bluetooth
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from pyplejd import get_sites, verify_credentials, AuthenticationError, ConnectionError
from .const import DOMAIN, CONF_SITE_ID, CONF_SITE_TITLE

_LOGGER = logging.getLogger(__name__)


class PlejdConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Plejd config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Plejd config flow"""
        self.config: dict[str, Any] = {}
        self.reauth_config_entry: ConfigEntry | None = None
        self.sites: dict[str, str] = {}

    async def async_step_bluetooth(self, _: Any) -> FlowResult:
        """Handle a discovered Plejd mesh."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        # Several devices may be discovered, but most likely they all belong to the same mesh.
        # So this makes sure we only get a single discovery message.
        if self._async_in_progress():
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_user()

    async def async_step_reauth(self, _: dict[str, Any] | None = None) -> FlowResult:
        """Trigger a reauthentication flow."""

        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        assert config_entry
        self.reauth_config_entry = config_entry

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return await self.async_step_user()

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=vol.Schema({})
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by user."""

        if not bluetooth.async_scanner_count(self.hass, connectable=True):
            return self.async_abort(reason="bluetooth_not_available")

        errors = {}

        if user_input is not None:
            self.config = {
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }

            try:
                await verify_credentials(
                    username=self.config[CONF_USERNAME],
                    password=self.config[CONF_PASSWORD],
                )
            except AuthenticationError:
                errors["base"] = "faulty_credentials"
            except ConnectionError:
                return self.async_abort(reason="no_cloud_connection")
            else:
                return await self.async_step_picksite()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
        )

    async def async_step_picksite(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select Plejd site to control."""

        if self.reauth_config_entry:
            self.config.update(
                {
                    CONF_SITE_ID: self.reauth_config_entry.data[CONF_SITE_ID],
                    CONF_SITE_TITLE: self.reauth_config_entry.data[CONF_SITE_TITLE],
                }
            )

            self.hass.config_entries.async_update_entry(
                self.reauth_config_entry,
                data=self.config,
            )
            await self.hass.config_entries.async_reload(
                self.reauth_config_entry.entry_id
            )

            return self.async_abort(reason="reauth_successful")
        elif user_input is not None:
            siteId = user_input["site"]

            await self.async_set_unique_id(siteId)
            self._abort_if_unique_id_configured()

            self.config.update(
                {
                    CONF_SITE_ID: siteId,
                    CONF_SITE_TITLE: self.sites[siteId],
                }
            )

            return self.async_create_entry(title=self.sites[siteId], data=self.config)

        sites = await get_sites(
            username=self.config[CONF_USERNAME], password=self.config[CONF_PASSWORD]
        )

        options = {}
        for site in sites:
            self.sites[site["siteId"]] = site["title"]
            options[site["siteId"]] = f"{site["title"]} ({site["deviceCount"]} devices)"

        return self.async_show_form(
            step_id="picksite",
            data_schema=vol.Schema({vol.Required("site"): vol.In(options)}),
        )
