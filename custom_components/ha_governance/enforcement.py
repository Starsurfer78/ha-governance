from time import monotonic
from typing import Any, Dict, Tuple, Optional, Set
import asyncio
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant, Context
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util
from .const import CONF_COOLDOWN_SECONDS, DOMAIN, DISPATCHER_POLICY_EXECUTED

def _split_service(s: str) -> Tuple[str, str]:
    parts = s.split(".")
    return parts[0], parts[1]

def _now() -> float:
    return monotonic()

def _cooldown_ok(hass: HomeAssistant, policy: Dict[str, Any], cooldown_seconds: int) -> bool:
    key = policy.get("name", "")
    store = hass.data.setdefault(DOMAIN, {})
    cd = store.setdefault("cooldown", {})
    last = cd.get(key, 0.0)
    if _now() - float(last) < float(cooldown_seconds):
        return False
    cd[key] = _now()
    return True


def _update_policy_stats(hass: HomeAssistant, policy_name: str, result: str) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    stats = data.setdefault("policy_stats", {})
    entry = stats.setdefault(
        policy_name,
        {
            "total": 0,
            "today": 0,
            "success_total": 0,
            "success_today": 0,
            "error_total": 0,
            "error_today": 0,
            "cooldown_skipped_total": 0,
            "cooldown_skipped_today": 0,
            "last_executed": None,
            "last_result": None,
        },
    )
    now = dt_util.utcnow().isoformat()
    entry["total"] += 1
    entry["today"] += 1
    if result == "success":
        entry["success_total"] += 1
        entry["success_today"] += 1
    elif result == "error":
        entry["error_total"] += 1
        entry["error_today"] += 1
    elif result == "skipped_cooldown":
        entry["cooldown_skipped_total"] += 1
        entry["cooldown_skipped_today"] += 1
    entry["last_executed"] = now
    entry["last_result"] = result
    async_dispatcher_send(hass, DISPATCHER_POLICY_EXECUTED, policy_name)

_LOGGER = logging.getLogger(__name__)
_COOLDOWN_LOCK = asyncio.Lock()
_ENFORCEMENT_CONTEXTS: Set[str] = set()
_CONTEXT_CLEANUP_DELAY = 10

def is_self_caused(event_context: Optional[Context]) -> bool:
    if event_context is None:
        return False
    parent_id = getattr(event_context, "parent_id", None)
    if not parent_id:
        return False
    return parent_id in _ENFORCEMENT_CONTEXTS

async def apply(hass: HomeAssistant, policy: Dict[str, Any], options: Dict[str, Any], trigger_context: Optional[Context] = None) -> Optional[str]:
    cooldown = int(options.get(CONF_COOLDOWN_SECONDS, 10))
    policy_name = str(policy.get("name", ""))
    async with _COOLDOWN_LOCK:
        if not _cooldown_ok(hass, policy, cooldown):
            _LOGGER.info("[ha_governance] LOOP_PREVENTED")
            _update_policy_stats(hass, policy_name, "skipped_cooldown")
            return "skipped_cooldown"
    enforce = policy.get("enforce", {})
    svc = enforce.get("service", "")
    tgt = enforce.get("target", {})
    dat = enforce.get("data", {})
    if not svc:
        return None
    domain, svc_name = _split_service(svc)
    enforcement_context = Context(parent_id=getattr(trigger_context, "id", None)) if trigger_context else Context()
    async with _COOLDOWN_LOCK:
        _ENFORCEMENT_CONTEXTS.add(enforcement_context.id)
    _LOGGER.info("[ha_governance] POLICY_TRIGGERED")
    try:
        await hass.services.async_call(domain, svc_name, dat, target=tgt, context=enforcement_context, blocking=True)
        _LOGGER.info("[ha_governance] ENFORCEMENT_EXECUTED")
        _update_policy_stats(hass, policy_name, "success")
        result = "success"
    except Exception as e:
        _LOGGER.error(f"[ha_governance] ENFORCEMENT_ERROR: {e}")
        _update_policy_stats(hass, policy_name, "error")
        result = "error"
    async def _cleanup_context():
        await asyncio.sleep(_CONTEXT_CLEANUP_DELAY)
        async with _COOLDOWN_LOCK:
            _ENFORCEMENT_CONTEXTS.discard(enforcement_context.id)
            _LOGGER.debug(f"[ha_governance] Context cleaned up: {enforcement_context.id[:8]}")
    hass.async_create_task(_cleanup_context())
    return result

async def setup_periodic_cleanup(hass: HomeAssistant) -> None:
    async def _cleanup_task(now):
        async with _COOLDOWN_LOCK:
            size = len(_ENFORCEMENT_CONTEXTS)
            _ENFORCEMENT_CONTEXTS.clear()
            _LOGGER.debug(f"[ha_governance] Periodic context cleanup: cleared {size} contexts")
    async_track_time_interval(hass, _cleanup_task, timedelta(minutes=5))
