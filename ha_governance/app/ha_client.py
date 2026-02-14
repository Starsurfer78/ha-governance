"""
Home Assistant WebSocket Client.
"""
import aiohttp
import asyncio
import logging
import json
import os
from typing import Optional, Callable, Awaitable

logger = logging.getLogger(__name__)

class HAClient:
    def __init__(self, 
                 url: str, 
                 token: str, 
                 state_cache, 
                 on_event: Optional[Callable[[dict], Awaitable[None]]] = None):
        self.url = url
        self.token = token
        self.state_cache = state_cache
        self.on_event = on_event
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._running = False
        self._message_id = 1
        self._pending_requests = {}
        # Reconnect logic
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0

    async def start(self):
        """Start the WebSocket connection loop."""
        self._running = True
        self._session = aiohttp.ClientSession()
        
        while self._running:
            try:
                await self._connect()
                # If connect returns successfully (e.g. clean close), reset delay
                self._reconnect_delay = 1.0
            except Exception as e:
                logger.error(f"Connection error: {e}")
                if self._running:
                    logger.info(f"Reconnecting in {self._reconnect_delay:.1f} seconds...")
                    await asyncio.sleep(self._reconnect_delay)
                    # Exponential Backoff with Jitter (optional, simple doubling here)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
            
            if self._running and (not self._ws or self._ws.closed):
                continue

    async def stop(self):
        """Stop the WebSocket connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        logger.info("HA Client stopped")

    async def _connect(self):
        """Connect to Home Assistant WebSocket API."""
        logger.info(f"Connecting to {self.url}...")
        async with self._session.ws_connect(self.url) as ws:
            self._ws = ws
            logger.info("WebSocket connected")
            
            # Reset backoff on successful connection
            self._reconnect_delay = 1.0
            
            # Authentication Phase
            auth_msg = await ws.receive_json()
            if auth_msg.get("type") != "auth_required":
                logger.error(f"Unexpected message during auth: {auth_msg}")
                return

            await ws.send_json({
                "type": "auth",
                "access_token": self.token
            })

            auth_response = await ws.receive_json()
            if auth_response.get("type") != "auth_ok":
                logger.error(f"Authentication failed: {auth_response}")
                return
            
            logger.info("Authentication successful")
            
            # Initial State Sync
            await self._fetch_initial_states()
            
            # Subscribe to events
            await self._subscribe_events()

            # Message Loop
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_message(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break

    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "event":
            event = data.get("event", {})
            event_type = event.get("event_type")
            
            if event_type == "state_changed":
                new_state = event.get("data", {}).get("new_state")
                entity_id = event.get("data", {}).get("entity_id")
                
                if new_state and entity_id:
                    # Update Cache
                    await self.state_cache.update_entity(entity_id, new_state)
                    
                    # Notify listener (Policy Engine triggers here)
                    if self.on_event:
                        await self.on_event(event)
                        
        elif msg_type == "result":
            req_id = data.get("id")
            if req_id in self._pending_requests:
                future = self._pending_requests.pop(req_id)
                if data.get("success"):
                    future.set_result(data.get("result"))
                else:
                    future.set_exception(Exception(data.get("error")))

    async def _fetch_initial_states(self):
        """Fetch all states initially."""
        logger.info("Fetching initial states...")
        states = await self.call_api("get_states")
        if states:
            for state in states:
                entity_id = state.get("entity_id")
                if entity_id:
                    await self.state_cache.update_entity(entity_id, state)
            logger.info(f"Initial sync complete. Loaded {len(states)} entities.")

    async def _subscribe_events(self):
        """Subscribe to state_changed events."""
        logger.info("Subscribing to state_changed events...")
        await self.call_api("subscribe_events", event_type="state_changed")

    async def call_api(self, command: str, **kwargs):
        """Send a command to the WebSocket API."""
        if not self._ws or self._ws.closed:
            raise ConnectionError("WebSocket is not connected")
            
        req_id = self._message_id
        self._message_id += 1
        
        msg = {"id": req_id, "type": command}
        msg.update(kwargs)
        
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = future
        
        await self._ws.send_json(msg)
        return await future

    async def call_service(self, domain: str, service: str, service_data: dict, target: dict = None):
        """Call a service in Home Assistant."""
        data = {
            "domain": domain,
            "service": service,
            "service_data": service_data
        }
        if target:
            data["target"] = target
            
        logger.info(f"Calling service {domain}.{service} with {service_data}")
        return await self.call_api("call_service", **data)
