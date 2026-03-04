# screens/session_screen.py - Session screen
# Compatible with KivyMD 1.2.0
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty
from kivy.clock import Clock
import threading

from state import app_state
from api_client import api_client
from components.dialogs import AddItemDialog
from components.item_card import ItemCard


class Tab(MDFloatLayout, MDTabsBase):
    """Tab class for session tabs."""
    pass


class SessionScreen(MDScreen):
    """Main session screen with tabs for items, participants, and summary."""

    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'session'
        self._build_ui()

        # Bind to state changes
        app_state.bind(session=self._on_session_update)
        app_state.bind(items=self._on_items_update)
        app_state.bind(participants=self._on_participants_update)

    def _build_ui(self):
        """Build the session screen UI."""
        # Main container
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding='0dp',
            spacing='0dp',
        )

        # Header card
        header = MDCard(
            orientation='vertical',
            padding='16dp',
            spacing='8dp',
            radius=[0],
            elevation=2,
            size_hint_y=None,
            height='100dp',
            md_bg_color=(0.13, 0.59, 0.95, 1),  # Primary color
        )

        # Session code row
        code_row = MDBoxLayout(
            orientation='horizontal',
            spacing='8dp',
            size_hint_y=None,
            height='30dp',
        )

        code_label = MDLabel(
            text="Session Code:",
            font_style='Body1',
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.7),
            halign='left',
            size_hint_x=0.4,
        )
        code_row.add_widget(code_label)

        self.code_value = MDLabel(
            text="------",
            font_style='H6',
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign='left',
            size_hint_x=0.6,
        )
        code_row.add_widget(self.code_value)

        header.add_widget(code_row)

        # Status row
        status_row = MDBoxLayout(
            orientation='horizontal',
            spacing='8dp',
            size_hint_y=None,
            height='30dp',
        )

        status_label = MDLabel(
            text="Status:",
            font_style='Body1',
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.7),
            halign='left',
            size_hint_x=0.4,
        )
        status_row.add_widget(status_label)

        self.status_value = MDLabel(
            text="Active",
            font_style='Body1',
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign='left',
            size_hint_x=0.6,
        )
        status_row.add_widget(self.status_value)

        header.add_widget(status_row)

        # Total row
        total_row = MDBoxLayout(
            orientation='horizontal',
            spacing='8dp',
            size_hint_y=None,
            height='30dp',
        )

        total_label = MDLabel(
            text="Total:",
            font_style='Body1',
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.7),
            halign='left',
            size_hint_x=0.4,
        )
        total_row.add_widget(total_label)

        self.total_value = MDLabel(
            text="₦0.00",
            font_style='H6',
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign='left',
            size_hint_x=0.6,
        )
        total_row.add_widget(self.total_value)

        header.add_widget(total_row)

        main_layout.add_widget(header)

        # Content container (we'll use simple switching instead of tabs for compatibility)
        self.content_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=1,
        )
        main_layout.add_widget(self.content_container)

        # Bottom navigation bar
        nav_bar = MDCard(
            orientation='horizontal',
            padding='8dp',
            spacing='8dp',
            radius=[0],
            elevation=4,
            size_hint_y=None,
            height='50dp',
        )

        items_btn = MDFlatButton(
            text="Items",
            on_release=lambda x: self._show_items_content(),
        )
        nav_bar.add_widget(items_btn)

        people_btn = MDFlatButton(
            text="People",
            on_release=lambda x: self._show_participants_content(),
        )
        nav_bar.add_widget(people_btn)

        summary_btn = MDFlatButton(
            text="Summary",
            on_release=lambda x: self._show_summary_content(),
        )
        nav_bar.add_widget(summary_btn)

        add_btn = MDRaisedButton(
            text="+ Add",
            on_release=self._show_add_item_dialog,
        )
        nav_bar.add_widget(add_btn)

        main_layout.add_widget(nav_bar)

        # Bottom action bar
        actions = MDCard(
            orientation='horizontal',
            padding='8dp',
            spacing='8dp',
            radius=[0],
            elevation=4,
            size_hint_y=None,
            height='60dp',
        )

        scan_btn = MDFlatButton(
            text="Scan",
            icon="camera",
            on_release=self._on_scan_receipt,
        )
        actions.add_widget(scan_btn)

        auto_btn = MDFlatButton(
            text="Split All",
            on_release=self._on_auto_assign,
        )
        actions.add_widget(auto_btn)

        lock_btn = MDRaisedButton(
            text="Lock",
            on_release=self._on_lock_session,
        )
        actions.add_widget(lock_btn)

        main_layout.add_widget(actions)

        self.add_widget(main_layout)

        # Initialize with items content
        self._show_items_content()

    def _show_items_content(self):
        """Show items list."""
        self.content_container.clear_widgets()

        scroll = MDScrollView()

        container = MDBoxLayout(
            orientation='vertical',
            padding='16dp',
            spacing='12dp',
            size_hint_y=None,
        )
        container.bind(minimum_height=container.setter('height'))

        if not app_state.items:
            empty_label = MDLabel(
                text="No items yet.\nTap 'Add' to add items or scan a receipt.",
                font_style='Body1',
                halign='center',
                theme_text_color="Secondary",
                size_hint_y=None,
                height='100dp',
            )
            container.add_widget(empty_label)
        else:
            for item in app_state.items:
                card = ItemCard(
                    item_id=item.get('id', 0),
                    description=item.get('description', ''),
                    amount=item.get('amount', 0),
                    quantity=item.get('quantity', 1),
                    assignments=item.get('assignments', []),
                    participants=app_state.participants,
                    disputed=item.get('is_disputed', False),
                    on_assign=self._show_assign_dialog,
                    on_delete=self._delete_item,
                )
                container.add_widget(card)

        scroll.add_widget(container)
        self.content_container.add_widget(scroll)

    def _show_participants_content(self):
        """Show participants list."""
        self.content_container.clear_widgets()

        scroll = MDScrollView()

        container = MDBoxLayout(
            orientation='vertical',
            padding='16dp',
            spacing='12dp',
            size_hint_y=None,
        )
        container.bind(minimum_height=container.setter('height'))

        # Current user highlight
        current_label = MDLabel(
            text="You",
            font_style='H6',
            size_hint_y=None,
            height='40dp',
        )
        container.add_widget(current_label)

        if app_state.participant:
            name_label = MDLabel(
                text=f"  {app_state.participant_name}",
                font_style='Body1',
                size_hint_y=None,
                height='30dp',
            )
            container.add_widget(name_label)

            share = app_state.participant_shares.get(app_state.participant_id, 0)
            share_label = MDLabel(
                text=f"  Your share: ₦{share:,.2f}",
                font_style='Body1',
                theme_text_color="Primary",
                size_hint_y=None,
                height='30dp',
            )
            container.add_widget(share_label)

        # Other participants
        others_label = MDLabel(
            text="\nOthers in this session",
            font_style='H6',
            size_hint_y=None,
            height='50dp',
        )
        container.add_widget(others_label)

        for p in app_state.participants:
            if p.get('id') != app_state.participant_id:
                name = p.get('name', 'Unknown')
                share = app_state.participant_shares.get(p.get('id'), 0)
                person_label = MDLabel(
                    text=f"  {name}: ₦{share:,.2f}",
                    font_style='Body1',
                    size_hint_y=None,
                    height='30dp',
                )
                container.add_widget(person_label)

        scroll.add_widget(container)
        self.content_container.add_widget(scroll)

    def _show_summary_content(self):
        """Show settlement summary."""
        self.content_container.clear_widgets()

        scroll = MDScrollView()

        container = MDBoxLayout(
            orientation='vertical',
            padding='16dp',
            spacing='16dp',
            size_hint_y=None,
        )
        container.bind(minimum_height=container.setter('height'))

        # Session summary card
        summary_card = MDCard(
            orientation='vertical',
            padding='16dp',
            spacing='12dp',
            radius=[12],
            elevation=2,
        )

        summary_title = MDLabel(
            text="Session Summary",
            font_style='H6',
        )
        summary_card.add_widget(summary_title)

        # Subtotal
        subtotal_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='30dp',
        )
        subtotal_row.add_widget(MDLabel(text="Subtotal:", size_hint_x=0.5))
        subtotal_row.add_widget(MDLabel(
            text=app_state.format_currency(app_state.session.get('subtotal', 0)),
            halign='right',
            size_hint_x=0.5,
        ))
        summary_card.add_widget(subtotal_row)

        # Tax
        tax_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='30dp',
        )
        tax_row.add_widget(MDLabel(text="Tax:", size_hint_x=0.5))
        tax_row.add_widget(MDLabel(
            text=app_state.format_currency(app_state.session.get('tax_amount', 0)),
            halign='right',
            size_hint_x=0.5,
        ))
        summary_card.add_widget(tax_row)

        # Tip
        tip_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='30dp',
        )
        tip_row.add_widget(MDLabel(text=f"Tip ({app_state.session.get('tip_percent', 18)}%):", size_hint_x=0.5))
        tip_row.add_widget(MDLabel(
            text=app_state.format_currency(app_state.session.get('tip_amount', 0)),
            halign='right',
            size_hint_x=0.5,
        ))
        summary_card.add_widget(tip_row)

        # Total
        total_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='40dp',
        )
        total_row.add_widget(MDLabel(
            text="Total:",
            font_style='H6',
            size_hint_x=0.5,
        ))
        total_row.add_widget(MDLabel(
            text=app_state.format_currency(app_state.session.get('total_amount', 0)),
            font_style='H6',
            halign='right',
            theme_text_color="Primary",
            size_hint_x=0.5,
        ))
        summary_card.add_widget(total_row)

        container.add_widget(summary_card)

        # Your share card
        share_card = MDCard(
            orientation='vertical',
            padding='16dp',
            spacing='12dp',
            radius=[12],
            elevation=2,
        )

        share_title = MDLabel(
            text="Your Share",
            font_style='H6',
        )
        share_card.add_widget(share_title)

        your_share = app_state.participant_shares.get(app_state.participant_id, 0)
        share_value = MDLabel(
            text=app_state.format_currency(your_share),
            font_style='H4',
            theme_text_color="Primary",
            halign='center',
        )
        share_card.add_widget(share_value)

        container.add_widget(share_card)

        scroll.add_widget(container)
        self.content_container.add_widget(scroll)

    def _show_add_item_dialog(self, instance=None):
        """Show dialog to add a new item."""
        content = AddItemDialog()
        self.dialog = MDDialog(
            title="Add Item",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    on_release=lambda x: self.dialog.dismiss(),
                ),
                MDRaisedButton(
                    text="Add",
                    on_release=lambda x: self._add_item(content),
                ),
            ],
        )
        self.dialog.open()

    def _add_item(self, content):
        """Add item to session."""
        data = content.get_item_data()
        if not data or not data.get('description'):
            self._show_snackbar("Please enter item details")
            return

        if self.dialog:
            self.dialog.dismiss()

        def add():
            try:
                api_client.add_item(app_state.session_id, data)
                self._refresh_session()
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_snackbar(str(e)), 0)

        threading.Thread(target=add, daemon=True).start()

    def _show_assign_dialog(self, item_id: int):
        """Show dialog to assign item to participants."""
        self._show_snackbar(f"Assign item #{item_id} - Select participants")

    def _delete_item(self, item_id: int):
        """Delete an item."""
        def delete():
            try:
                api_client.delete_item(item_id)
                self._refresh_session()
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_snackbar(str(e)), 0)

        threading.Thread(target=delete, daemon=True).start()

    def _on_scan_receipt(self, instance):
        """Handle scan receipt button."""
        self._show_snackbar("Scan receipt - Coming soon!")

    def _on_auto_assign(self, instance):
        """Auto-assign all items equally."""
        def auto():
            try:
                api_client.auto_assign(app_state.session_id)
                self._refresh_session()
                Clock.schedule_once(lambda dt: self._show_snackbar("Items split equally!"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_snackbar(str(e)), 0)

        threading.Thread(target=auto, daemon=True).start()

    def _on_lock_session(self, instance):
        """Lock the session."""
        def lock():
            try:
                api_client.lock_session(app_state.session_id)
                self._refresh_session()
                Clock.schedule_once(lambda dt: self._show_snackbar("Session locked!"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_snackbar(str(e)), 0)

        threading.Thread(target=lock, daemon=True).start()

    def _refresh_session(self):
        """Refresh session data."""
        def refresh():
            try:
                session = api_client.get_session(app_state.session_code)
                Clock.schedule_once(lambda dt: app_state.update_session(session), 0)
            except Exception as e:
                print(f"Error refreshing session: {e}")

        threading.Thread(target=refresh, daemon=True).start()

    def _on_session_update(self, instance, value):
        """Handle session state update."""
        self.code_value.text = app_state.session_code or "------"
        self.status_value.text = app_state.session_status.title() or "Active"
        self.total_value.text = app_state.format_currency(
            app_state.session.get('total_amount', 0)
        )

    def _on_items_update(self, instance, value):
        """Handle items update."""
        pass

    def _on_participants_update(self, instance, value):
        """Handle participants update."""
        pass

    def _show_snackbar(self, message: str):
        """Show a snackbar message."""
        Snackbar(text=message).open()

    def on_enter(self):
        """Called when screen is entered."""
        self._on_session_update(None, None)
        self._show_items_content()
