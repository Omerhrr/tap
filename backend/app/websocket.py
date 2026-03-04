# backend/app/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from datetime import datetime


# Store active connections per session
# Structure: {session_id: {websocket1, websocket2, ...}}
active_connections: Dict[int, Set[WebSocket]] = {}

# Store device_id -> websocket mapping for identification
websocket_devices: Dict[WebSocket, str] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.device_map: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, session_id: int):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)

    def disconnect(self, websocket: WebSocket, session_id: int):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        if websocket in self.device_map:
            del self.device_map[websocket]

    def register_device(self, websocket: WebSocket, device_id: str):
        """Register a device ID for a WebSocket connection."""
        self.device_map[websocket] = device_id

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")

    async def broadcast_to_session(self, session_id: int, message: dict, exclude: WebSocket = None):
        """Broadcast a message to all connections in a session."""
        if session_id not in self.active_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        disconnected = set()

        for connection in self.active_connections[session_id]:
            if connection == exclude:
                continue

            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws, session_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all active connections."""
        for session_id in self.active_connections:
            await self.broadcast_to_session(session_id, message)


# Global connection manager
manager = ConnectionManager()


async def broadcast_to_session(session_id: int, message: dict, exclude: WebSocket = None):
    """Helper function to broadcast to a session using the global manager."""
    await manager.broadcast_to_session(session_id, message, exclude)


async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """
    WebSocket endpoint for real-time session updates.

    Protocol:
    - Client sends: {"type": "identify", "device_id": "...", "participant_id": ...}
    - Client sends: {"type": "ping"} for keepalive
    - Server broadcasts events: participant_joined, item_added, item_assigned, etc.
    """
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "data": {"message": "Invalid JSON"}},
                    websocket
                )
                continue

            msg_type = message.get("type")

            if msg_type == "identify":
                # Register device
                device_id = message.get("device_id")
                participant_id = message.get("participant_id")

                if device_id:
                    manager.register_device(websocket, device_id)

                    # Store participant_id for this connection
                    websocket.participant_id = participant_id

                    # Confirm identification
                    await manager.send_personal_message(
                        {
                            "type": "identified",
                            "data": {
                                "device_id": device_id,
                                "participant_id": participant_id,
                                "session_id": session_id
                            }
                        },
                        websocket
                    )

            elif msg_type == "ping":
                # Respond to keepalive
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )

            elif msg_type == "request_state":
                # Client is requesting full state sync
                # This would trigger a state_sync message with full session data
                # The actual state fetching is done by the routers
                await manager.send_personal_message(
                    {"type": "state_request", "data": {"session_id": session_id}},
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

        # Notify others that participant left (if we have device info)
        device_id = manager.device_map.get(websocket)
        if device_id:
            await manager.broadcast_to_session(
                session_id,
                {
                    "type": "participant_left",
                    "data": {"device_id": device_id}
                },
                exclude=websocket
            )

    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)
