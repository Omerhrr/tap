# frontend/components/summary_card.py
import flet as ft
from typing import Optional, Callable


class SummaryCard(ft.Container):
    """
    A card showing session totals and user's share.
    """

    def __init__(
        self,
        subtotal: float = 0.0,
        tax_amount: float = 0.0,
        tip_percent: float = 18.0,
        tip_amount: float = 0.0,
        total_amount: float = 0.0,
        my_share: float = 0.0,
        currency: str = "USD",
        status: str = "active",
        on_lock: Optional[Callable] = None,
        on_settle: Optional[Callable] = None
    ):
        """
        Initialize summary card.

        Args:
            subtotal: Session subtotal
            tax_amount: Tax amount
            tip_percent: Tip percentage
            tip_amount: Tip amount
            total_amount: Total amount
            my_share: Current user's share
            currency: Currency code
            status: Session status (active, locked, settled)
            on_lock: Lock button handler
            on_settle: Settle button handler
        """
        super().__init__()

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.tip_percent = tip_percent
        self.tip_amount = tip_amount
        self.total_amount = total_amount
        self.my_share = my_share
        self.currency = currency
        self.status = status
        self.on_lock_callback = on_lock
        self.on_settle_callback = on_settle

        # Container styling
        self.bgcolor = ft.colors.WHITE
        self.border_radius = 16
        self.padding = 20
        self.shadow = ft.BoxShadow(
            blur_radius=12,
            color=ft.colors.BLACK12,
            offset=ft.Offset(0, 4)
        )

        self.content = self._build_content()

    def _build_content(self) -> ft.Column:
        """Build the card's content."""
        # Status badge
        status_color = {
            'active': ft.colors.GREEN,
            'locked': ft.colors.ORANGE,
            'settled': ft.colors.BLUE
        }.get(self.status, ft.colors.GREY)

        status_text = {
            'active': 'Active',
            'locked': 'Locked',
            'settled': 'Settled'
        }.get(self.status, self.status.title())

        status_badge = ft.Container(
            content=ft.Text(
                status_text,
                size=12,
                color=ft.colors.WHITE,
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=status_color,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=12, vertical=4)
        )

        # Header row
        header = ft.Row(
            controls=[
                ft.Text(
                    "Session Summary",
                    size=18,
                    weight=ft.FontWeight.BOLD
                ),
                status_badge
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Total and share row
        totals_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            f"${self.total_amount:.2f}",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.INDIGO
                        ),
                        ft.Text(
                            "Total",
                            size=12,
                            color=ft.colors.GREY_600
                        )
                    ]
                ),
                ft.VerticalDivider(width=1, color=ft.colors.GREY_300),
                ft.Column(
                    controls=[
                        ft.Text(
                            f"${self.my_share:.2f}",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREEN_700
                        ),
                        ft.Text(
                            "Your Share",
                            size=12,
                            color=ft.colors.GREY_600
                        )
                    ]
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        )

        # Breakdown
        breakdown = ft.Column(
            controls=[
                ft.Divider(height=16, color=ft.colors.TRANSPARENT),
                _BreakdownRow("Subtotal", self.subtotal),
                _BreakdownRow("Tax", self.tax_amount),
                _BreakdownRow(f"Tip ({self.tip_percent:.0f}%)", self.tip_amount),
                ft.Divider(height=8, color=ft.colors.GREY_300),
                _BreakdownRow("Total", self.total_amount, is_total=True)
            ],
            spacing=4
        )

        # Action buttons
        action_buttons = ft.Row(
            controls=[],
            spacing=10
        )

        if self.status == 'active':
            action_buttons.controls.append(
                ft.ElevatedButton(
                    "Lock Session",
                    icon=ft.icons.LOCK,
                    bgcolor=ft.colors.INDIGO,
                    color=ft.colors.WHITE,
                    on_click=self._on_lock_click,
                    expand=True
                )
            )
        elif self.status == 'locked':
            action_buttons.controls.append(
                ft.ElevatedButton(
                    "Mark Settled",
                    icon=ft.icons.CHECK_CIRCLE,
                    bgcolor=ft.colors.GREEN,
                    color=ft.colors.WHITE,
                    on_click=self._on_settle_click,
                    expand=True
                )
            )

        return ft.Column(
            controls=[
                header,
                ft.Divider(height=16, color=ft.colors.TRANSPARENT),
                totals_row,
                breakdown,
                action_buttons
            ],
            spacing=0
        )

    def _on_lock_click(self, e):
        """Handle lock button click."""
        if self.on_lock_callback:
            self.on_lock_callback()

    def _on_settle_click(self, e):
        """Handle settle button click."""
        if self.on_settle_callback:
            self.on_settle_callback()

    def update_summary(
        self,
        subtotal: float,
        tax_amount: float,
        tip_percent: float,
        tip_amount: float,
        total_amount: float,
        my_share: float,
        status: str = None
    ):
        """Update the summary values."""
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.tip_percent = tip_percent
        self.tip_amount = tip_amount
        self.total_amount = total_amount
        self.my_share = my_share

        if status:
            self.status = status

        self.content = self._build_content()


class _BreakdownRow(ft.Row):
    """A row in the breakdown section."""

    def __init__(self, label: str, amount: float, is_total: bool = False):
        super().__init__(
            controls=[
                ft.Text(
                    label,
                    size=14 if is_total else 13,
                    weight=ft.FontWeight.BOLD if is_total else ft.FontWeight.NORMAL,
                    color=ft.colors.BLACK if is_total else ft.colors.GREY_700,
                    expand=True
                ),
                ft.Text(
                    f"${amount:.2f}",
                    size=14 if is_total else 13,
                    weight=ft.FontWeight.BOLD if is_total else ft.FontWeight.NORMAL,
                    color=ft.colors.BLACK if is_total else ft.colors.GREY_700
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
