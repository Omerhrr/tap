# flet_app/state.py
from typing import Callable, List, Dict, Optional
import json
import asyncio
import websockets


class AppState:
    """Global state management for the application."""

    def __init__(self):
        # User info
        self.session_id: Optional[int] = None
        self.session_code: Optional[str] = None
        self.device_id: Optional[str] = None
        self.participant_id: Optional[int] = None
        self.my_name: Optional[str] = None
        self.my_color: str = "#2196F3"

        # Session data
        self.status: str = "active"  # active, locked, settled
        self.participants: List[dict] = []
        self.items: List[dict] = []
        self.assignments: List[dict] = []

        # Totals
        self.subtotal: float = 0.0
        self.tax_amount: float = 0.0
        self.tip_percent: float = 18.0
        self.tip_amount: float = 0.0
        self.total_amount: float = 0.0
        self.participant_shares: Dict[int, float] = {}

        # WebSocket
        self._listeners: List[Callable] = []
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._ws_task: Optional[asyncio.Task] = None
        self._ws_url: str = "ws://localhost:8000/ws"

        # UI state
        self.is_connected: bool = False
        self.error_message: Optional[str] = None

    def subscribe(self, callback: Callable):
        """Subscribe to state changes."""
        self._listeners.append(callback)
        return lambda: self._listeners.remove(callback)

    def notify(self):
        """Notify all listeners of state change."""
        for callback in self._listeners:
            try:
                callback()
            except Exception as e:
                print(f"Error in state listener: {e}")

    def update_session(self, data: dict):
        """Update session data from API response."""
        self.session_id = data.get('id')
        self.session_code = data.get('code')
        self.status = data.get('status', 'active')
        self.participants = data.get('participants', [])
        self.items = data.get('items', [])
        self.subtotal = data.get('subtotal', 0.0)
        self.tax_amount = data.get('tax_amount', 0.0)
        self.tip_percent = data.get('tip_percent', 18.0)
        self.tip_amount = data.get('tip_amount', 0.0)
        self.total_amount = data.get('total_amount', 0.0)
        self.participant_shares = data.get('participant_shares', {})

        # Flatten assignments
        self.calculate_assignments()
        self.notify()

    def calculate_assignments(self):
        """Flatten assignments for easy lookup."""
        self.assignments = []
        for item in self.items:
            for assignment in item.get('assignments', []):
                self.assignments.append({
                    'id': assignment['id'],
                    'item_id': item['id'],
                    'participant_id': assignment['participant_id'],
                    'share_percent': assignment['share_percent']
                })

    def get_item_assignments(self, item_id: int) -> List[dict]:
        """Get all assignments for an item."""
        return [a for a in self.assignments if a['item_id'] == item_id]

    def get_participant_by_id(self, participant_id: int) -> Optional[dict]:
        """Get participant by ID."""
        return next(
            (p for p in self.participants if p['id'] == participant_id),
            None
        )

    def get_my_share(self) -> float:
        """Calculate current user's total owed."""
        if not self.participant_id:
            return 0.0

        # Use pre-calculated shares if available
        if self.participant_shares and self.participant_id in self.participant_shares:
            return self.participant_shares[self.participant_id]

        # Manual calculation
        total = 0.0
        for item in self.items:
            item_total = item['amount']
            item_assignments = self.get_item_assignments(item['id'])

            if not item_assignments:
                # Split equally
                total += item_total / max(len(self.participants), 1)
            else:
                my_assignment = next(
                    (a for a in item_assignments if a['participant_id'] == self.participant_id),
                    None
                )
                if my_assignment:
                    total += (my_assignment['share_percent'] / 100) * item_total

        return round(total, 2)

    def is_item_assigned(self, item_id: int) -> bool:
        """Check if item has any assignments."""
        return len(self.get_item_assignments(item_id)) > 0

    def get_unassigned_items(self) -> List[dict]:
        """Get all unassigned items."""
        return [item for item in self.items if not self.is_item_assigned(item['id'])]

    # WebSocket methods
    async def connect_websocket(self):
        """Connect to WebSocket for real-time updates."""
        if self._ws_task:
            self._ws_task.cancel()

        self._ws_task = asyncio.create_task(self._ws_loop())

    async def disconnect_websocket(self):
        """Disconnect WebSocket."""
        if self._ws_task:
            self._ws_task.cancel()
            self._ws_task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        self.is_connected = False
        self.notify()

    async def _ws_loop(self):
        """WebSocket connection loop."""
        uri = f"{self._ws_url}/{self.session_id}"

        while True:
            try:
                async with websockets.connect(uri) as ws:
                    self._ws = ws
                    self.is_connected = True
                    self.error_message = None
                    self.notify()

                    # Identify self
                    await ws.send(json.dumps({
                        "type": "identify",
                        "device_id": self.device_id,
                        "participant_id": self.participant_id
                    }))

                    # Message loop
                    async for message in ws:
                        await self._handle_message(json.loads(message))

            except websockets.exceptions.ConnectionClosed:
                self.is_connected = False
                self.notify()
                # Attempt reconnect after delay
                await asyncio.sleep(3)

            except Exception as e:
                print(f"WebSocket error: {e}")
                self.error_message = str(e)
                self.is_connected = False
                self.notify()
                await asyncio.sleep(3)

    async def _handle_message(self, msg: dict):
        """Handle incoming WebSocket message."""
        msg_type = msg.get('type')
        data = msg.get('data', {})

        if msg_type == 'item_added':
            if data.get('bulk'):
                # Multiple items added
                for item in data.get('items', []):
                    self.items.append(item)
            else:
                self.items.append(data)

        elif msg_type == 'item_updated':
            # Update existing item
            for i, item in enumerate(self.items):
                if item['id'] == data['id']:
                    self.items[i] = {**item, **data}
                    break

        elif msg_type == 'item_removed':
            # Remove item
            self.items = [i for i in self.items if i['id'] != data.get('item_id')]

        elif msg_type == 'item_assigned':
            # Add assignment
            self.assignments.append({
                'id': data['assignment_id'],
                'item_id': data['item_id'],
                'participant_id': data['participant_id'],
                'share_percent': data['share_percent']
            })

        elif msg_type == 'assignment_removed':
            # Remove assignment
            self.assignments = [
                a for a in self.assignments
                if a['id'] != data.get('assignment_id')
            ]

        elif msg_type == 'participant_joined':
            # Add participant if not already in list
            if not any(p['id'] == data['id'] for p in self.participants):
                self.participants.append(data)

        elif msg_type == 'participant_left':
            # Remove participant
            self.participants = [
                p for p in self.participants
                if p['device_id'] != data.get('device_id')
            ]

        elif msg_type == 'session_locked':
            self.status = 'locked'

        elif msg_type == 'session_settled':
            self.status = 'settled'

        elif msg_type == 'state_sync':
            # Full state sync
            if 'items' in data:
                self.items = data['items']
                self.calculate_assignments()

        self.notify()

    async def send_ws_message(self, msg: dict):
        """Send a message via WebSocket."""
        if self._ws:
            await self._ws.send(json.dumps(msg))


# Global state instance
state = AppState()
