# flet_app/components/summary_card.py
import flet as ft
from typing import Optional, Callable


class SummaryCard(ft.Container):
    """A card showing session totals and user's share."""

    def __init__(
        self,
        subtotal: float = 0.0,
        tax_amount: float = 0.0,
        tip_percent: float = 18.0,
        tip_amount: float = 0.0,
        total_amount: float = 0.0,
        my_share: float = 0.0,
        status: str = "active",
        on_lock: Optional[Callable] = None,
        on_settle: Optional[Callable] = None
    ):
        super().__init__()
        
        self.on_lock_callback = on_lock
        self.on_settle_callback = on_settle

        self.bgcolor = "white"
        self.border_radius = 16
        self.padding = 20

        self.content = self._build_content(status, total_amount, my_share, subtotal, tax_amount, tip_amount, tip_percent)

    def _build_content(self, status, total, my_share, subtotal, tax, tip, tip_pct):
        # Status badge
        status_colors = {
            'active': 'green',
            'locked': 'orange',
            'settled': 'blue'
        }
        status_texts = {
            'active': 'Active',
            'locked': 'Locked',
            'settled': 'Settled'
        }

        status_badge = ft.Container(
            content=ft.Text(status_texts.get(status, status), size=12, color="white", weight="bold"),
            bgcolor=status_colors.get(status, 'grey'),
            border_radius=12,
            padding=ft.Padding.only(left=12, right=12, top=4, bottom=4),
        )

        # Header
        header = ft.Row(
            controls=[
                ft.Text("Session Summary", size=18, weight="bold"),
                status_badge
            ],
            alignment="spaceBetween"
        )

        # Totals
        totals_row = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(f"${total:.2f}", size=28, weight="bold", color="indigo"),
                        ft.Text("Total", size=12, color="grey"),
                    ],
                    horizontal_alignment="center",
                ),
                ft.VerticalDivider(width=1, color="grey"),
                ft.Column(
                    controls=[
                        ft.Text(f"${my_share:.2f}", size=28, weight="bold", color="green"),
                        ft.Text("Your Share", size=12, color="grey"),
                    ],
                    horizontal_alignment="center",
                ),
            ],
            alignment="spaceAround"
        )

        # Breakdown
        breakdown = ft.Column(
            controls=[
                ft.Row(controls=[ft.Text("Subtotal", expand=True), ft.Text(f"${subtotal:.2f}")]),
                ft.Row(controls=[ft.Text("Tax", expand=True), ft.Text(f"${tax:.2f}")]),
                ft.Row(controls=[ft.Text(f"Tip ({tip_pct:.0f}%)", expand=True), ft.Text(f"${tip:.2f}")]),
                ft.Divider(height=4),
                ft.Row(controls=[ft.Text("Total", weight="bold", expand=True), ft.Text(f"${total:.2f}", weight="bold")]),
            ],
            spacing=4
        )

        # Action button
        action_btn = None
        if status == 'active':
            action_btn = ft.Button(
                "Lock Session",
                icon="lock",
                bgcolor="indigo",
                color="white",
                on_click=lambda e: self.on_lock_callback() if self.on_lock_callback else None,
                expand=True,
            )
        elif status == 'locked':
            action_btn = ft.Button(
                "Mark Settled",
                icon="check_circle",
                bgcolor="green",
                color="white",
                on_click=lambda e: self.on_settle_callback() if self.on_settle_callback else None,
                expand=True,
            )

        controls = [header, ft.Divider(height=16, color="transparent"), totals_row, ft.Divider(height=16, color="transparent"), breakdown]
        
        if action_btn:
            controls.append(ft.Divider(height=16, color="transparent"))
            controls.append(action_btn)

        return ft.Column(controls=controls, spacing=0)

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
        self.content = self._build_content(
            status or 'active',
            total_amount,
            my_share,
            subtotal,
            tax_amount,
            tip_amount,
            tip_percent
        )
