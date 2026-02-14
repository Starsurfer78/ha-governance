"""
Hybrid House Mode Controller.
"""
import logging
from datetime import datetime, time
from .state_cache import StateCache

logger = logging.getLogger(__name__)

class ModeController:
    MODE_AUTO = "AUTO"
    MODE_HOME = "HOME"
    MODE_AWAY = "AWAY"
    MODE_NIGHT = "NIGHT"

    ENTITY_OVERRIDE = "input_select.house_mode_override"
    
    def __init__(self, state_cache: StateCache):
        self.state_cache = state_cache

    async def get_effective_mode(self) -> str:
        """
        Calculate effective house mode based on override and derived mode.
        """
        # Get override state
        override_state = await self.state_cache.get_state(self.ENTITY_OVERRIDE)
        override = override_state.get("state") if override_state else self.MODE_AUTO
        
        if override and override != self.MODE_AUTO:
            return override
            
        return await self._calculate_derived_mode()

    async def _calculate_derived_mode(self) -> str:
        """
        Calculate derived mode based on time and presence.
        Deterministic logic:
        1. Night (23:00 - 06:00)
        2. Away (No person home - simplified check)
        3. Home (Default)
        """
        now = datetime.now().time()
        
        # 1. Night Check
        if self._is_time_between(time(23, 0), time(6, 0), now):
            return self.MODE_NIGHT
            
        # 2. Presence Check (Simplified: Check if any person is home)
        # In a real scenario, we'd check specific person entities or a group
        # For v0.1 we'll look for any entity starting with person. that is 'home'
        all_states = await self.state_cache.get_all_states()
        anyone_home = False
        for entity_id, state_data in all_states.items():
            if entity_id.startswith("person."):
                if state_data.get("state") == "home":
                    anyone_home = True
                    break
        
        if not anyone_home and self._has_person_entities(all_states):
             return self.MODE_AWAY
             
        # 3. Default
        return self.MODE_HOME

    def _is_time_between(self, begin_time, end_time, check_time=None):
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time

    def _has_person_entities(self, all_states):
        for entity_id in all_states:
            if entity_id.startswith("person."):
                return True
        return False
