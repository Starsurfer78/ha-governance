import asyncio
import logging
import os
import operator
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from homeassistant.core import HomeAssistant, State
from .const import DEFAULT_POLICY_PATH

def _split_service(s: str) -> Tuple[str, str]:
    parts = s.split(".")
    return parts[0], parts[1]

def _get_state(hass: HomeAssistant, entity_id: str) -> Optional[State]:
    return hass.states.get(entity_id)

OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}

def _parse_expected(expected: Any):
    if not isinstance(expected, str):
        return None, expected
    for symbol in sorted(OPS.keys(), key=len, reverse=True):
        if expected.startswith(symbol):
            return symbol, expected[len(symbol):]
    return None, expected

def _get_entity_value(hass: HomeAssistant, entity_path: str):
    if "." not in entity_path:
        return None
    parts = entity_path.split(".")
    entity_id = parts[0] + "." + parts[1]
    state = hass.states.get(entity_id)
    if state is None:
        return None
    if len(parts) > 2:
        attr_name = parts[2]
        return state.attributes.get(attr_name)
    return state.state

def _match_when(hass: HomeAssistant, when: Dict[str, Any]) -> bool:
    for entity_path, expected in when.items():
        value = _get_entity_value(hass, entity_path)
        if value is None:
            return False
        op_symbol, compare_value = _parse_expected(expected)
        if op_symbol:
            try:
                op_func = OPS[op_symbol]
                try:
                    value_num = float(value)
                    compare_num = float(compare_value)
                    if not op_func(value_num, compare_num):
                        return False
                except (ValueError, TypeError):
                    if not op_func(str(value), str(compare_value)):
                        return False
            except Exception:
                return False
        else:
            if str(value) != str(compare_value):
                return False
    return True

def _sort_policies(policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(policies, key=lambda p: int(p.get("priority", 0)), reverse=True)

def _load_yaml(path: str) -> Dict[str, Any]:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _compute_file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def get_policy_path(hass: HomeAssistant, path: Optional[str] = None) -> str:
    if path:
        return path
    return hass.config.path("policies.yaml")

def ensure_policy_file_exists(hass: HomeAssistant, path: Optional[str] = None) -> str:
    target = get_policy_path(hass, path)
    if not os.path.exists(target):
        default_path = os.path.join(os.path.dirname(__file__), "policies.yaml")
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as src:
                default_content = src.read()
            with open(target, "w", encoding="utf-8") as dst:
                dst.write(default_content)
            logging.getLogger(__name__).info(f"[ha_governance] Created initial policies.yaml at {target}")
    return target

async def load_policies(hass: HomeAssistant, path: Optional[str]) -> List[Dict[str, Any]]:
    _LOGGER = logging.getLogger(__name__)
    target = get_policy_path(hass, path)
    exists = await hass.async_add_executor_job(os.path.exists, target)
    if not exists:
        legacy_paths = [
            "/config/ha_governance/policies.yaml",
            "/config/custom_components/ha_governance/policies.yaml",
        ]
        for legacy_path in legacy_paths:
            if await hass.async_add_executor_job(os.path.exists, legacy_path):
                _LOGGER.warning(f"Found legacy policy file at {legacy_path}. Please move it to {target} to make it update-safe.")
                target = legacy_path
                exists = True
                break
        if not exists:
            _LOGGER.error(f"Policy file not found at {target} and no legacy file found. Governance disabled (no policies loaded).")
            return []
    try:
        data = await hass.async_add_executor_job(_load_yaml, target)
        if not isinstance(data, dict) or "policies" not in data:
            _LOGGER.error(f"Invalid policy file structure at {target}. Governance disabled (expected dict with 'policies' list).")
            return []
        items = data.get("policies", [])
        try:
            digest = await hass.async_add_executor_job(_compute_file_hash, target)
            _LOGGER.debug(f"[ha_governance] Loaded policies.yaml SHA256: {digest} from {target}")
        except Exception:
            _LOGGER.debug(f"[ha_governance] Could not compute SHA256 for policies at {target}")
        _LOGGER.info(f"Loaded {len(items)} policies from {target}")
        return _sort_policies(items)
    except Exception as e:
        _LOGGER.error(f"Error loading policies from {target}: {e}")
        return []

def evaluate(hass: HomeAssistant, policies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for p in policies:
        when = p.get("when", {})
        if not isinstance(when, dict):
            continue
        if _match_when(hass, when):
            return p
    return None
