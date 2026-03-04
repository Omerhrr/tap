# screens/home_screen.py - Home screen
# Compatible with KivyMD 1.2.0
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.snackbar import Snackbar
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
import threading

from state import app_state
from api_client import api_client
from components.dialogs import SessionCodeDialog


class HomeScreen(MDScreen):
    """Home screen for creating or joining sessions."""

    name_input = ObjectProperty(None)
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'
        self._build_ui()

    def _build_ui(self):
        """Build the home screen UI."""
        # Main container
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding='24dp',
            spacing='24dp',
        )

        # Header section
        header = MDBoxLayout(
            orientation='vertical',
            spacing='12dp',
            size_hint_y=None,
            height='120dp',
        )

        title = MDLabel(
            text="Tap & Split",
            halign='center',
            font_style='H4',
            theme_text_color="Primary",
        )
        header.add_widget(title)

        subtitle = MDLabel(
            text="Split bills with friends instantly",
            halign='center',
            font_style='Body1',
            theme_text_color="Secondary",
        )
        header.add_widget(subtitle)

        main_layout.add_widget(header)

        # Card for name input
        name_card = MDCard(
            orientation='vertical',
            padding='20dp',
            spacing='16dp',
            radius=[16],
            elevation=2,
            size_hint_y=None,
            height='120dp',
        )

        name_label = MDLabel(
            text="Your Name",
            font_style='H6',
        )
        name_card.add_widget(name_label)

        self.name_input = MDTextField(
            hint_text="Enter your name",
            size_hint_x=1,
            max_text_length=50,
        )
        name_card.add_widget(self.name_input)

        main_layout.add_widget(name_card)

        # Action buttons card
        actions_card = MDCard(
            orientation='vertical',
            padding='20dp',
            spacing='16dp',
            radius=[16],
            elevation=2,
            size_hint_y=None,
            height='200dp',
        )

        actions_label = MDLabel(
            text="Start or Join a Session",
            font_style='H6',
        )
        actions_card.add_widget(actions_label)

        # Create session button
        create_btn = MDRaisedButton(
            text="Create New Session",
            size_hint_x=1,
            on_release=self._on_create_session,
        )
        actions_card.add_widget(create_btn)

        # Join session button
        join_btn = MDFlatButton(
            text="Join Existing Session",
            size_hint_x=1,
            on_release=self._on_join_session,
        )
        actions_card.add_widget(join_btn)

        main_layout.add_widget(actions_card)

        # Device ID info
        info_label = MDLabel(
            text=f"Device ID: {app_state.device_id}",
            font_style='Caption',
            theme_text_color="Secondary",
            halign='center',
            size_hint_y=None,
            height='30dp',
        )
        main_layout.add_widget(info_label)

        # Spacer
        main_layout.add_widget(MDBoxLayout(size_hint_y=1))

        self.add_widget(main_layout)

    def _on_create_session(self, instance):
        """Handle create session button."""
        name = self.name_input.text.strip()
        if not name:
            self._show_error("Please enter your name")
            return

        # Create session in background thread
        def create():
            try:
                app_state.is_loading = True
                session = api_client.create_session()
                app_state.update_session(session)

                # Join the session
                participant = api_client.join_session(
                    session['id'],
                    {
                        'name': name,
                        'device_id': app_state.device_id,
                        'color': '#4CAF50',  # Green for creator
                    }
                )
                app_state.set_current_participant(participant)

                # Navigate to session screen
                Clock.schedule_once(lambda dt: self._go_to_session(), 0)

            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_error(str(e)), 0)
            finally:
                app_state.is_loading = False

        threading.Thread(target=create, daemon=True).start()

    def _on_join_session(self, instance):
        """Handle join session button."""
        name = self.name_input.text.strip()
        if not name:
            self._show_error("Please enter your name")
            return

        # Show session code dialog
        content = SessionCodeDialog()
        self.dialog = MDDialog(
            title="Join Session",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda x: self.dialog.dismiss(),
                ),
                MDFlatButton(
                    text="Join",
                    on_release=lambda x: self._join_with_code(content.text_field.text, name),
                ),
            ],
        )
        self.dialog.open()

    def _join_with_code(self, code: str, name: str):
        """Join session with code."""
        if not code or len(code) != 6:
            self._show_error("Please enter a valid 6-character code")
            return

        if self.dialog:
            self.dialog.dismiss()

        def join():
            try:
                app_state.is_loading = True
                session = api_client.get_session(code.upper())
                app_state.update_session(session)

                # Join the session
                participant = api_client.join_session(
                    session['id'],
                    {
                        'name': name,
                        'device_id': app_state.device_id,
                        'color': '#2196F3',  # Blue for joiner
                    }
                )
                app_state.set_current_participant(participant)

                # Navigate to session screen
                Clock.schedule_once(lambda dt: self._go_to_session(), 0)

            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_error(str(e)), 0)
            finally:
                app_state.is_loading = False

        threading.Thread(target=join, daemon=True).start()

    def _go_to_session(self):
        """Navigate to session screen."""
        self.manager.current = 'session'

    def _show_error(self, message: str):
        """Show error message."""
        app_state.set_error(message)
        Snackbar(text=message, bg_color=(1, 0.3, 0.3, 1)).open()

    def on_enter(self):
        """Called when screen is entered."""
        app_state.clear_session()
        app_state.clear_messages()
