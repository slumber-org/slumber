"""Primary and outline button helpers.

The visual styles live in ``slumber.ui.theme`` (``.slumber-btn*`` classes); these
helpers only pick the variant.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from nicegui.elements.button import Button

ButtonVariant = Literal["primary", "secondary", "attention"]


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
