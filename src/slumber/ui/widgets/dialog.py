"""Confirm dialog helper."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from slumber.ui.theme import add_component_css
from slumber.ui.widgets.buttons import ButtonSettings, outline_button, primary_button

if TYPE_CHECKING:
    from nicegui.elements.button import Button
    from nicegui.elements.dialog import Dialog

DIALOG_CSS = """
.slumber-dialog {
  width: min(440px, 100%);
  max-width: 100%;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  padding: 24px;
  border-radius: 12px;
  background: var(--slumber-surface);
  color: var(--slumber-text);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
.slumber-dialog-title { font-size: 22px; line-height: 1.3; font-weight: 700; }
.slumber-dialog-message { color: var(--slumber-secondary); }
.slumber-dialog-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}
"""


def build_confirm_dialog(
    *,
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
) -> tuple[Dialog, Button, Button]:
    """Build the confirm dialog without opening it.

    Cancel is the button that has focus when the dialog opens, so an accidental
    key press does not confirm.

    Args:
        title: Dialog heading.
        message: Body text.
        confirm_label: Label of the button that confirms.
        cancel_label: Label of the button that cancels.

    Returns:
        The dialog and its Cancel and Confirm buttons.
    """
    from nicegui import ui

    add_component_css(DIALOG_CSS)
    with ui.dialog() as dialog, ui.card().classes("slumber-dialog"):
        ui.label(title).classes("slumber-dialog-title")
        ui.label(message).classes("slumber-dialog-message")
        with ui.element("div").classes("slumber-dialog-actions"):
            cancel = outline_button(cancel_label, on_click=lambda: dialog.submit(False))
            cancel.props["data-autofocus"] = True
            confirm = primary_button(
                confirm_label, on_click=lambda: dialog.submit(True)
            )
    return dialog, cancel, confirm


async def confirm_dialog(
    *,
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
) -> bool:
    """Show a modal confirm dialog and return whether the user confirmed.

    Args:
        title: Dialog heading.
        message: Body text.
        confirm_label: Label of the button that confirms.
        cancel_label: Label of the button that cancels.

    Returns:
        ``True`` if Confirm was pressed, ``False`` if Cancel or dismissed.
    """
    dialog, _, _ = build_confirm_dialog(
        title=title,
        message=message,
        confirm_label=confirm_label,
        cancel_label=cancel_label,
    )
    try:
        return bool(await dialog)
    finally:
        # Otherwise every answered dialog stays in the page. A phase change may
        # already have removed it with the rest of the body.
        if not dialog.is_deleted:
            dialog.delete()


def with_confirmation(
    settings: ButtonSettings, action: Callable[[], Any]
) -> Callable[[], Any]:
    """Make *action* ask the button's question first.

    Args:
        settings: The button the action belongs to; its ``confirm`` setting says
            what to ask, if anything.
        action: What to do once the participant confirms.

    Returns:
        A function to give to a button. It opens the confirm dialog, runs
        *action* (awaiting it if it is async) only on "Confirm", and returns
        ``False`` when the participant cancels or *action* itself returns
        ``False``, so that a toggle button stays as it is. When the button asks
        nothing, *action* is returned unchanged.
    """
    confirmation = settings.confirmation()
    if confirmation is None:
        return action

    async def confirmed_action() -> bool:
        confirmed = await confirm_dialog(
            title=confirmation.title or "",
            message=confirmation.message,
            confirm_label=confirmation.confirm_label,
            cancel_label=confirmation.cancel_label,
        )
        if not confirmed:
            return False
        result = action()
        if inspect.isawaitable(result):
            result = await result
        return result is not False

    return confirmed_action
