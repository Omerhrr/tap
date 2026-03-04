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
    """
    Main application entry point.

    Args:
        page: Flet page instance
    """
    # Configure page
    page.title = "Tap & Split"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.GREY_100

    # Set window size for desktop
    if page.platform in [ft.PagePlatform.MACOS, ft.PagePlatform.WINDOWS, ft.PagePlatform.LINUX]:
        page.window.width = 400
        page.window.height = 700
        page.window.min_width = 350
        page.window.min_height = 500

    # Current view
    current_view = None

    def show_home():
        """Show the home view."""
        nonlocal current_view
        page.clean()
        current_view = HomeView(
            page=page,
            on_session_joined=show_session
        )
        page.add(current_view)
        page.update()

    def show_session():
        """Show the session view."""
        nonlocal current_view
        page.clean()
        current_view = SessionView(page=page)
        page.add(current_view)
        page.update()

    def on_disconnect(e):
        """Handle page disconnect."""
        # Close WebSocket connection
        asyncio.create_task(state.disconnect_websocket())

    # Register disconnect handler
    page.on_disconnect = on_disconnect

    # Start with home view
    show_home()


if __name__ == "__main__":
    ft.app(target=main)
