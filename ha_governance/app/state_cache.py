"""
In-Memory State Cache.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StateCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def update_entity(self, entity_id: str, state: Dict[str, Any]):
        """
        Update the state of an entity in the cache.
        Adds a local timestamp 'cached_at'.
        """
        async with self._lock:
            # We store the full state object from HA, plus our own metadata
            state['cached_at'] = datetime.now().isoformat()
            self._cache[entity_id] = state
            logger.debug(f"Updated cache for {entity_id}: {state.get('state')}")

    async def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the state of an entity from the cache.
        Returns None if entity is not found.
        """
        async with self._lock:
            return self._cache.get(entity_id)

    async def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Return a copy of all cached states.
        """
        async with self._lock:
            return self._cache.copy()

    async def remove_entity(self, entity_id: str):
        """
        Remove an entity from the cache.
        """
        async with self._lock:
            if entity_id in self._cache:
                del self._cache[entity_id]
                logger.debug(f"Removed {entity_id} from cache")

    async def clear(self):
        """
        Clear the entire cache.
        """
        async with self._lock:
            self._cache.clear()
            logger.info("State cache cleared")
