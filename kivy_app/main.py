#!/usr/bin/env python3
"""
Tap & Split - Bill Splitting App
Main entry point for KivyMD frontend
Compatible with KivyMD 1.2.0
"""

import sys
import os

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy import Config
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivy.core.window import Window
from kivy.clock import Clock

from screens.home_screen import HomeScreen
from screens.session_screen import SessionScreen
from state import app_state


class TapSplitApp(MDApp):
    """Main application class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Tap & Split"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Teal"
        self.theme_cls.theme_style = "Light"

    def build(self):
        """Build the application UI."""
        # Set window size for desktop
        Window.size = (400, 700)

        # Create screen manager
        sm = ScreenManager()

        # Add screens
        sm.add_widget(HomeScreen())
        sm.add_widget(SessionScreen())

        return sm

    def on_start(self):
        """Called when app starts."""
        print(f"Tap & Split started - Device ID: {app_state.device_id}")

    def on_stop(self):
        """Called when app stops."""
        app_state.stop_websocket()
        from api_client import api_client
        api_client.close()


def main():
    """Main entry point."""
    TapSplitApp().run()


if __name__ == '__main__':
    main()
