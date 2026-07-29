"""Config flow for Pont Chaban-Delmas integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class PontChabanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Pont Chaban-Delmas."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step — no parameters needed."""
        # Only allow a single instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Pont Chaban-Delmas", data={})

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
