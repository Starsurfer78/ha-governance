import logging
import asyncio
import json
import hashlib
from collections import deque
from typing import Any, Dict, Optional
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_STATE_CHANGED
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from .const import (
    DOMAIN,
    CONF_POLICY_PATH,
    CONF_COOLDOWN_SECONDS,
    DEFAULT_POLICY_PATH,
    DEFAULT_COOLDOWN_SECONDS,
    DISPATCHER_POLICIES_UPDATED,
    DISPATCHER_POLICY_EXECUTED,
    DISPATCHER_DECISION_UPDATED,
)
from .policy_engine import load_policies, evaluate, ensure_policy_file_exists
from .enforcement import apply as apply_enforcement, is_self_caused, setup_periodic_cleanup
from .config_flow import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)
_EVENT_LOCK = asyncio.Lock()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    data = hass.data[DOMAIN]
    data["entry"] = entry
    data["options"] = {
        CONF_POLICY_PATH: entry.options.get(CONF_POLICY_PATH, DEFAULT_POLICY_PATH),
        CONF_COOLDOWN_SECONDS: entry.options.get(CONF_COOLDOWN_SECONDS, DEFAULT_COOLDOWN_SECONDS),
    }
    data.setdefault("reload_lock", asyncio.Lock())
    data.setdefault("policy_stats", {})
    data.setdefault("policy_snapshot_hash", "")
    data.setdefault("audit_log", deque(maxlen=1000))
    data["last_decision"] = None
    await hass.async_add_executor_job(
        ensure_policy_file_exists,
        hass,
        hass.data[DOMAIN]["options"].get(CONF_POLICY_PATH),
    )
    await _reload_policies(hass)
    await setup_periodic_cleanup(hass)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    _setup_daily_stats_reset(hass)
    async def _on_started(event) -> None:
        await _register_listeners(hass)
        _LOGGER.info("[ha_governance] Event listeners registered after HA startup")
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _on_started)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return unload_ok

async def _reload_policies(hass: HomeAssistant) -> None:
    data = hass.data[DOMAIN]
    lock = data.setdefault("reload_lock", asyncio.Lock())
    async with lock:
        options = data["options"]
        path = options.get(CONF_POLICY_PATH, DEFAULT_POLICY_PATH)
        policies = await load_policies(hass, path)
        data["policies"] = tuple(policies)
        relevant_entities = set()
        for p in policies:
            when = p.get("when", {})
            if isinstance(when, dict):
                for entity_path in when.keys():
                    parts = str(entity_path).split(".")
                    if len(parts) >= 2:
                        relevant_entities.add(parts[0] + "." + parts[1])
        data["relevant_entities"] = frozenset(relevant_entities)
        try:
            snapshot_hash = hashlib.sha256(
                json.dumps(policies, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        except Exception:
            snapshot_hash = ""
        data["policy_snapshot_hash"] = snapshot_hash
        entry = data.get("entry")
        if entry is not None:
            new_title = f"HA Governance ({len(policies)})"
            if entry.title != new_title:
                hass.config_entries.async_update_entry(entry, title=new_title)
        async_dispatcher_send(hass, DISPATCHER_POLICIES_UPDATED)


def _setup_daily_stats_reset(hass: HomeAssistant) -> None:
    async def _reset_daily_stats(now) -> None:
        data = hass.data.get(DOMAIN, {})
        stats = data.get("policy_stats", {})
        for entry in stats.values():
            entry["today"] = 0
            entry["success_today"] = 0
            entry["error_today"] = 0
            entry["cooldown_skipped_today"] = 0
        async_dispatcher_send(hass, DISPATCHER_POLICY_EXECUTED, None)
    async_track_time_change(hass, _reset_daily_stats, hour=0, minute=0, second=0)

async def _register_listeners(hass: HomeAssistant) -> None:
    async def _handle_event(event) -> None:
        try:
            async with _EVENT_LOCK:
                policies = hass.data[DOMAIN].get("policies", [])
                if not policies:
                    return
                entity_id = None
                try:
                    entity_id = event.data.get("entity_id")
                except Exception:
                    entity_id = None
                if entity_id and entity_id.startswith("sensor.ha_governance_"):
                    return
                if is_self_caused(getattr(event, "context", None)):
                    _LOGGER.debug("[ha_governance] Ignoring self-caused event")
                    return
                relevant = hass.data[DOMAIN].get("relevant_entities")
                if entity_id and relevant and entity_id not in relevant:
                    return
                winner, evaluations = evaluate(hass, list(policies))
                result = None
                if winner:
                    result = await apply_enforcement(
                        hass,
                        winner,
                        hass.data[DOMAIN]["options"],
                        getattr(event, "context", None),
                    )
                    if result == "skipped_cooldown":
                        name = str(winner.get("name", ""))
                        for e in evaluations:
                            if e.get("name") == name and e.get("matched"):
                                e["cooldown_blocked"] = True
                                break
                if winner is None and result is None:
                    return
                data = hass.data[DOMAIN]
                snapshot_hash = data.get("policy_snapshot_hash", "")
                context_id = None
                last_decision = data.get("last_decision")
                ctx = getattr(event, "context", None)
                if ctx is not None:
                    try:
                        context_id = ctx.id
                    except Exception:
                        context_id = None
                from homeassistant.util import dt as dt_util

                final_policy_name = str(winner.get("name", "")) if winner else None
                if last_decision is not None:
                    if (
                        last_decision.get("final_policy") == final_policy_name
                        and last_decision.get("enforcement_result") == result
                        and last_decision.get("event_type") == event.event_type
                        and last_decision.get("entity_id") == entity_id
                        and last_decision.get("policy_snapshot_hash") == snapshot_hash
                    ):
                        return
                decision = {
                    "timestamp": dt_util.utcnow().isoformat(),
                    "event_type": event.event_type,
                    "entity_id": entity_id,
                    "policy_snapshot_hash": snapshot_hash,
                    "evaluations": tuple(evaluations),
                    "final_policy": final_policy_name,
                    "enforcement_result": result,
                    "context_id": context_id,
                }
                audit_log = data.get("audit_log")
                if audit_log is not None:
                    audit_log.append(decision)
                data["last_decision"] = decision
                async_dispatcher_send(hass, DISPATCHER_DECISION_UPDATED)
        except Exception as e:
            _LOGGER.error(f"[ha_governance] Error in event handler: {e}", exc_info=True)
    hass.bus.async_listen(EVENT_STATE_CHANGED, _handle_event)

def async_get_options_flow(config_entry: ConfigEntry):
    return OptionsFlowHandler(config_entry)

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
