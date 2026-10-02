"""Primary and outline CTA helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from slumber.ui.theme import CTA, NEGATIVE, TEXT


def primary_button(
    label: str,
    *,
    on_click: Callable[[], Any] | None = None,
    icon: str | None = None,
    enabled: bool = True,
) -> Any:
    """Render a filled CTA button (Quasar primary / amber).

    Args:
        label: Button text.
        on_click: Click handler.
        icon: Optional Material icon name.
        enabled: Whether the button accepts clicks.

    Returns:
        The NiceGUI button element.
    """
    from nicegui import ui

    button = (
        ui.button(label, icon=icon, on_click=on_click)
        .props("rounded unelevated color=primary")
        .style(f"letter-spacing: 0.5px; color: {TEXT};")
    )
    button.set_enabled(enabled)
    return button


def outline_button(
    label: str,
    *,
    on_click: Callable[[], Any] | None = None,
    icon: str | None = None,
    enabled: bool = True,
    attention: bool = False,
) -> Any:
    """Render an outline button; optional attention (destructive) styling.

    Args:
        label: Button text.
        on_click: Click handler.
        icon: Optional Material icon name.
        enabled: Whether the button accepts clicks.
        attention: When True, use the attention/negative colour.

    Returns:
        The NiceGUI button element.
    """
    from nicegui import ui

    color = NEGATIVE if attention else CTA
    button = (
        ui.button(label, icon=icon, on_click=on_click)
        .props("rounded outline")
        .style(f"letter-spacing: 0.5px; color: {color};")
    )
    button.set_enabled(enabled)
    return button
