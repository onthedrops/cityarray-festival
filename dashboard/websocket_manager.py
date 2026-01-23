"""
CITYARRAY Festival Edition - WebSocket Manager
"""

from fastapi import WebSocket
from typing import Dict, List, Optional
import json

class ConnectionManager:
    def __init__(self):
        self.dashboard_connections: List[WebSocket] = []
        self.sign_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_type: str, client_id: Optional[str] = None):
        await websocket.accept()
        if client_type == "dashboard":
            self.dashboard_connections.append(websocket)
        elif client_type == "sign" and client_id:
            self.sign_connections[client_id] = websocket
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.dashboard_connections:
            self.dashboard_connections.remove(websocket)
        for sign_id, ws in list(self.sign_connections.items()):
            if ws == websocket:
                del self.sign_connections[sign_id]
                break
    
    async def broadcast_to_dashboards(self, message: dict):
        for connection in self.dashboard_connections:
            try:
                await connection.send_json(message)
            except:
                pass
    
    async def broadcast_to_signs(self, message: dict):
        for sign_id, connection in self.sign_connections.items():
            try:
                await connection.send_json(message)
            except:
                pass
    
    async def send_to_sign(self, sign_id: str, message: dict):
        if sign_id in self.sign_connections:
            try:
                await self.sign_connections[sign_id].send_json(message)
            except:
                pass
    
    @property
    def dashboard_count(self) -> int:
        return len(self.dashboard_connections)
    
    @property
    def sign_count(self) -> int:
        return len(self.sign_connections)
