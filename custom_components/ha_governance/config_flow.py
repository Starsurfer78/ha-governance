from typing import Any, Dict
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_COOLDOWN_SECONDS, CONF_MODE_ENTITY, CONF_POLICY_PATH, DEFAULT_COOLDOWN_SECONDS, DEFAULT_POLICY_PATH

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="HA Governance", data={}, options=user_input)
        schema = vol.Schema({
            vol.Optional(CONF_COOLDOWN_SECONDS, default=DEFAULT_COOLDOWN_SECONDS): int,
            vol.Optional(CONF_MODE_ENTITY, default=""): str,
            vol.Optional(CONF_POLICY_PATH, default=DEFAULT_POLICY_PATH): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_import(self, user_input: Dict[str, Any]):
        return await self.async_step_user(user_input)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        data = self.config_entry.options
        schema = vol.Schema({
            vol.Optional(CONF_COOLDOWN_SECONDS, default=data.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS)): int,
            vol.Optional(CONF_MODE_ENTITY, default=data.get(CONF_MODE_ENTITY, "")): str,
            vol.Optional(CONF_POLICY_PATH, default=data.get(CONF_POLICY_PATH, DEFAULT_POLICY_PATH)): str,
        })
        return self.async_show_form(step_id="init", data_schema=schema)
