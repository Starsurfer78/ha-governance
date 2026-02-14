"""
Main entry point for HA Governance Add-on.
"""
import asyncio
import logging
import os
import signal
from logging_config import setup_logging
from state_cache import StateCache
from ha_client import HAClient
from mode_controller import ModeController
from policy_engine import PolicyEngine
from enforcement import Enforcement
from health import HealthServer

logger = setup_logging()

# Configuration
HA_WS_URL = os.environ.get("HA_WS_URL", "ws://supervisor/core/websocket")
HA_TOKEN = os.environ.get("SUPERVISOR_TOKEN", os.environ.get("HASSIO_TOKEN", ""))

async def main():
    logger.info("Starting HA Governance Add-on v0.1")
    
    if not HA_TOKEN:
        logger.warning("No SUPERVISOR_TOKEN found. Authentication might fail.")

    # 1. Initialize State Cache
    state_cache = StateCache()
    
    # 2. Initialize Logic Components
    mode_controller = ModeController(state_cache)
    policy_engine = PolicyEngine(state_cache, policies_path="/data/policies.yaml" if os.path.exists("/data/policies.yaml") else "policies.yaml")
    
    # 3. Initialize HA Client (Placeholder for on_event)
    ha_client = HAClient(HA_WS_URL, HA_TOKEN, state_cache)
    
    # 4. Initialize Enforcement
    enforcement = Enforcement(ha_client, state_cache, mode_controller)
    
    # 5. Define Event Processing Logic
    async def process_event(event):
        # Loop Protection: Check if event was caused by us (origin=governor)
        # Since we can't easily check origin field in all events, we rely on logic.
        # But if we did tag it in context, we would check it here.
        # For v0.1, we proceed to evaluate.
        
        # Evaluate Policies
        result = await policy_engine.evaluate()
        if result:
            action, policy_name = result
            logger.info(f"Policy '{policy_name}' matched. Enforcing...")
            await enforcement.execute(policy_name, action)

    # 6. Link Event Processor
    ha_client.on_event = process_event
    
    # 7. Initialize Health Server
    health_server = HealthServer(ha_client)
    
    # 8. Start Services
    await health_server.start()
    
    # Run HA Client (Blocking loop)
    # We run it as a task so we can handle shutdown
    client_task = asyncio.create_task(ha_client.start())
    
    # Graceful Shutdown Handling
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    
    def handle_signal():
        logger.info("Received shutdown signal")
        stop_event.set()

    # Register signals
    # Note: Windows doesn't support add_signal_handler for SIGTERM same way as Unix
    # We use simple try-except or check OS
    if os.name != 'nt':
        loop.add_signal_handler(signal.SIGTERM, handle_signal)
        loop.add_signal_handler(signal.SIGINT, handle_signal)
    
    try:
        # On Windows, we might need a loop to check for stop_event or use simple sleep
        # But since client_task is running, we wait for stop_event
        if os.name == 'nt':
            # Simple loop for Windows dev environment
            while not stop_event.is_set():
                await asyncio.sleep(1)
        else:
            await stop_event.wait()
            
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    finally:
        logger.info("Shutting down...")
        await health_server.stop()
        await ha_client.stop()
        await client_task
        logger.info("Shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
