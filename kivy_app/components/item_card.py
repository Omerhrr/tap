# components/item_card.py - Item card component
from kivy.properties import StringProperty, NumericProperty, ListProperty, DictProperty, BooleanProperty
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.widget import MDWidget
from participant_chip import ParticipantChip


class ItemCard(MDCard):
    """Card displaying an item with assignment status."""

    item_id = NumericProperty(0)
    description = StringProperty('')
    amount = NumericProperty(0.0)
    quantity = NumericProperty(1)
    assignments = ListProperty([])
    participants = ListProperty([])
    disputed = BooleanProperty(False)
    on_assign = None
    on_delete = None
    on_edit = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 'auto'
        self.padding = '12dp'
        self.spacing = '8dp'
        self.radius = [12]
        self.elevation = 2
        self.ripple_behavior = True

        self._build_ui()

    def _build_ui(self):
        """Build the card UI."""
        self.clear_widgets()

        main_container = MDBoxLayout(
            orientation='vertical',
            spacing='8dp',
            size_hint_y=None,
            height='auto',
        )

        # Header row: Description and amount
        header = MDBoxLayout(
            orientation='horizontal',
            spacing='8dp',
            size_hint_y=None,
            height='30dp',
        )

        # Description
        desc_label = MDLabel(
            text=self.description,
            theme_font_size="Body",
            font_style="Medium",
            halign='left',
            size_hint_x=0.6,
        )
        header.add_widget(desc_label)

        # Amount
        amount_label = MDLabel(
            text=f"₦{self.amount:,.2f}",
            theme_font_size="Body",
            font_style="Bold",
            theme_text_color="Primary",
            halign='right',
            size_hint_x=0.4,
        )
        header.add_widget(amount_label)

        main_container.add_widget(header)

        # Quantity row if > 1
        if self.quantity > 1:
            qty_label = MDLabel(
                text=f"Qty: {self.quantity}",
                theme_font_size="Caption",
                theme_text_color="Secondary",
                halign='left',
                size_hint_y=None,
                height='20dp',
            )
            main_container.add_widget(qty_label)

        # Assigned participants row
        if self.assignments:
            assign_container = MDBoxLayout(
                orientation='horizontal',
                spacing='4dp',
                size_hint_y=None,
                height='36dp',
                padding=('0dp', '4dp'),
            )

            assign_label = MDLabel(
                text="Split with:",
                theme_font_size="Caption",
                theme_text_color="Secondary",
                halign='left',
                size_hint_x=None,
                width='70dp',
            )
            assign_container.add_widget(assign_label)

            for assignment in self.assignments:
                participant = self._get_participant(assignment.get('participant_id', 0))
                if participant:
                    chip = MDChip(
                        MDChipText(text=participant.get('name', '?')),
                        style="assist",
                        size_hint_x=None,
                        width='auto',
                    )
                    assign_container.add_widget(chip)

            main_container.add_widget(assign_container)

        # Unassigned warning
        unassigned = self._get_unassigned_amount()
        if unassigned > 0 and not self.assignments:
            warning = MDLabel(
                text=f"⚠ Unassigned: ₦{unassigned:,.2f}",
                theme_font_size="Caption",
                theme_text_color="Error",
                halign='left',
                size_hint_y=None,
                height='20dp',
            )
            main_container.add_widget(warning)

        # Disputed warning
        if self.disputed:
            disputed_label = MDLabel(
                text="⚠ This item is disputed",
                theme_font_size="Caption",
                theme_text_color="Error",
                halign='left',
                size_hint_y=None,
                height='20dp',
            )
            main_container.add_widget(disputed_label)

        # Action buttons
        actions = MDBoxLayout(
            orientation='horizontal',
            spacing='8dp',
            size_hint_y=None,
            height='36dp',
            padding=('0dp', '8dp', '0dp', '0dp'),
        )

        if self.on_assign:
            assign_btn = MDButton(
                MDButtonText(text="Assign"),
                style="text",
                theme_width="custom",
                width='80dp',
                on_release=lambda x: self.on_assign(self.item_id) if self.on_assign else None,
            )
            actions.add_widget(assign_btn)

        if self.on_edit:
            edit_btn = MDButton(
                MDButtonText(text="Edit"),
                style="text",
                theme_width="custom",
                width='60dp',
                on_release=lambda x: self.on_edit(self.item_id) if self.on_edit else None,
            )
            actions.add_widget(edit_btn)

        if self.on_delete:
            delete_btn = MDButton(
                MDButtonText(text="Delete"),
                style="text",
                theme_text_color="Error",
                theme_width="custom",
                width='70dp',
                on_release=lambda x: self.on_delete(self.item_id) if self.on_delete else None,
            )
            actions.add_widget(delete_btn)

        main_container.add_widget(actions)

        # Set container height
        main_container.height = main_container.minimum_height
        self.height = main_container.minimum_height + 24

        self.add_widget(main_container)

    def _get_participant(self, participant_id: int):
        """Get participant by ID."""
        for p in self.participants:
            if p.get('id') == participant_id:
                return p
        return None

    def _get_unassigned_amount(self) -> float:
        """Calculate unassigned amount."""
        assigned = sum(a.get('share_percent', 0) / 100 * self.amount for a in self.assignments)
        return self.amount - assigned

    def on_description(self, instance, value):
        self._build_ui()

    def on_amount(self, instance, value):
        self._build_ui()

    def on_assignments(self, instance, value):
        self._build_ui()

    def on_participants(self, instance, value):
        self._build_ui()
