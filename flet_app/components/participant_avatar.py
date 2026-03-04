# flet_app/components/participant_avatar.py
import flet as ft
from typing import Optional, Callable


class ParticipantAvatar(ft.Container):
    """A clickable participant avatar."""

    def __init__(
        self,
        participant: dict,
        is_me: bool = False,
        on_click: Optional[Callable] = None
    ):
        super().__init__()
        self.participant = participant
        self.is_me = is_me

        # Create avatar with initial
        initial = participant['name'][0].upper() if participant['name'] else "?"
        
        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text(initial, color="white", weight="bold"),
                    bgcolor=participant.get('color', '#2196F3'),
                    width=48,
                    height=48,
                    border_radius=24,
                    alignment="center",
                ),
                ft.Text(participant['name'], size=11, text_align="center", no_wrap=True),
            ],
            horizontal_alignment="center",
            spacing=4
        )

        if on_click:
            self.on_click = on_click

    def set_selected(self, selected: bool):
        self.content.controls[0].border = ft.border.all(3, "blue") if selected else None


class ParticipantsRow(ft.Row):
    """Horizontal scrollable row of participant avatars."""

    def __init__(
        self,
        participants: list,
        my_id: Optional[int] = None,
        on_participant_click: Optional[Callable] = None
    ):
        avatars = []
        for p in participants:
            avatar = ParticipantAvatar(
                participant=p,
                is_me=(p['id'] == my_id),
                on_click=lambda e, pid=p['id']: self._handle_click(pid) if on_participant_click else None
            )
            avatars.append(avatar)

        super().__init__(
            controls=avatars,
            scroll="auto",
            spacing=10,
        )
        self.on_participant_click = on_participant_click

    def _handle_click(self, participant_id: int):
        if self.on_participant_click:
            self.on_participant_click(participant_id)
