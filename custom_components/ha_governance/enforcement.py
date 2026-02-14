from time import monotonic
from typing import Any, Dict, Tuple, Optional, Set
import asyncio
import logging
from homeassistant.core import HomeAssistant, Context
from .const import CONF_COOLDOWN_SECONDS

def _split_service(s: str) -> Tuple[str, str]:
    parts = s.split(".")
    return parts[0], parts[1]

def _now() -> float:
    return monotonic()

def _cooldown_ok(hass: HomeAssistant, policy: Dict[str, Any], cooldown_seconds: int) -> bool:
    key = policy.get("name", "")
    store = hass.data.setdefault("ha_governance", {})
    cd = store.setdefault("cooldown", {})
    last = cd.get(key, 0.0)
    if _now() - float(last) < float(cooldown_seconds):
        return False
    cd[key] = _now()
    return True

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

async def apply(hass: HomeAssistant, policy: Dict[str, Any], options: Dict[str, Any], trigger_context: Optional[Context] = None) -> None:
    cooldown = int(options.get(CONF_COOLDOWN_SECONDS, 10))
    async with _COOLDOWN_LOCK:
        if not _cooldown_ok(hass, policy, cooldown):
            _LOGGER.info("[ha_governance] LOOP_PREVENTED")
            return
    enforce = policy.get("enforce", {})
    svc = enforce.get("service", "")
    tgt = enforce.get("target", {})
    dat = enforce.get("data", {})
    if not svc:
        return
    domain, name = _split_service(svc)
    enforcement_context = Context(parent_id=getattr(trigger_context, "id", None)) if trigger_context else Context()
    async with _COOLDOWN_LOCK:
        _ENFORCEMENT_CONTEXTS.add(enforcement_context.id)
    _LOGGER.info("[ha_governance] POLICY_TRIGGERED")
    try:
        await hass.services.async_call(domain, name, dat, target=tgt, context=enforcement_context, blocking=True)
        _LOGGER.info("[ha_governance] ENFORCEMENT_EXECUTED")
    except Exception as e:
        _LOGGER.error(f"[ha_governance] ENFORCEMENT_ERROR: {e}")
    async def _cleanup_context():
        await asyncio.sleep(_CONTEXT_CLEANUP_DELAY)
        async with _COOLDOWN_LOCK:
            _ENFORCEMENT_CONTEXTS.discard(enforcement_context.id)
            _LOGGER.debug(f"[ha_governance] Context cleaned up: {enforcement_context.id[:8]}")
    hass.async_create_task(_cleanup_context())

async def setup_periodic_cleanup(hass: HomeAssistant) -> None:
    async def _cleanup_task():
        while True:
            await asyncio.sleep(3600)
            async with _COOLDOWN_LOCK:
                size = len(_ENFORCEMENT_CONTEXTS)
                _ENFORCEMENT_CONTEXTS.clear()
                _LOGGER.debug(f"[ha_governance] Periodic context cleanup: cleared {size} contexts")
    hass.async_create_task(_cleanup_task())
