import asyncio
import logging
import os
import operator
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Set
from homeassistant.core import HomeAssistant, State
from .const import DEFAULT_POLICY_FILENAME
_LOGGER = logging.getLogger(__name__)

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
            _LOGGER.debug(f"[ha_governance] Entity not found or unavailable: {entity_path}")
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
    return sorted(
        policies,
        key=lambda p: (-int(p.get("priority", 0)), str(p.get("name", ""))),
    )

def _extract_target_entities(target: Any) -> List[str]:
    if isinstance(target, str):
        return [target]
    if isinstance(target, dict):
        value = target.get("entity_id")
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(v) for v in value if isinstance(v, str)]
    return []

def build_entity_index(policies: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    index: Dict[str, Set[str]] = {}
    for policy in policies:
        name = str(policy.get("name", ""))
        when = policy.get("when", {})
        if isinstance(when, dict):
            for entity_path in when.keys():
                parts = str(entity_path).split(".")
                if len(parts) >= 2:
                    entity_id = parts[0] + "." + parts[1]
                    index.setdefault(entity_id, set()).add(name)
        enforce = policy.get("enforce", {})
        if isinstance(enforce, dict):
            targets = _extract_target_entities(enforce.get("target"))
            for entity_id in targets:
                parts = str(entity_id).split(".")
                if len(parts) >= 2:
                    normalized = parts[0] + "." + parts[1]
                    index.setdefault(normalized, set()).add(name)
    return index

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
    return hass.config.path(DEFAULT_POLICY_FILENAME)

def ensure_policy_file_exists(hass: HomeAssistant, path: Optional[str] = None) -> str:
    target = get_policy_path(hass, path)
    if not os.path.exists(target):
        default_path = os.path.join(os.path.dirname(__file__), "policies.yaml")
        if os.path.exists(default_path):
            with open(default_path, "r", encoding="utf-8") as src:
                default_content = src.read()
            with open(target, "w", encoding="utf-8") as dst:
                dst.write(default_content)
            _LOGGER.info(f"[ha_governance] Created initial policies.yaml at {target}")
    return target

async def load_policies(hass: HomeAssistant, path: Optional[str]) -> List[Dict[str, Any]]:
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
        combined: List[Dict[str, Any]] = []
        if not isinstance(data, dict):
            _LOGGER.error(f"Invalid policy file structure at {target}. Governance disabled (expected dict with 'policies' list).")
            return []
        base_items = data.get("policies", [])
        if isinstance(base_items, list):
            combined.extend(base_items)
        includes = data.get("includes", [])
        if isinstance(includes, list) and includes:
            base_dir = os.path.dirname(target)
            import glob as _glob
            for pattern in includes:
                try:
                    patt = str(pattern)
                    if not os.path.isabs(patt):
                        patt = os.path.join(base_dir, patt)
                    matched = await hass.async_add_executor_job(_glob.glob, patt)
                    if not matched:
                        _LOGGER.warning(f"[ha_governance] Include pattern matched no files: {pattern}")
                        continue
                    for inc_file in matched:
                        try:
                            inc_data = await hass.async_add_executor_job(_load_yaml, inc_file)
                        except Exception as e:
                            _LOGGER.warning(f"[ha_governance] Failed to load include '{inc_file}': {e}")
                            continue
                        if isinstance(inc_data, dict):
                            inc_items = inc_data.get("policies", [])
                            if isinstance(inc_items, list):
                                combined.extend(inc_items)
                            else:
                                _LOGGER.warning(f"[ha_governance] Included file '{inc_file}' missing 'policies' list")
                        elif isinstance(inc_data, list):
                            # Support files that directly contain a list of policies
                            for item in inc_data:
                                if isinstance(item, dict):
                                    combined.append(item)
                        else:
                            _LOGGER.warning(f"[ha_governance] Included file '{inc_file}' has invalid structure (ignored)")
                except Exception as e:
                    _LOGGER.warning(f"[ha_governance] Error processing include pattern '{pattern}': {e}")
        try:
            digest = await hass.async_add_executor_job(_compute_file_hash, target)
            _LOGGER.debug(f"[ha_governance] Loaded policies.yaml SHA256: {digest} from {target}")
        except Exception:
            _LOGGER.debug(f"[ha_governance] Could not compute SHA256 for policies at {target}")
        _LOGGER.info(f"Loaded {len(combined)} policies from {target}")
        return _sort_policies(combined)
    except Exception as e:
        _LOGGER.error(f"Error loading policies from {target}: {e}")
        return []

def evaluate(hass: HomeAssistant, policies: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    winner = None
    evaluations: List[Dict[str, Any]] = []
    for p in policies:
        when = p.get("when", {})
        matched = False
        if isinstance(when, dict) and _match_when(hass, when):
            matched = True
            if winner is None:
                winner = p
        evaluations.append(
            {
                "name": str(p.get("name", "")),
                "priority": int(p.get("priority", 0)),
                "matched": matched,
                "cooldown_blocked": False,
            }
        )
    return winner, evaluations
