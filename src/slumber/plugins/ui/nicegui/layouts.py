"""Reusable viewport layouts for NiceGUI participant pages."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from nicegui import ui

from slumber.plugins.ui.nicegui.renderers import render_powered_by


@contextmanager
def centered_fullscreen_layout(
    *,
    content_gap: str | None = "gap-2",
    outer_classes: str = "",
) -> Generator[None, None, None]:
    """Stack: main area (vertically centered) + attribution footer.

    The inner column uses ``flex-1`` and ``justify-center`` so the main block stays
    centered; the footer is rendered below via :func:`render_powered_by` (see
    ``footer.py`` for shared padding).

    Args:
        content_gap: Optional Tailwind gap class for the main column (e.g.
            ``gap-2``). Use ``None`` when children use explicit margins.
        outer_classes: Extra classes on the outer column (e.g. ``pt-16`` for top
            inset on the sleep hub).
    """

    outer = f"w-full h-screen flex flex-col items-center {outer_classes}".strip()
    inner_parts = [
        "flex-1",
        "w-full",
        "min-h-0",
        "justify-center",
        "items-center",
    ]
    if content_gap:
        inner_parts.append(content_gap)
    with ui.column().classes(outer):
        with ui.column().classes(" ".join(inner_parts)):
            yield
        render_powered_by()
