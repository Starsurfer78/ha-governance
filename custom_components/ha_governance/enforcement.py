from time import monotonic
from typing import Any, Dict, Tuple
from homeassistant.core import HomeAssistant
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

async def apply(hass: HomeAssistant, policy: Dict[str, Any], options: Dict[str, Any]) -> None:
    cooldown = int(options.get(CONF_COOLDOWN_SECONDS, 10))
    if not _cooldown_ok(hass, policy, cooldown):
        hass.logger.info("[ha_governance] LOOP_PREVENTED")
        return
    enforce = policy.get("enforce", {})
    svc = enforce.get("service", "")
    tgt = enforce.get("target", {})
    dat = enforce.get("data", {})
    if not svc:
        return
    domain, name = _split_service(svc)
    hass.logger.info("[ha_governance] POLICY_TRIGGERED")
    await hass.services.async_call(domain, name, dat, target=tgt)
    hass.logger.info("[ha_governance] ENFORCEMENT_EXECUTED")
