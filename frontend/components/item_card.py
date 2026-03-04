# frontend/components/item_card.py
import flet as ft
from typing import Optional, Callable, List, Dict
from frontend.state import state
from frontend.api_client import api_client


class ItemCard(ft.Container):
    """
    A card component displaying a bill item with assignments.

    Supports drag-and-drop for participant assignment.
    """

    def __init__(
        self,
        item_data: dict,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        page: Optional[ft.Page] = None
    ):
        """
        Initialize item card.

        Args:
            item_data: Dict with id, description, amount, quantity, is_disputed
            on_edit: Optional edit handler
            on_delete: Optional delete handler
            page: Flet page reference
        """
        super().__init__()
        self.item = item_data
        self.page = page
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete

        # Container styling
        self.bgcolor = ft.colors.WHITE
        self.border_radius = 12
        self.padding = 16
        self.margin = ft.margin.only(bottom=8)
        self.shadow = ft.BoxShadow(
            blur_radius=8,
            color=ft.colors.BLACK12,
            offset=ft.Offset(0, 2)
        )

        # Add border for disputed items
        if item_data.get('is_disputed'):
            self.border = ft.border.all(2, ft.colors.ORANGE)
            self.bgcolor = ft.colors.ORANGE_50

        # Build the card content
        self.content = self._build_content()

    def _build_content(self) -> ft.Column:
        """Build the card's content."""
        # Header row with description and amount
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            self.item['description'],
                            size=16,
                            weight=ft.FontWeight.W_500,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Text(
                            f"${self.item['amount']:.2f}",
                            size=14,
                            color=ft.colors.GREY_700
                        ),
                    ],
                    expand=True
                ),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.WARNING_ROUNDED if self.item.get('is_disputed') else ft.icons.EDIT,
                            icon_color=ft.colors.ORANGE if self.item.get('is_disputed') else ft.colors.GREY_500,
                            icon_size=20,
                            on_click=self._on_edit_click,
                            tooltip="Disputed" if self.item.get('is_disputed') else "Edit"
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE,
                            icon_color=ft.colors.RED_400,
                            icon_size=20,
                            on_click=self._on_delete_click,
                            tooltip="Delete"
                        )
                    ]
                )
            ]
        )

        # Assignment chips row
        self.assignment_chips = self._build_assignment_chips()

        # Drag target for assignment
        drag_target = ft.DragTarget(
            content=ft.Container(
                content=self.assignment_chips if self.assignment_chips.controls else ft.Text(
                    "Drag participant here to assign",
                    size=12,
                    color=ft.colors.GREY_400,
                    italic=True
                ),
                bgcolor=ft.colors.BLUE_GREY_50,
                border_radius=8,
                padding=10,
                border=ft.border.all(1, ft.colors.BLUE_GREY_200)
            ),
            group="participant",
            on_accept=self._on_assign_dropped,
            on_will_accept=self._on_will_accept,
            on_leave=self._on_leave
        )

        return ft.Column(
            controls=[
                header,
                ft.Divider(height=8, color=ft.colors.TRANSPARENT),
                drag_target
            ],
            spacing=0
        )

    def _build_assignment_chips(self) -> ft.Row:
        """Build chips showing current assignments."""
        chips_row = ft.Row(wrap=True, spacing=5)

        assignments = state.get_item_assignments(self.item['id'])

        for assignment in assignments:
            participant = state.get_participant_by_id(assignment['participant_id'])
            if participant:
                chip = ft.Chip(
                    label=ft.Text(
                        f"{participant['name']} {assignment['share_percent']:.0f}%",
                        size=12,
                        color=ft.colors.WHITE
                    ),
                    bgcolor=participant.get('color', '#2196F3'),
                    delete_icon=ft.icons.CLOSE,
                    on_delete=lambda e, aid=assignment['id']: self._remove_assignment(aid)
                )
                chips_row.controls.append(chip)

        return chips_row

    def _on_edit_click(self, e):
        """Handle edit button click."""
        if self.on_edit_callback:
            self.on_edit_callback(self.item)

    def _on_delete_click(self, e):
        """Handle delete button click."""
        if self.on_delete_callback:
            self.on_delete_callback(self.item)

    async def _on_assign_dropped(self, e):
        """Handle participant dropped for assignment."""
        try:
            participant_id = int(e.data)
            await api_client.assign_item(
                self.item['id'],
                {
                    "participant_id": participant_id,
                    "share_percent": 100.0
                }
            )
        except Exception as ex:
            print(f"Assignment error: {ex}")
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Failed to assign: {str(ex)}"),
                    bgcolor=ft.colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()

    def _on_will_accept(self, e):
        """Visual feedback when dragging over."""
        e.control.content.bgcolor = ft.colors.BLUE_100
        e.control.content.border = ft.border.all(2, ft.colors.BLUE)
        e.control.update()

    def _on_leave(self, e):
        """Reset visual when dragging leaves."""
        e.control.content.bgcolor = ft.colors.BLUE_GREY_50
        e.control.content.border = ft.border.all(1, ft.colors.BLUE_GREY_200)
        e.control.update()

    async def _remove_assignment(self, assignment_id: int):
        """Remove an assignment."""
        try:
            await api_client.remove_assignment(assignment_id)
        except Exception as ex:
            print(f"Remove assignment error: {ex}")

    def update_item(self, item_data: dict):
        """Update item data and refresh display."""
        self.item = item_data
        self.content = self._build_content()
        if self.page:
            self.update()


class ItemList(ft.Column):
    """
    A scrollable list of item cards.
    """

    def __init__(
        self,
        items: List[dict],
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        page: Optional[ft.Page] = None
    ):
        """
        Initialize item list.

        Args:
            items: List of item dicts
            on_edit: Optional edit handler
            on_delete: Optional delete handler
            page: Flet page reference
        """
        item_cards = [
            ItemCard(
                item_data=item,
                on_edit=on_edit,
                on_delete=on_delete,
                page=page
            )
            for item in items
        ]

        super().__init__(
            controls=item_cards,
            scroll=ft.ScrollMode.AUTO,
            spacing=0
        )

    def update_items(self, items: List[dict]):
        """Update the list of items."""
        self.controls = [
            ItemCard(
                item_data=item,
                page=self.page
            )
            for item in items
        ]
        if self.page:
            self.update()
