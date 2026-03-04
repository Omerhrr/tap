# flet_app/components/item_card.py
import flet as ft
from typing import Optional, Callable, List

from state import state
from api_client import api_client


class ItemCard(ft.Container):
    """A card component displaying a bill item."""

    def __init__(
        self,
        item_data: dict,
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        page: Optional[ft.Page] = None
    ):
        super().__init__()
        self.item = item_data
        self._page = page
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete

        self.bgcolor = "white"
        self.border_radius = 12
        self.padding = 16
        self.margin = ft.margin.only(bottom=8)

        if item_data.get('is_disputed'):
            self.border = ft.border.all(2, "orange")
            self.bgcolor = "#FFF3E0"

        self.content = self._build_content()

    def _build_content(self) -> ft.Column:
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(self.item.get('description', 'Item'), size=16, weight="w500"),
                        ft.Text(f"${self.item.get('amount', 0):.2f}", size=14, color="grey"),
                    ],
                    expand=True
                ),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon="warning" if self.item.get('is_disputed') else "edit",
                            icon_color="orange" if self.item.get('is_disputed') else "grey",
                            icon_size=20,
                            on_click=self._on_edit_click,
                        ),
                        ft.IconButton(
                            icon="delete_outline",
                            icon_color="red",
                            icon_size=20,
                            on_click=self._on_delete_click,
                        )
                    ]
                )
            ]
        )

        assignment_area = ft.Container(
            content=ft.Text("Tap to assign", size=12, color="grey", italic=True),
            bgcolor="#ECEFF1",
            border_radius=8,
            padding=10,
        )

        return ft.Column(
            controls=[header, ft.Divider(height=8, color="transparent"), assignment_area],
            spacing=0
        )

    def _on_edit_click(self, e):
        if self.on_edit_callback:
            self.on_edit_callback(self.item)

    def _on_delete_click(self, e):
        if self.on_delete_callback:
            self.on_delete_callback(self.item)


class ItemList(ft.Column):
    """A scrollable list of item cards."""

    def __init__(
        self,
        items: List[dict],
        on_edit: Optional[Callable] = None,
        on_delete: Optional[Callable] = None,
        page: Optional[ft.Page] = None
    ):
        self._page = page
        item_cards = [
            ItemCard(item_data=item, on_edit=on_edit, on_delete=on_delete, page=page)
            for item in items
        ]

        super().__init__(
            controls=item_cards,
            scroll="auto",
            spacing=0
        )

    def update_items(self, items: List[dict]):
        self.controls = [
            ItemCard(item_data=item, page=self._page)
            for item in items
        ]
        if self._page:
            self.update()
