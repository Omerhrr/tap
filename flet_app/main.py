# flet_app/main.py
"""
Tap & Split - Main Entry Point

A real-time collaborative bill-splitting application.
Run with: flet run main.py
"""
import flet as ft
import asyncio

from state import state
from api_client import api_client
from components.home_view import HomeView
from components.session_view import SessionView


def main(page: ft.Page):
    """Main application entry point."""
    # Configure page
    page.title = "Tap & Split"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Current view
    current_view = None

    def show_home():
        """Show the home view."""
        nonlocal current_view
        page.clean()
        current_view = HomeView(page, on_session_joined=show_session)
        page.add(current_view)
        page.update()

    def show_session():
        """Show the session view."""
        nonlocal current_view
        page.clean()
        current_view = SessionView(page)
        page.add(current_view)
        page.update()

    def on_disconnect(e):
        """Handle page disconnect."""
        asyncio.create_task(state.disconnect_websocket())

    page.on_disconnect = on_disconnect
    show_home()


if __name__ == "__main__":
    ft.app(main)
