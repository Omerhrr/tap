# flet_app/components/home_view.py
import flet as ft
from typing import Optional, Callable
import uuid
import asyncio
import random

from state import state
from api_client import api_client


class HomeView(ft.Column):
    """Home view for creating or joining a session."""

    def __init__(self, page: ft.Page, on_session_joined: Optional[Callable] = None):
        super().__init__()
        self._page = page
        self.on_session_joined = on_session_joined
        self.expand = True
        self.device_id = str(uuid.uuid4())[:8]
        self.controls = self._build_controls()

    def _build_controls(self) -> list:
        """Build the view's controls."""
        # Logo and title using text-based emoji instead of icon
        logo = ft.Column(
            controls=[
                ft.Text("🍽️", size=60),
                ft.Text("Tap & Split", size=32, weight="bold", color="#3F51B5"),
                ft.Text("Split bills effortlessly", size=16, color="grey"),
            ],
            horizontal_alignment="center",
            spacing=8
        )

        # Name input
        self.name_field = ft.TextField(
            label="Your Name",
            hint_text="Enter your name",
            autofocus=True,
        )

        # Create session button
        create_btn = ft.Button(
            "Create New Session",
            icon="add_circle",
            bgcolor="#3F51B5",
            color="white",
            on_click=self._on_create_click,
            width=280
        )

        # Divider
        divider = ft.Row(
            controls=[
                ft.Divider(expand=True, color="grey"),
                ft.Text("or", color="grey"),
                ft.Divider(expand=True, color="grey")
            ],
            alignment="center"
        )

        # Join session section
        self.join_code_field = ft.TextField(
            label="Session Code",
            hint_text="Enter 6-character code",
            max_length=6,
        )

        join_btn = ft.Button(
            "Join Session",
            icon="login",
            bgcolor="#4CAF50",
            color="white",
            on_click=self._on_join_click,
            width=280
        )

        join_section = ft.Column(
            controls=[
                self.join_code_field,
                ft.Divider(height=8, color="transparent"),
                join_btn
            ],
            horizontal_alignment="center",
            width=280
        )

        # Main content
        content = ft.Column(
            controls=[
                logo,
                ft.Divider(height=32, color="transparent"),
                self.name_field,
                ft.Divider(height=16, color="transparent"),
                create_btn,
                ft.Divider(height=24, color="transparent"),
                divider,
                ft.Divider(height=24, color="transparent"),
                join_section
            ],
            horizontal_alignment="center",
            alignment="center",
            expand=True
        )

        return [content]

    async def _on_create_click(self, e):
        """Handle create session button click."""
        name = self.name_field.value.strip()
        if not name:
            self._show_error("Please enter your name")
            return

        try:
            session_data = await api_client.create_session()
            participant_data = await api_client.join_session(
                session_data['id'],
                {
                    "device_id": self.device_id,
                    "name": name,
                    "color": self._generate_color()
                }
            )

            state.device_id = self.device_id
            state.my_name = name
            state.participant_id = participant_data['id']
            state.update_session(session_data)
            await state.connect_websocket()

            if self.on_session_joined:
                self.on_session_joined()

        except Exception as ex:
            self._show_error(f"Failed to create session: {str(ex)}")

    async def _on_join_click(self, e):
        """Handle join session button click."""
        name = self.name_field.value.strip()
        code = self.join_code_field.value.strip().upper()

        if not name:
            self._show_error("Please enter your name")
            return

        if len(code) != 6:
            self._show_error("Please enter a valid 6-character code")
            return

        try:
            session_data = await api_client.get_session(code)
            participant_data = await api_client.join_session(
                session_data['id'],
                {
                    "device_id": self.device_id,
                    "name": name,
                    "color": self._generate_color()
                }
            )

            state.device_id = self.device_id
            state.my_name = name
            state.participant_id = participant_data['id']
            state.update_session(session_data)
            await state.connect_websocket()

            if self.on_session_joined:
                self.on_session_joined()

        except Exception as ex:
            self._show_error(f"Failed to join session: {str(ex)}")

    def _generate_color(self) -> str:
        """Generate a random color for the participant."""
        colors = [
            "#F44336", "#E91E63", "#9C27B0", "#673AB7",
            "#3F51B5", "#2196F3", "#00BCD4", "#009688",
            "#4CAF50", "#8BC34A", "#CDDC39", "#FFC107",
            "#FF9800", "#FF5722", "#795548", "#607D8B"
        ]
        return random.choice(colors)

    def _show_error(self, message: str):
        """Show an error message."""
        self._page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor="red")
        self._page.snack_bar.open = True
        self._page.update()
