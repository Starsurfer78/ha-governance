"""
Post-Action Enforcement.
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Enforcement:
    def __init__(self, ha_client, state_cache, mode_controller):
        self.ha_client = ha_client
        self.state_cache = state_cache
        self.mode_controller = mode_controller
        # Loop Protection: Stores last enforcement timestamp for each entity
        # Key: entity_id, Value: timestamp (float)
        self._recently_enforced: Dict[str, float] = {}
        self._cooldown_seconds = 5.0

    async def execute(self, policy_name: str, action: Dict[str, Any]):
        """
        Execute an enforcement action.
        """
        service_full = action.get("service", "")
        if "." not in service_full:
            logger.error(f"Invalid service format: {service_full}")
            return

        domain, service = service_full.split(".", 1)
        target = action.get("target")
        data = action.get("data", {})
        
        # Determine entity_id for logging and loop protection
        entity_id = target
        if isinstance(target, dict):
            entity_id = target.get("entity_id")
        
        # Loop Protection Check
        if entity_id:
            now = time.time()
            last_enforced = self._recently_enforced.get(entity_id, 0)
            if now - last_enforced < self._cooldown_seconds:
                logger.warning(f"Loop protection: Skipping enforcement for {entity_id} (Policy: {policy_name}). Last enforced {now - last_enforced:.1f}s ago.")
                return
            
            # Update timestamp
            self._recently_enforced[entity_id] = now
            # Lazy cleanup: We don't actively clean up the dict, 
            # but it only grows by number of entities, which is small in v0.1 scope.

        # Get previous state for logging
        previous_state = "unknown"
        if entity_id:
            state_obj = await self.state_cache.get_state(entity_id)
            if state_obj:
                previous_state = state_obj.get("state")

        # Get effective mode for logging
        effective_mode = await self.mode_controller.get_effective_mode()

        # Execute Service Call
        try:
            # We assume HA Client handles the actual call
            await self.ha_client.call_service(domain, service, data, target={"entity_id": entity_id} if isinstance(target, str) else target)
            
            # Structured Log
            log_payload = {
                "event_type": "policy_enforcement",
                "policy": policy_name,
                "entity_id": entity_id,
                "previous_state": previous_state,
                "new_state": str(data), # Simplified, as new state is result of action
                "effective_mode": effective_mode,
                "origin": "governor"
            }
            
            logger.info("Policy Enforcement Triggered", extra={"structured_data": log_payload})
            
        except Exception as e:
            logger.error(f"Enforcement failed for policy {policy_name}: {e}")
