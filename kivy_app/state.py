# state.py - Global state management
from typing import Optional, Dict, List, Any
from kivy.event import EventDispatcher
from kivy.properties import DictProperty, ListProperty, StringProperty, NumericProperty, BooleanProperty
import uuid
import json
import threading
import websockets


class AppState(EventDispatcher):
    """Global application state with Kivy properties for reactive updates."""

    # Device identity
    device_id: str = StringProperty('')

    # Current session
    session: Dict = DictProperty({})
    session_id: NumericProperty(0)
    session_code: StringProperty('')
    session_status: StringProperty('')

    # Current participant
    participant: Dict = DictProperty({})
    participant_id: NumericProperty(0)
    participant_name: StringProperty('')
    participant_color: StringProperty('#2196F3')

    # Participants list
    participants: List = ListProperty([])

    # Items list
    items: List = ListProperty([])

    # Participant shares
    participant_shares: Dict = DictProperty({})

    # UI State
    is_loading: BooleanProperty(False)
    error_message: StringProperty('')
    success_message: StringProperty('')

    # WebSocket connection
    _ws_thread: Optional[threading.Thread] = None
    _ws_running: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device_id = str(uuid.uuid4())[:8].upper()

    def clear_messages(self):
        """Clear error and success messages."""
        self.error_message = ''
        self.success_message = ''

    def set_error(self, message: str):
        """Set error message."""
        self.error_message = message

    def set_success(self, message: str):
        """Set success message."""
        self.success_message = message

    def update_session(self, session_data: Dict):
        """Update session data."""
        self.session = session_data
        self.session_id = session_data.get('id', 0)
        self.session_code = session_data.get('code', '')
        self.session_status = session_data.get('status', 'active')

        # Update nested data
        if 'participants' in session_data:
            self.participants = session_data['participants']

        if 'items' in session_data:
            self.items = session_data['items']

        if 'participant_shares' in session_data:
            self.participant_shares = session_data['participant_shares']

    def clear_session(self):
        """Clear session data."""
        self.session = {}
        self.session_id = 0
        self.session_code = ''
        self.session_status = ''
        self.participants = []
        self.items = []
        self.participant_shares = {}
        self.participant = {}
        self.participant_id = 0

    def set_current_participant(self, participant_data: Dict):
        """Set current participant data."""
        self.participant = participant_data
        self.participant_id = participant_data.get('id', 0)
        self.participant_name = participant_data.get('name', '')
        self.participant_color = participant_data.get('color', '#2196F3')

    def get_participant_by_id(self, participant_id: int) -> Optional[Dict]:
        """Get participant by ID."""
        for p in self.participants:
            if p.get('id') == participant_id:
                return p
        return None

    def format_currency(self, amount: float) -> str:
        """Format amount with Naira currency."""
        return f"₦{amount:,.2f}"

    def start_websocket(self, on_message_callback):
        """Start WebSocket connection in a background thread."""
        if self._ws_thread and self._ws_thread.is_alive():
            return

        self._ws_running = True

        def ws_loop():
            import asyncio
            asyncio.run(self._websocket_handler(on_message_callback))

        self._ws_thread = threading.Thread(target=ws_loop, daemon=True)
        self._ws_thread.start()

    async def _websocket_handler(self, on_message_callback):
        """Handle WebSocket connection."""
        if not self.session_code:
            return

        ws_url = f"ws://localhost:8000/ws/{self.session_code}?device_id={self.device_id}"

        try:
            async with websockets.connect(ws_url) as websocket:
                while self._ws_running:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=30.0
                        )
                        data = json.loads(message)
                        if on_message_callback:
                            on_message_callback(data)
                    except asyncio.TimeoutError:
                        # Send ping to keep connection alive
                        await websocket.send(json.dumps({"type": "ping"}))
        except Exception as e:
            print(f"WebSocket error: {e}")

    def stop_websocket(self):
        """Stop WebSocket connection."""
        self._ws_running = False


# Global state instance
app_state = AppState()
