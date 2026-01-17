"""
CITYARRAY Festival Edition - WebSocket Manager
Handles real-time connections between backend, dashboards, and signs
"""

from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Two types of clients:
    - Dashboards: Operator interfaces that receive all updates
    - Signs: Individual sign units that receive messages and send status
    """
    
    def __init__(self):
        # Dashboard connections (broadcast receivers)
        self.dashboard_connections: List[WebSocket] = []
        
        # Sign connections (keyed by sign_id)
        self.sign_connections: Dict[str, WebSocket] = {}
        
        # Connection metadata
        self.connection_info: Dict[WebSocket, dict] = {}
    
    @property
    def dashboard_count(self) -> int:
        return len(self.dashboard_connections)
    
    @property
    def sign_count(self) -> int:
        return len(self.sign_connections)
    
    async def connect(
        self,
        websocket: WebSocket,
        client_type: str,
        client_id: Optional[str] = None
    ):
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_type: "dashboard" or "sign"
            client_id: For signs, the sign_id
        """
        await websocket.accept()
        
        # Store connection metadata
        self.connection_info[websocket] = {
            "type": client_type,
            "id": client_id,
            "connected_at": datetime.utcnow().isoformat()
        }
        
        if client_type == "dashboard":
            self.dashboard_connections.append(websocket)
            print(f"✅ Dashboard connected. Total dashboards: {self.dashboard_count}")
            
            # Send welcome message with current status
            await websocket.send_json({
                "type": "connected",
                "message": "Connected to CITYARRAY backend",
                "dashboard_count": self.dashboard_count,
                "sign_count": self.sign_count
            })
            
        elif client_type == "sign" and client_id:
            # If sign was already connected, close old connection
            if client_id in self.sign_connections:
                try:
                    old_ws = self.sign_connections[client_id]
                    await old_ws.close()
                except:
                    pass
            
            self.sign_connections[client_id] = websocket
            print(f"✅ Sign {client_id} connected. Total signs: {self.sign_count}")
            
            # Notify dashboards of new sign connection
            await self.broadcast_to_dashboards({
                "type": "sign_connected",
                "sign_id": client_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send welcome message to sign
            await websocket.send_json({
                "type": "connected",
                "message": f"Sign {client_id} connected to backend"
            })
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        info = self.connection_info.get(websocket, {})
        client_type = info.get("type")
        client_id = info.get("id")
        
        if client_type == "dashboard":
            if websocket in self.dashboard_connections:
                self.dashboard_connections.remove(websocket)
            print(f"👋 Dashboard disconnected. Total dashboards: {self.dashboard_count}")
            
        elif client_type == "sign" and client_id:
            if client_id in self.sign_connections:
                del self.sign_connections[client_id]
            print(f"👋 Sign {client_id} disconnected. Total signs: {self.sign_count}")
        
        # Clean up metadata
        if websocket in self.connection_info:
            del self.connection_info[websocket]
    
    async def broadcast_to_dashboards(self, message: dict):
        """
        Send a message to all connected dashboards.
        
        Args:
            message: Dict to send as JSON
        """
        if not self.dashboard_connections:
            return
        
        disconnected = []
        
        for websocket in self.dashboard_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to dashboard: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast_to_signs(self, message: dict):
        """
        Send a message to all connected signs.
        
        Args:
            message: Dict to send as JSON
        """
        if not self.sign_connections:
            return
        
        disconnected = []
        
        for sign_id, websocket in self.sign_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to sign {sign_id}: {e}")
                disconnected.append(sign_id)
        
        # Clean up disconnected signs
        for sign_id in disconnected:
            if sign_id in self.sign_connections:
                ws = self.sign_connections[sign_id]
                self.disconnect(ws)
    
    async def send_to_sign(self, sign_id: str, message: dict) -> bool:
        """
        Send a message to a specific sign.
        
        Args:
            sign_id: The target sign ID
            message: Dict to send as JSON
            
        Returns:
            True if sent successfully, False if sign not connected
        """
        if sign_id not in self.sign_connections:
            print(f"⚠️ Sign {sign_id} not connected")
            return False
        
        try:
            websocket = self.sign_connections[sign_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            print(f"❌ Error sending to sign {sign_id}: {e}")
            # Clean up disconnected sign
            self.disconnect(self.sign_connections.get(sign_id))
            return False
    
    async def send_to_signs(self, sign_ids: List[str], message: dict) -> Dict[str, bool]:
        """
        Send a message to multiple specific signs.
        
        Args:
            sign_ids: List of target sign IDs
            message: Dict to send as JSON
            
        Returns:
            Dict mapping sign_id to success/failure
        """
        results = {}
        for sign_id in sign_ids:
            results[sign_id] = await self.send_to_sign(sign_id, message)
        return results
    
    async def send_to_zones(self, zone_ids: List[str], message: dict, db) -> Dict[str, bool]:
        """
        Send a message to all signs in specified zones.
        
        Args:
            zone_ids: List of zone IDs
            message: Dict to send as JSON
            db: Database session
            
        Returns:
            Dict mapping sign_id to success/failure
        """
        from models import Sign
        
        # Get all signs in the specified zones
        signs = db.query(Sign).filter(Sign.zone_id.in_(zone_ids)).all()
        sign_ids = [s.id for s in signs]
        
        return await self.send_to_signs(sign_ids, message)
    
    def get_connected_sign_ids(self) -> List[str]:
        """Get list of currently connected sign IDs"""
        return list(self.sign_connections.keys())
    
    def is_sign_connected(self, sign_id: str) -> bool:
        """Check if a specific sign is connected"""
        return sign_id in self.sign_connections
    
    async def ping_sign(self, sign_id: str) -> bool:
        """
        Send a ping to check if sign is responsive.
        
        Returns:
            True if sign responds, False otherwise
        """
        return await self.send_to_sign(sign_id, {"type": "ping"})
    
    async def request_sign_status(self, sign_id: str) -> bool:
        """Request immediate status update from a sign"""
        return await self.send_to_sign(sign_id, {"type": "request_status"})
    
    def get_connection_stats(self) -> dict:
        """Get statistics about current connections"""
        return {
            "dashboards": {
                "count": self.dashboard_count,
                "connections": [
                    self.connection_info.get(ws, {})
                    for ws in self.dashboard_connections
                ]
            },
            "signs": {
                "count": self.sign_count,
                "connected_ids": list(self.sign_connections.keys()),
                "connections": {
                    sign_id: self.connection_info.get(ws, {})
                    for sign_id, ws in self.sign_connections.items()
                }
            }
        }


# Background task to monitor connections and detect offline signs
async def monitor_connections(manager: ConnectionManager, db_session_factory, timeout_seconds: int = 30):
    """
    Background task to monitor sign connections and mark offline signs.
    
    Args:
        manager: The ConnectionManager instance
        db_session_factory: Function to create database sessions
        timeout_seconds: How long before marking a sign as offline
    """
    from models import Sign
    from datetime import datetime, timedelta
    
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        
        try:
            db = db_session_factory()
            
            # Find signs that haven't been seen recently
            threshold = datetime.utcnow() - timedelta(seconds=timeout_seconds)
            
            stale_signs = db.query(Sign).filter(
                Sign.status == "online",
                Sign.last_seen < threshold
            ).all()
            
            for sign in stale_signs:
                sign.status = "offline"
                
                # Notify dashboards
                await manager.broadcast_to_dashboards({
                    "type": "sign_offline",
                    "sign_id": sign.id,
                    "last_seen": sign.last_seen.isoformat() if sign.last_seen else None,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                print(f"⚠️ Sign {sign.id} marked offline (last seen: {sign.last_seen})")
            
            if stale_signs:
                db.commit()
            
            db.close()
            
        except Exception as e:
            print(f"❌ Connection monitor error: {e}")
