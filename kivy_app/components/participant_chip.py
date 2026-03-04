# components/participant_chip.py - Participant avatar/chip component
from kivy.properties import StringProperty, NumericProperty, DictProperty, BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.circularlayout import MDCircularLayout
from kivymd.uix.widget import MDWidget


class ParticipantAvatar(MDCard):
    """Circular avatar for a participant."""

    name = StringProperty('')
    color = StringProperty('#2196F3')
    participant_id = NumericProperty(0)
    selected = BooleanProperty(False)
    share = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = ('60dp', '60dp')
        self.radius = [30]
        self.elevation = 2
        self.ripple_behavior = True
        self.md_bg_color = self._hex_to_rgba(self.color)

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the avatar UI."""
        self.clear_widgets()

        # Main container
        container = MDBoxLayout(
            orientation='vertical',
            spacing='4dp',
            padding='4dp',
            size_hint=(1, 1),
        )

        # Initial letter
        initial = self.name[0].upper() if self.name else '?'

        label = MDLabel(
            text=initial,
            halign='center',
            valign='center',
            theme_font_size="Title",
            font_style="Medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        )

        container.add_widget(label)
        self.add_widget(container)

        # Update background color
        self.md_bg_color = self._hex_to_rgba(self.color)

    def _hex_to_rgba(self, hex_color: str):
        """Convert hex color to RGBA tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return (r, g, b, 1)
        return (0.13, 0.59, 0.95, 1)  # Default blue

    def on_name(self, instance, value):
        self._build_ui()

    def on_color(self, instance, value):
        self.md_bg_color = self._hex_to_rgba(value)


class ParticipantChip(MDCard):
    """Chip showing participant with name and optional share."""

    name = StringProperty('')
    color = StringProperty('#2196F3')
    participant_id = NumericProperty(0)
    share = NumericProperty(0.0)
    show_share = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.width = '150dp'
        self.height = '40dp'
        self.radius = [20]
        self.elevation = 1
        self.ripple_behavior = True
        self.padding = ('8dp', '4dp', '8dp', '4dp')

        self._build_ui()

    def _build_ui(self):
        """Build the chip UI."""
        self.clear_widgets()

        container = MDBoxLayout(
            orientation='horizontal',
            spacing='8dp',
            size_hint=(1, 1),
        )

        # Color dot
        dot = MDWidget(
            size_hint=(None, None),
            size=('12dp', '12dp'),
            radius=[6],
        )
        dot.md_bg_color = self._hex_to_rgba(self.color)
        container.add_widget(dot)

        # Name
        name_label = MDLabel(
            text=self.name,
            theme_font_size="Body",
            font_style="Medium",
            halign='left',
            valign='center',
            size_hint_x=0.6,
        )
        container.add_widget(name_label)

        # Share amount if enabled
        if self.show_share and self.share > 0:
            share_label = MDLabel(
                text=f"₦{self.share:,.0f}",
                theme_font_size="Body",
                font_style="Medium",
                theme_text_color="Secondary",
                halign='right',
                valign='center',
                size_hint_x=0.4,
            )
            container.add_widget(share_label)

        self.add_widget(container)
        self.md_bg_color = self._hex_to_rgba(self.color + '20')  # 20% opacity

    def _hex_to_rgba(self, hex_color: str):
        """Convert hex color to RGBA tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            return (r, g, b, 1)
        return (0.13, 0.59, 0.95, 1)

    def on_name(self, instance, value):
        self._build_ui()

    def on_color(self, instance, value):
        self._build_ui()

    def on_share(self, instance, value):
        self._build_ui()
