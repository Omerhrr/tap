# flet_app/components/session_view.py
import flet as ft
from typing import Optional, Callable
from state import state
from api_client import api_client
from components.participant_avatar import ParticipantsRow
from components.item_card import ItemList
from components.summary_card import SummaryCard


class SessionView(ft.Column):
    """
    Main session view component.

    Displays participants, items, and summary for a bill-splitting session.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.expand = True

        # Subscribe to state changes
        state.subscribe(self._on_state_change)

        # Build the initial view
        self.controls = self._build_controls()

    def _build_controls(self) -> list:
        """Build the view's controls."""
        # App bar
        app_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self._on_back_click
                    ),
                    ft.Text(
                        f"Session: {state.session_code}",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.QR_CODE,
                        on_click=self._on_qr_click,
                        tooltip="Show QR Code"
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.symmetric(horizontal=8, vertical=4)
        )

        # Participants row
        self.participants_row = ParticipantsRow(
            participants=state.participants,
            my_id=state.participant_id
        )

        participants_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Participants", size=14, color=ft.Colors.GREY_600),
                    self.participants_row
                ],
                spacing=8
            ),
            bgcolor=ft.Colors.GREY_50,
            padding=12,
            border_radius=ft.border_radius.all(8)
        )

        # Summary card
        self.summary_card = SummaryCard(
            subtotal=state.subtotal,
            tax_amount=state.tax_amount,
            tip_percent=state.tip_percent,
            tip_amount=state.tip_amount,
            total_amount=state.total_amount,
            my_share=state.get_my_share(),
            status=state.status,
            on_lock=self._on_lock_session,
            on_settle=self._on_settle_session
        )

        # Action buttons
        action_buttons = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Scan Receipt",
                    icon=ft.icons.CAMERA_ALT,
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    on_click=self._on_scan_click,
                    expand=True
                ),
                ft.ElevatedButton(
                    "Add Item",
                    icon=ft.icons.ADD,
                    bgcolor=ft.Colors.GREEN,
                    color=ft.Colors.WHITE,
                    on_click=self._on_add_item_click,
                    expand=True
                )
            ],
            spacing=10
        )

        # Items header
        items_header = ft.Row(
            controls=[
                ft.Text(
                    "Bill Items",
                    size=16,
                    weight=ft.FontWeight.BOLD
                ),
                ft.ElevatedButton(
                    "Auto Split",
                    icon=ft.icons.CALL_SPLIT,
                    on_click=self._on_auto_split_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.INDIGO_50,
                        color=ft.Colors.INDIGO
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Items list
        self.items_list = ItemList(
            items=state.items,
            on_edit=self._on_edit_item,
            on_delete=self._on_delete_item,
            page=self._page
        )

        # Main content column
        content = ft.Column(
            controls=[
                participants_container,
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                self.summary_card,
                ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                action_buttons,
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                items_header,
                self.items_list
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=8
        )

        return [
            app_bar,
            content
        ]

    def _on_state_change(self):
        """Handle state change notification."""
        # Update participants
        self.participants_row = ParticipantsRow(
            participants=state.participants,
            my_id=state.participant_id
        )

        # Update summary
        self.summary_card.update_summary(
            subtotal=state.subtotal,
            tax_amount=state.tax_amount,
            tip_percent=state.tip_percent,
            tip_amount=state.tip_amount,
            total_amount=state.total_amount,
            my_share=state.get_my_share(),
            status=state.status
        )

        # Update items list
        self.items_list.update_items(state.items)

        if self._page:
            self._page.update()

    def _on_back_click(self, e):
        """Handle back button click."""
        # Navigate back to home
        pass

    def _on_qr_click(self, e):
        """Handle QR code button click."""
        # Show QR code dialog
        self._show_qr_dialog()

    def _on_scan_click(self, e):
        """Handle scan receipt button click."""
        # Show scan dialog
        self._show_scan_dialog()

    def _on_add_item_click(self, e):
        """Handle add item button click."""
        # Show add item dialog
        self._show_add_item_dialog()

    def _on_auto_split_click(self, e):
        """Handle auto split button click."""
        # Call API to auto-assign
        import asyncio
        asyncio.create_task(self._auto_assign())

    async def _auto_assign(self):
        """Auto-assign items equally."""
        try:
            data = await api_client.auto_assign(state.session_id)
            state.update_session(data)
        except Exception as ex:
            print(f"Auto-assign error: {ex}")

    async def _on_lock_session(self):
        """Handle lock session."""
        try:
            data = await api_client.lock_session(state.session_id)
            state.status = data.get('status', 'locked')
            state.notify()
        except Exception as ex:
            print(f"Lock error: {ex}")

    async def _on_settle_session(self):
        """Handle settle session."""
        try:
            data = await api_client.settle_session(state.session_id)
            state.status = data.get('status', 'settled')
            state.notify()
        except Exception as ex:
            print(f"Settle error: {ex}")

    def _on_edit_item(self, item: dict):
        """Handle edit item."""
        self._show_edit_item_dialog(item)

    def _on_delete_item(self, item: dict):
        """Handle delete item."""
        import asyncio
        asyncio.create_task(self._delete_item(item['id']))

    async def _delete_item(self, item_id: int):
        """Delete an item."""
        try:
            await api_client.delete_item(item_id)
            state.items = [i for i in state.items if i['id'] != item_id]
            state.notify()
        except Exception as ex:
            print(f"Delete error: {ex}")

    def _show_qr_dialog(self):
        """Show QR code dialog."""
        # Generate QR code for session
        qr_dialog = ft.AlertDialog(
            title=ft.Text("Join Session"),
            content=ft.Column(
                controls=[
                    ft.Text(f"Session Code: {state.session_code}"),
                    ft.Text("Share this code with others to join"),
                    ft.Container(
                        content=ft.Text(
                            state.session_code,
                            size=48,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO
                        ),
                        alignment=ft.alignment.center,
                        padding=20
                    )
                ],
                tight=True
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog())
            ]
        )
        self._page.dialog = qr_dialog
        qr_dialog.open = True
        self._page.update()

    def _show_scan_dialog(self):
        """Show scan receipt dialog."""
        # File picker for image upload
        file_picker = ft.FilePicker(on_result=self._on_file_picked)

        scan_dialog = ft.AlertDialog(
            title=ft.Text("Scan Receipt"),
            content=ft.Column(
                controls=[
                    ft.Text("Upload a photo of your receipt"),
                    ft.ElevatedButton(
                        "Choose Image",
                        icon=ft.icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files(
                            allowed_extensions=["jpg", "jpeg", "png", "heic"]
                        )
                    )
                ],
                tight=True
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog())
            ]
        )

        self._page.overlay.append(file_picker)
        self._page.dialog = scan_dialog
        scan_dialog.open = True
        self._page.update()

    async def _on_file_picked(self, e):
        """Handle file picker result."""
        if e.files:
            # Process the uploaded image
            import asyncio

            file = e.files[0]
            # Read file and process
            # Note: In production, you'd read the actual file

            self._close_dialog()

            # Show processing indicator
            self._page.snack_bar = ft.SnackBar(
                content=ft.Text("Processing receipt..."),
                bgcolor=ft.Colors.BLUE
            )
            self._page.snack_bar.open = True
            self._page.update()

            try:
                # This would process the actual file in production
                # result = await api_client.process_receipt(file_bytes)
                pass
            except Exception as ex:
                print(f"OCR error: {ex}")

    def _show_add_item_dialog(self):
        """Show add item dialog."""
        description_field = ft.TextField(
            label="Description",
            autofocus=True
        )
        amount_field = ft.TextField(
            label="Amount",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        quantity_field = ft.TextField(
            label="Quantity",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER
        )

        add_dialog = ft.AlertDialog(
            title=ft.Text("Add Item"),
            content=ft.Column(
                controls=[
                    description_field,
                    amount_field,
                    quantity_field
                ],
                tight=True
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton(
                    "Add",
                    on_click=lambda e: self._add_item(
                        description_field.value,
                        float(amount_field.value or 0),
                        int(quantity_field.value or 1)
                    )
                )
            ]
        )
        self._page.dialog = add_dialog
        add_dialog.open = True
        self._page.update()

    async def _add_item(self, description: str, amount: float, quantity: int):
        """Add a new item."""
        if not description or amount <= 0:
            return

        try:
            import asyncio
            await api_client.add_item(
                state.session_id,
                {
                    "description": description,
                    "amount": amount,
                    "quantity": quantity
                }
            )
            self._close_dialog()
        except Exception as ex:
            print(f"Add item error: {ex}")

    def _show_edit_item_dialog(self, item: dict):
        """Show edit item dialog."""
        description_field = ft.TextField(
            label="Description",
            value=item.get('description', '')
        )
        amount_field = ft.TextField(
            label="Amount",
            value=str(item.get('amount', 0)),
            keyboard_type=ft.KeyboardType.NUMBER
        )

        edit_dialog = ft.AlertDialog(
            title=ft.Text("Edit Item"),
            content=ft.Column(
                controls=[
                    description_field,
                    amount_field
                ],
                tight=True
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton(
                    "Save",
                    on_click=lambda e: self._update_item(
                        item['id'],
                        description_field.value,
                        float(amount_field.value or 0)
                    )
                )
            ]
        )
        self._page.dialog = edit_dialog
        edit_dialog.open = True
        self._page.update()

    async def _update_item(self, item_id: int, description: str, amount: float):
        """Update an item."""
        try:
            import asyncio
            await api_client.update_item(
                item_id,
                {
                    "description": description,
                    "amount": amount
                }
            )
            self._close_dialog()
        except Exception as ex:
            print(f"Update item error: {ex}")

    def _close_dialog(self):
        """Close the current dialog."""
        self._page.dialog.open = False
        self._page.update()
