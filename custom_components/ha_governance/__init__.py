import logging
from typing import Any, Dict, Optional
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_STATE_CHANGED
from .const import DOMAIN, CONF_POLICY_PATH, CONF_COOLDOWN_SECONDS, DEFAULT_POLICY_PATH, DEFAULT_COOLDOWN_SECONDS
from .policy_engine import load_policies, evaluate
from .enforcement import apply as apply_enforcement
from .config_flow import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["options"] = {
        CONF_POLICY_PATH: entry.options.get(CONF_POLICY_PATH, DEFAULT_POLICY_PATH),
        CONF_COOLDOWN_SECONDS: entry.options.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS),
    }
    async def _on_started(event) -> None:
        await _reload_policies(hass)
        await _register_listeners(hass)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _on_started)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True

async def _reload_policies(hass: HomeAssistant) -> None:
    options = hass.data[DOMAIN]["options"]
    path = options.get(CONF_POLICY_PATH, DEFAULT_POLICY_PATH)
    policies = await load_policies(hass, path)
    hass.data[DOMAIN]["policies"] = policies

async def _register_listeners(hass: HomeAssistant) -> None:
    async def _handle_event(event) -> None:
        policies = hass.data[DOMAIN].get("policies", [])
        if not policies:
            return
        p = evaluate(hass, policies)
        if p:
            await apply_enforcement(hass, p, hass.data[DOMAIN]["options"])
    hass.bus.async_listen(EVENT_STATE_CHANGED, _handle_event)

def async_get_options_flow(config_entry: ConfigEntry):
    return OptionsFlowHandler(config_entry)
