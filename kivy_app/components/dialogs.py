# components/dialogs.py - Custom dialogs
# Compatible with KivyMD 1.2.0
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivy.properties import StringProperty


class SessionCodeDialog(MDBoxLayout):
    """Custom content for session code input dialog."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = '10dp'
        self.padding = '20dp'
        self.size_hint_y = None
        self.height = '60dp'

        self.text_field = MDTextField(
            hint_text="Enter 6-character code",
            size_hint_x=1,
            max_text_length=6,
        )
        self.add_widget(self.text_field)


class AddItemDialog(MDBoxLayout):
    """Custom content for adding an item."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = '15dp'
        self.padding = '20dp'
        self.size_hint_y = None
        self.height = '180dp'

        self.desc_field = MDTextField(
            hint_text="Item description",
            size_hint_x=1,
        )

        self.amount_field = MDTextField(
            hint_text="Amount (₦)",
            size_hint_x=1,
        )

        self.qty_field = MDTextField(
            hint_text="Quantity",
            text='1',
            size_hint_x=1,
        )

        self.add_widget(self.desc_field)
        self.add_widget(self.amount_field)
        self.add_widget(self.qty_field)

    def get_item_data(self):
        """Return item data as dict."""
        try:
            amount = float(self.amount_field.text) if self.amount_field.text else 0
            qty = int(self.qty_field.text) if self.qty_field.text else 1
        except ValueError:
            return None

        return {
            'description': self.desc_field.text,
            'amount': amount,
            'quantity': qty,
        }


class NameInputDialog(MDBoxLayout):
    """Custom content for name input dialog."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = '10dp'
        self.padding = '20dp'
        self.size_hint_y = None
        self.height = '60dp'

        self.text_field = MDTextField(
            hint_text="Enter your name",
            size_hint_x=1,
            max_text_length=50,
        )
        self.add_widget(self.text_field)
