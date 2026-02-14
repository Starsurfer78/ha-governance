"""
Declarative Policy Engine.
"""
import logging
import yaml
import os
from typing import List, Dict, Optional, Tuple, Any
from state_cache import StateCache

logger = logging.getLogger(__name__)

class PolicyEngine:
    def __init__(self, state_cache: StateCache, policies_path: str = "policies.yaml"):
        self.state_cache = state_cache
        self.policies_path = policies_path
        self.policies = []
        self.load_policies()

    def load_policies(self):
        """Load policies from YAML file."""
        if not os.path.exists(self.policies_path):
            logger.warning(f"Policies file not found at {self.policies_path}")
            return

        try:
            with open(self.policies_path, 'r') as f:
                data = yaml.safe_load(f)
                
            raw_policies = data.get('policies', [])
            # Sort by priority descending
            self.policies = sorted(raw_policies, key=lambda x: x.get('priority', 0), reverse=True)
            
            # Limit to 5 policies as per v0.1 scope
            if len(self.policies) > 5:
                logger.warning("More than 5 policies defined. Truncating to top 5.")
                self.policies = self.policies[:5]
                
            logger.info(f"Loaded {len(self.policies)} policies.")
            
        except Exception as e:
            logger.error(f"Error loading policies: {e}")

    async def evaluate(self) -> Optional[Tuple[Dict, str]]:
        """
        Evaluate all policies against current state.
        Returns the enforcement action (dict) and policy name (str) of the first matching policy.
        Returns None if no policy matches.
        """
        for policy in self.policies:
            if await self._check_policy(policy):
                return policy.get('enforce'), policy.get('name')
        return None

    async def _check_policy(self, policy: Dict) -> bool:
        """Check if a policy's conditions are met."""
        conditions = policy.get('when', {})
        
        for entity_id, expected_value in conditions.items():
            current_state_obj = await self.state_cache.get_state(entity_id)
            if not current_state_obj:
                # If entity state is missing, condition fails (fail-safe)
                return False
                
            current_state = current_state_obj.get('state')
            
            if not self._match_state(current_state, expected_value):
                return False
                
        return True

    def _match_state(self, current: str, expected: Any) -> bool:
        """
        Match current state against expected value.
        Handles boolean mapping for HA states.
        """
        if isinstance(expected, bool):
            if expected: # True
                return current in ('on', 'home', 'open', 'active')
            else: # False
                return current in ('off', 'not_home', 'closed', 'inactive')
        
        # String comparison
        return str(current) == str(expected)
