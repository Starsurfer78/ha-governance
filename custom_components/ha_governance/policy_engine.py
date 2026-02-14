import asyncio
from typing import Any, Dict, List, Optional, Tuple
from homeassistant.core import HomeAssistant, State
from .const import DEFAULT_POLICY_PATH

def _split_service(s: str) -> Tuple[str, str]:
    parts = s.split(".")
    return parts[0], parts[1]

def _get_state(hass: HomeAssistant, entity_id: str) -> Optional[State]:
    return hass.states.get(entity_id)

def _match_when(hass: HomeAssistant, when: Dict[str, Any]) -> bool:
    for entity_id, expected in when.items():
        st = _get_state(hass, entity_id)
        if st is None:
            return False
        if st.state != str(expected):
            return False
    return True

def _sort_policies(policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(policies, key=lambda p: int(p.get("priority", 0)), reverse=True)

def _load_yaml(path: str) -> Dict[str, Any]:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

async def load_policies(hass: HomeAssistant, path: Optional[str]) -> List[Dict[str, Any]]:
    target = path or DEFAULT_POLICY_PATH
    data = await hass.async_add_executor_job(_load_yaml, target)
    items = data.get("policies", []) if isinstance(data, dict) else []
    return _sort_policies(items)

def evaluate(hass: HomeAssistant, policies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for p in policies:
        when = p.get("when", {})
        if not isinstance(when, dict):
            continue
        if _match_when(hass, when):
            return p
    return None
