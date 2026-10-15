"""Surface card container."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from slumber.ui.theme import add_component_css

if TYPE_CHECKING:
    from nicegui.element import Element

CARD_CSS = """
.slumber-card { background: var(--slumber-surface); border-radius: 12px; }
"""


@contextmanager
def surface_card(*, classes: str = "") -> Generator[Element, None, None]:
    """Yield a flat, borderless card filled with the surface colour.

    Args:
        classes: Extra Tailwind/Quasar or component classes on the card.

    Yields:
        The card element, so callers can keep a reference to it.
    """
    from nicegui import ui

    add_component_css(CARD_CSS)
    with ui.element("div").classes(f"slumber-card {classes}".strip()) as card:
        yield card
