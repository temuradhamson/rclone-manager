import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WSManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        logger.info(f"WebSocket connected, total: {len(self.connections)}")

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)
        logger.info(f"WebSocket disconnected, total: {len(self.connections)}")

    async def broadcast(self, message: dict):
        data = json.dumps(message, default=str)
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections.remove(ws)


ws_manager = WSManager()
