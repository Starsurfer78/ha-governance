"""
Home Assistant WebSocket Client.
"""
import aiohttp
import asyncio
import logging
import json
import os
import sys
from typing import Optional, Callable, Awaitable

logger = logging.getLogger(__name__)

class AuthError(Exception):
    """Raised when authentication fails."""
    pass

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
        # Syncing state
        self._syncing = False
        self._event_queue = []

    async def start(self):
        """Start the WebSocket connection loop."""
        self._running = True
        self._session = aiohttp.ClientSession()
        
        while self._running:
            try:
                # 1. Connect and Authenticate
                await self._connect_and_auth()
                
                # 2. Start Message Reader Task
                read_task = asyncio.create_task(self._read_loop())
                
                # 3. Subscribe to Events (Queue events during sync)
                self._syncing = True
                await self._subscribe_events()
                
                # 4. Fetch Initial States
                await self._fetch_initial_states()
                
                # 5. Process Queued Events and Enable Real-time
                logger.info(f"Processing {len(self._event_queue)} queued events...")
                for event in self._event_queue:
                    await self._handle_event(event)
                self._event_queue = []
                self._syncing = False
                
                # 6. Wait for Reader Task (runs until connection lost)
                await read_task
                
                # Reset delay on clean exit (unlikely here)
                self._reconnect_delay = 1.0

            except AuthError as e:
                logger.critical(f"Fatal Authentication Error: {e}")
                sys.exit(1)  # Fail fast
            except Exception as e:
                logger.error(f"Connection error: {e}")
                if self._running:
                    logger.info(f"Reconnecting in {self._reconnect_delay:.1f} seconds...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
            
            # Clean up before reconnecting
            if self._ws and not self._ws.closed:
                await self._ws.close()

    async def stop(self):
        """Stop the WebSocket connection."""
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        logger.info("HA Client stopped")

    async def _connect_and_auth(self):
        """Connect to Home Assistant and Authenticate."""
        logger.info(f"Connecting to {self.url}...")
        self._ws = await self._session.ws_connect(self.url)
        logger.info("WebSocket connected")
        
        # Reset backoff on successful connection
        self._reconnect_delay = 1.0
        
        # Authentication Phase
        auth_msg = await self._ws.receive_json()
        if auth_msg.get("type") != "auth_required":
            logger.error(f"Unexpected message during auth: {auth_msg}")
            raise AuthError("Unexpected message during auth")

        await self._ws.send_json({
            "type": "auth",
            "access_token": self.token
        })

        auth_response = await self._ws.receive_json()
        if auth_response.get("type") != "auth_ok":
            logger.error(f"Authentication failed: {auth_response}")
            raise AuthError(f"Authentication failed: {auth_response}")
        
        logger.info("Authentication successful")

    async def _read_loop(self):
        """Read messages from WebSocket."""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_message(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON received: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self._ws.exception()}")
                    break
        except Exception as e:
            logger.error(f"Read loop error: {e}")
            raise

    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "event":
            event = data.get("event", {})
            event_type = event.get("event_type")
            
            if event_type == "state_changed":
                if self._syncing:
                    self._event_queue.append(event)
                else:
                    await self._handle_event(event)
                        
        elif msg_type == "result":
            req_id = data.get("id")
            if req_id in self._pending_requests:
                future = self._pending_requests.pop(req_id)
                if data.get("success"):
                    future.set_result(data.get("result"))
                else:
                    future.set_exception(Exception(data.get("error")))

    async def _handle_event(self, event: dict):
        """Process a single event (Update Cache -> Notify Listener)."""
        new_state = event.get("data", {}).get("new_state")
        entity_id = event.get("data", {}).get("entity_id")
        
        if new_state and entity_id:
            # Update Cache
            await self.state_cache.update_entity(entity_id, new_state)
            
            # Notify listener (Policy Engine triggers here)
            if self.on_event:
                await self.on_event(event)

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
