"""Surface card container for activity content."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from slumber.ui.theme import SURFACE, SURFACE_BORDER


@contextmanager
def surface_card(*, classes: str = "w-full px-6 py-5") -> Generator[None, None, None]:
    """Yield a flat bordered card using the surface token.

    Args:
        classes: Extra Tailwind/Quasar classes on the card.
    """
    from nicegui import ui

    with (
        ui.card()
        .classes(f"{classes} bg-[{SURFACE}] border border-[{SURFACE_BORDER}]")
        .props("flat bordered")
    ):
        yield
