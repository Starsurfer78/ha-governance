import logging
import asyncio
from typing import Any, Dict, Optional
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_STATE_CHANGED
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import DOMAIN, CONF_POLICY_PATH, CONF_COOLDOWN_SECONDS, DEFAULT_POLICY_PATH, DEFAULT_COOLDOWN_SECONDS, DISPATCHER_POLICIES_UPDATED
from .policy_engine import load_policies, evaluate, ensure_policy_file_exists
from .enforcement import apply as apply_enforcement, is_self_caused, setup_periodic_cleanup
from .config_flow import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)
_EVENT_LOCK = asyncio.Lock()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["entry"] = entry
    hass.data[DOMAIN]["options"] = {
        CONF_POLICY_PATH: entry.options.get(CONF_POLICY_PATH, DEFAULT_POLICY_PATH),
        CONF_COOLDOWN_SECONDS: entry.options.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS),
    }
    await hass.async_add_executor_job(
        ensure_policy_file_exists,
        hass,
        hass.data[DOMAIN]["options"].get(CONF_POLICY_PATH),
    )
    await _reload_policies(hass)
    await _register_listeners(hass)
    await setup_periodic_cleanup(hass)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    async def _on_started(event) -> None:
        await _reload_policies(hass)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _on_started)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return unload_ok

async def _reload_policies(hass: HomeAssistant) -> None:
    data = hass.data[DOMAIN]
    options = data["options"]
    path = options.get(CONF_POLICY_PATH, DEFAULT_POLICY_PATH)
    policies = await load_policies(hass, path)
    data["policies"] = policies
    entry = data.get("entry")
    if entry is not None:
        new_title = f"HA Governance ({len(policies)})"
        if entry.title != new_title:
            hass.config_entries.async_update_entry(entry, title=new_title)
    async_dispatcher_send(hass, DISPATCHER_POLICIES_UPDATED)

async def _register_listeners(hass: HomeAssistant) -> None:
    async def _handle_event(event) -> None:
        async with _EVENT_LOCK:
            policies = hass.data[DOMAIN].get("policies", [])
            if not policies:
                return
            if is_self_caused(getattr(event, "context", None)):
                _LOGGER.debug("[ha_governance] Ignoring self-caused event")
                return
            p = evaluate(hass, policies)
            if p:
                await apply_enforcement(hass, p, hass.data[DOMAIN]["options"], getattr(event, "context", None))
    hass.bus.async_listen(EVENT_STATE_CHANGED, _handle_event)

def async_get_options_flow(config_entry: ConfigEntry):
    return OptionsFlowHandler(config_entry)

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
