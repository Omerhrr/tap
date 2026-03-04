# frontend/components/participant_avatar.py
import flet as ft
from typing import Optional, Callable


class ParticipantAvatar(ft.Draggable):
    """
    A draggable participant avatar component.

    Used for assigning participants to items via drag-and-drop.
    """

    def __init__(
        self,
        participant: dict,
        is_me: bool = False,
        on_click: Optional[Callable] = None
    ):
        """
        Initialize participant avatar.

        Args:
            participant: Dict with id, name, color
            is_me: Whether this is the current user
            on_click: Optional click handler
        """
        self.participant = participant
        self.is_me = is_me

        # Create avatar
        avatar_content = ft.CircleAvatar(
            content=ft.Text(
                participant['name'][0].upper(),
                color=ft.colors.WHITE,
                weight=ft.FontWeight.BOLD,
                size=18
            ),
            bgcolor=participant.get('color', '#2196F3'),
            radius=24
        )

        # Add "me" indicator if needed
        if is_me:
            avatar_with_indicator = ft.Stack(
                controls=[
                    avatar_content,
                    ft.Container(
                        content=ft.Icon(
                            ft.icons.STAR,
                            size=12,
                            color=ft.colors.YELLOW
                        ),
                        alignment=ft.alignment.top_right,
                        padding=ft.padding.only(right=2, top=2)
                    )
                ],
                width=52,
                height=52
            )
        else:
            avatar_with_indicator = avatar_content

        # Create main content column
        content_column = ft.Column(
            controls=[
                avatar_with_indicator,
                ft.Text(
                    participant['name'],
                    size=11,
                    text_align=ft.TextAlign.CENTER,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            width=60
        )

        # Initialize as Draggable
        super().__init__(
            content=content_column,
            data=str(participant['id']),
            group="participant"
        )

        # Store click handler
        if on_click:
            self.on_click = on_click


class ParticipantChip(ft.Chip):
    """
    A chip showing participant assignment on an item.
    """

    def __init__(
        self,
        participant: dict,
        share_percent: float,
        on_delete: Optional[Callable] = None
    ):
        """
        Initialize participant chip.

        Args:
            participant: Dict with id, name, color
            share_percent: Percentage of item assigned
            on_delete: Optional delete handler
        """
        self.participant = participant

        super().__init__(
            label=ft.Text(
                f"{participant['name']} {share_percent:.0f}%",
                size=12,
                color=ft.colors.WHITE
            ),
            bgcolor=participant.get('color', '#2196F3'),
            delete_icon=ft.icons.CLOSE,
            on_delete=on_delete,
            padding=ft.padding.symmetric(horizontal=8, vertical=4)
        )


class ParticipantsRow(ft.Row):
    """
    Horizontal scrollable row of participant avatars.
    """

    def __init__(
        self,
        participants: list,
        my_id: Optional[int] = None,
        on_participant_click: Optional[Callable] = None
    ):
        """
        Initialize participants row.

        Args:
            participants: List of participant dicts
            my_id: Current user's participant ID
            on_participant_click: Optional click handler
        """
        avatars = []
        for p in participants:
            avatar = ParticipantAvatar(
                participant=p,
                is_me=(p['id'] == my_id),
                on_click=lambda e, pid=p['id']: on_participant_click(pid) if on_participant_click else None
            )
            avatars.append(avatar)

        super().__init__(
            controls=avatars,
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            wrap=False
        )
