"""Confirm dialog helper."""

from __future__ import annotations

from slumber.ui.theme import SECONDARY, SURFACE, SURFACE_BORDER
from slumber.ui.widgets.buttons import outline_button, primary_button


async def confirm_dialog(*, title: str, message: str) -> bool:
    """Show a modal confirm dialog and return whether the user confirmed.

    Args:
        title: Dialog heading.
        message: Body text.

    Returns:
        ``True`` if Confirm was pressed, ``False`` if Cancel or dismissed.
    """
    from nicegui import ui

    with (
        ui.dialog() as dialog,
        ui.card()
        .classes(f"px-6 py-5 bg-[{SURFACE}] border border-[{SURFACE_BORDER}]")
        .props("flat bordered"),
    ):
        ui.label(title).classes("text-h6 font-bold")
        ui.label(message).classes(f"text-body1 text-[{SECONDARY}] mt-1")
        with ui.row().classes("justify-end w-full mt-4 gap-2"):
            outline_button("Cancel", on_click=lambda: dialog.submit(False))
            primary_button("Confirm", on_click=lambda: dialog.submit(True))
    return bool(await dialog)
