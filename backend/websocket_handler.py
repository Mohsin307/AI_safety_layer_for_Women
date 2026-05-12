"""
WebSocket handlers for real-time communication
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set, Optional
import json
import asyncio
import logging
from datetime import datetime

from .database import get_db, User
from .api.auth import decode_token

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        # User ID -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Emergency ID -> Set of watching user IDs
        self.emergency_watchers: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register new connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {self._total_connections()}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from emergency watchers
        for watchers in self.emergency_watchers.values():
            watchers.discard(user_id)
        
        logger.info(f"User {user_id} disconnected. Total connections: {self._total_connections()}")
    
    async def send_personal(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {user_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)
    
    async def send_to_contacts(self, contact_ids: list, message: dict):
        """Send message to multiple users"""
        for contact_id in contact_ids:
            await self.send_personal(contact_id, message)
    
    async def broadcast_emergency(self, emergency_id: str, message: dict):
        """Broadcast emergency update to watchers"""
        if emergency_id in self.emergency_watchers:
            for user_id in self.emergency_watchers[emergency_id]:
                await self.send_personal(user_id, message)
    
    def add_emergency_watcher(self, emergency_id: str, user_id: str):
        """Add user as emergency watcher"""
        if emergency_id not in self.emergency_watchers:
            self.emergency_watchers[emergency_id] = set()
        self.emergency_watchers[emergency_id].add(user_id)
    
    def remove_emergency_watcher(self, emergency_id: str, user_id: str):
        """Remove user from emergency watchers"""
        if emergency_id in self.emergency_watchers:
            self.emergency_watchers[emergency_id].discard(user_id)
    
    def _total_connections(self) -> int:
        """Get total number of connections"""
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


async def authenticate_websocket(
    websocket: WebSocket,
    token: Optional[str] = None
) -> Optional[str]:
    """Authenticate WebSocket connection"""
    if not token:
        # Try to get token from query params
        token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return None
    
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return None
        return payload.get("sub")
    except Exception as e:
        await websocket.close(code=4001, reason="Invalid token")
        return None


async def handle_websocket_message(
    websocket: WebSocket,
    user_id: str,
    message: dict
):
    """Handle incoming WebSocket messages"""
    msg_type = message.get("type")
    data = message.get("data", {})
    
    if msg_type == "ping":
        await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
    
    elif msg_type == "location_update":
        # Broadcast location to emergency watchers if any active emergency
        # This would integrate with the emergency system
        pass
    
    elif msg_type == "watch_emergency":
        emergency_id = data.get("emergency_id")
        if emergency_id:
            manager.add_emergency_watcher(emergency_id, user_id)
            await websocket.send_json({
                "type": "watching",
                "emergency_id": emergency_id
            })
    
    elif msg_type == "unwatch_emergency":
        emergency_id = data.get("emergency_id")
        if emergency_id:
            manager.remove_emergency_watcher(emergency_id, user_id)
    
    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        })


async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint handler"""
    user_id = await authenticate_websocket(websocket)
    if not user_id:
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, user_id, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


# Utility functions for other modules to send real-time updates
async def notify_emergency_triggered(
    user_id: str,
    emergency_id: str,
    emergency_type: str,
    risk_level: int,
    location: Optional[dict] = None
):
    """Notify about new emergency"""
    message = {
        "type": "emergency_triggered",
        "data": {
            "emergency_id": emergency_id,
            "emergency_type": emergency_type,
            "risk_level": risk_level,
            "location": location,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.send_personal(user_id, message)


async def notify_emergency_update(
    emergency_id: str,
    status: str,
    location: Optional[dict] = None
):
    """Notify watchers about emergency update"""
    message = {
        "type": "emergency_update",
        "data": {
            "emergency_id": emergency_id,
            "status": status,
            "location": location,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.broadcast_emergency(emergency_id, message)


async def notify_contacts(
    contact_ids: list,
    emergency_id: str,
    message_text: str,
    location: Optional[dict] = None
):
    """Notify emergency contacts"""
    message = {
        "type": "contact_alert",
        "data": {
            "emergency_id": emergency_id,
            "message": message_text,
            "location": location,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.send_to_contacts(contact_ids, message)
