"""Brand logo mark at hero / header / hub sizes."""

from __future__ import annotations

from typing import Literal

from slumber.ui.theme import BRAND_LIGHT, LOGO_SIZE

LogoSize = Literal["hero", "header", "hub"]


def logo_mark(
    logo_url: str | None,
    *,
    size: LogoSize = "header",
    fallback_icon: str = "nights_stay",
) -> None:
    """Render the brand logo image, or a fallback icon when no URL is set.

    Args:
        logo_url: Served logo URL, or ``None`` for the icon fallback.
        size: One of ``hero``, ``header``, or ``hub`` (see :data:`LOGO_SIZE`).
        fallback_icon: Quasar/Material icon name when *logo_url* is missing.
    """
    from nicegui import ui

    dimension = LOGO_SIZE[size]
    if logo_url:
        ui.image(logo_url).style(
            f"width: {dimension}; height: {dimension}; object-fit: contain;"
        ).classes("rounded-lg")
    else:
        ui.icon(fallback_icon, size=dimension).classes(f"text-[{BRAND_LIGHT}]")
