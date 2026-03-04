# components/dialogs.py - Custom dialogs
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.properties import StringProperty, ObjectProperty


class InputDialog(MDDialog):
    """Generic input dialog."""

    def __init__(self, title: str, hint: str, on_confirm, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.on_confirm = on_confirm

        self.text_field = MDTextField(
            hint_text=hint,
            size_hint_x=1,
        )

        self.add_widget(self.text_field)

        # Add buttons
        cancel_btn = MDButton(
            MDButtonText(text="Cancel"),
            style="text",
            on_release=lambda x: self.dismiss()
        )
        confirm_btn = MDButton(
            MDButtonText(text="Confirm"),
            style="text",
            on_release=self._on_confirm
        )

        # Note: MDDialog handles buttons differently, using properties
        self.buttons = [cancel_btn, confirm_btn]

    def _on_confirm(self, instance):
        if self.on_confirm:
            self.on_confirm(self.text_field.text)
        self.dismiss()


class NameInputDialog(MDBoxLayout):
    """Custom content for name input dialog."""

    text = StringProperty('')
    hint = StringProperty('Enter your name')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = '10dp'
        self.padding = '20dp'
        self.size_hint_y = None
        self.height = '60dp'

        self.text_field = MDTextField(
            hint_text=self.hint,
            size_hint_x=1,
        )
        self.text_field.bind(text=self.setter('text'))
        self.add_widget(self.text_field)


class SessionCodeDialog(MDBoxLayout):
    """Custom content for session code input dialog."""

    code = StringProperty('')

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
        self.text_field.bind(text=self.setter('code'))
        self.add_widget(self.text_field)


class AddItemDialog(MDBoxLayout):
    """Custom content for adding an item."""

    description = StringProperty('')
    amount = StringProperty('0')
    quantity = StringProperty('1')

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
        self.desc_field.bind(text=self.setter('description'))

        self.amount_field = MDTextField(
            hint_text="Amount (₦)",
            input_filter='float',
            size_hint_x=1,
        )
        self.amount_field.bind(text=self.setter('amount'))

        self.qty_field = MDTextField(
            hint_text="Quantity",
            input_filter='int',
            text='1',
            size_hint_x=1,
        )
        self.qty_field.bind(text=self.setter('quantity'))

        self.add_widget(self.desc_field)
        self.add_widget(self.amount_field)
        self.add_widget(self.qty_field)

    def get_item_data(self):
        """Return item data as dict."""
        try:
            return {
                'description': self.description,
                'amount': float(self.amount) if self.amount else 0,
                'quantity': int(self.quantity) if self.quantity else 1,
            }
        except ValueError:
            return None


class ConfirmDialog(MDBoxLayout):
    """Confirmation dialog content."""

    message = StringProperty('')

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.orientation = 'vertical'
        self.padding = '20dp'
        self.size_hint_y = None
        self.height = '60dp'

        self.add_widget(MDLabel(
            text=self.message,
            theme_font_size="Body",
            halign='center',
        ))
