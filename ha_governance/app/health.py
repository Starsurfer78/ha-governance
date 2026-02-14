"""
Health Endpoint.
"""
from aiohttp import web
import logging
import time

logger = logging.getLogger(__name__)

class HealthServer:
    def __init__(self, ha_client):
        self.ha_client = ha_client
        self.start_time = time.time()
        self.runner = None
        self.site = None

    async def health_handler(self, request):
        uptime = int(time.time() - self.start_time)
        ws_connected = False
        if self.ha_client and self.ha_client._ws and not self.ha_client._ws.closed:
            ws_connected = True
            
        return web.json_response({
            "status": "ok",
            "websocket_connected": ws_connected,
            "uptime_seconds": uptime
        })

    async def start(self):
        app = web.Application()
        app.router.add_get('/health', self.health_handler)
        
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        
        # In Add-ons, usually expose on a port. Let's use 8000 or similar.
        # PRD doesn't specify port, but usually 8099 or so.
        # I'll use 8099.
        self.site = web.TCPSite(self.runner, '0.0.0.0', 8099)
        await self.site.start()
        logger.info("Health server started on port 8099")

    async def stop(self):
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
