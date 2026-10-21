"""Buttons: the plain variants, and buttons configured from study settings.

The visual styles live in ``slumber.ui.theme`` (``.slumber-btn*`` classes); the
plain helpers only pick the variant. ``action_button`` and ``toggle_button`` build
a button from ``ButtonSettings`` and call a function when it is pressed. Asking
"Are you sure?" first is a separate step: see ``with_confirmation`` in
``slumber.ui.widgets.dialog``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, model_validator

from slumber.ui.theme import add_component_css

if TYPE_CHECKING:
    from nicegui.element import Element
    from nicegui.elements.button import Button

ButtonVariant = Literal["primary", "secondary", "attention"]

TOGGLE_CSS = """
.slumber-toggle-button {
  display: flex;
  justify-content: center;
}
"""


def _make_button(
    label: str,
    *,
    variant: ButtonVariant,
    on_click: Callable[[], Any] | None,
    icon: str | None,
    enabled: bool,
    large: bool = False,
) -> Button:
    from nicegui import ui

    classes = f"slumber-btn slumber-btn-{variant}"
    if large:
        classes += " slumber-btn-lg"
    props = "unelevated no-caps" if variant == "primary" else "outline no-caps"
    button = (
        ui.button(label, icon=icon, on_click=on_click).props(props).classes(classes)
    )
    button.set_enabled(enabled)
    return button


def primary_button(
    label: str,
    *,
    on_click: Callable[[], Any] | None = None,
    icon: str | None = None,
    enabled: bool = True,
    large: bool = False,
) -> Button:
    """Render the main action button.

    Args:
        label: Button text.
        on_click: Click handler.
        icon: Optional Material icon name.
        enabled: Whether the button accepts clicks.
        large: Use the larger size.

    Returns:
        The NiceGUI button element.
    """
    return _make_button(
        label,
        variant="primary",
        on_click=on_click,
        icon=icon,
        enabled=enabled,
        large=large,
    )


def outline_button(
    label: str,
    *,
    on_click: Callable[[], Any] | None = None,
    icon: str | None = None,
    enabled: bool = True,
    attention: bool = False,
) -> Button:
    """Render an outline button, secondary by default or in the attention style.

    Args:
        label: Button text.
        on_click: Click handler.
        icon: Optional Material icon name.
        enabled: Whether the button accepts clicks.
        attention: When True, use the attention style.

    Returns:
        The NiceGUI button element.
    """
    return _make_button(
        label,
        variant="attention" if attention else "secondary",
        on_click=on_click,
        icon=icon,
        enabled=enabled,
    )


class ConfirmSettings(BaseModel):
    """What the question asked before a button acts says."""

    title: str | None = Field(
        default=None,
        description="Dialog heading. Defaults to the button's label with a question mark.",
    )
    message: str = Field(default="Are you sure?", description="Dialog text.")
    confirm_label: str = Field(
        default="Confirm", description="Label of the button that confirms."
    )
    cancel_label: str = Field(
        default="Cancel", description="Label of the button that cancels."
    )


def merge_button_defaults(value: object, defaults: dict[str, Any]) -> object:
    """Let a button be written as a label or as a partial mapping.

    Args:
        value: The settings as written: a label, a mapping or a ready model.
        defaults: Settings used for whatever the mapping leaves out.

    Returns:
        A mapping with the defaults filled in when *value* is a label or a
        mapping, otherwise *value* unchanged.
    """
    if isinstance(value, str):
        value = {"label": value}
    if isinstance(value, dict):
        return {**defaults, **value}
    return value


class ButtonSettings(BaseModel):
    """How a button looks and what it asks before acting."""

    label: str = Field(min_length=1, description="Text on the button.")
    style: ButtonVariant = Field(
        default="primary",
        description="Look of the button: primary, secondary or attention.",
    )
    confirm: bool | str | ConfirmSettings = Field(
        default=True,
        description="Ask before acting: true for a standard question, false for "
        "none, a text for the question, or a mapping to set the dialog's text.",
    )

    @model_validator(mode="before")
    @classmethod
    def _accept_a_label(cls, data: object) -> object:
        return merge_button_defaults(data, {})

    def confirmation(self) -> ConfirmSettings | None:
        """Work out what to ask before this button acts.

        Returns:
            The question with its defaults filled in, or ``None`` when the button
            acts on a single press.
        """
        confirm = self.confirm
        if confirm is False:
            return None
        if confirm is True:
            confirm = ConfirmSettings()
        elif isinstance(confirm, str):
            confirm = ConfirmSettings(message=confirm)
        title = confirm.title if confirm.title is not None else f"{self.label}?"
        return confirm.model_copy(update={"title": title})


async def _acted(callback: Callable[[], Any]) -> bool:
    """Run *callback* (sync or async); ``False`` means it chose not to act."""
    result = callback()
    if inspect.isawaitable(result):
        result = await result
    return result is not False


def _from_settings(
    settings: ButtonSettings, on_click: Callable[[], Any], large: bool
) -> Button:
    if settings.style == "primary":
        return primary_button(settings.label, on_click=on_click, large=large)
    return outline_button(
        settings.label, on_click=on_click, attention=settings.style == "attention"
    )


def action_button(
    settings: ButtonSettings, on_press: Callable[[], Any], *, large: bool = False
) -> Button:
    """Render a button from its settings that calls *on_press* when pressed.

    Args:
        settings: Label and style of the button.
        on_press: Called on every press. Wrap it with ``with_confirmation`` to ask
            first.
        large: Use the larger size for a primary button.

    Returns:
        The NiceGUI button element.
    """

    async def pressed() -> None:
        await _acted(on_press)

    return _from_settings(settings, pressed, large)


def toggle_button(
    first: ButtonSettings,
    second: ButtonSettings,
    *,
    on_first: Callable[[], Any],
    on_second: Callable[[], Any],
    large: bool = False,
) -> Element:
    """Render a button that swaps to the other one after each press that acted.

    It starts as *first*. Pressing it calls *on_first* and shows *second*;
    pressing that calls *on_second* and shows *first* again. A callback that
    returns ``False`` (for example a cancelled confirmation) leaves the button as
    it is.

    Args:
        first: The button shown at the start.
        second: The button shown after *first* acted.
        on_first: Called when *first* is pressed.
        on_second: Called when *second* is pressed.
        large: Use the larger size for primary buttons.

    Returns:
        The element holding whichever button is shown.
    """
    from nicegui import ui

    add_component_css(TOGGLE_CSS)
    holder = ui.element("div").classes("slumber-toggle-button")
    showing_second = False

    def show() -> None:
        holder.clear()
        with holder:
            _from_settings(second if showing_second else first, pressed, large)

    async def pressed() -> None:
        nonlocal showing_second
        acted = await _acted(on_second if showing_second else on_first)
        # The callback can end the phase, which removes this button with the rest.
        if not acted or holder.is_deleted:
            return
        showing_second = not showing_second
        show()

    show()
    return holder
