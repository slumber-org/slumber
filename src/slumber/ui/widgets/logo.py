"""Brand logo mark at hero / header / hub sizes."""

from __future__ import annotations

from typing import Literal

from slumber.ui.theme import BRAND, LOGO_SIZE

LogoSize = Literal["hero", "header", "hub"]


def logo_mark(
    logo_url: str | None,
    *,
    size: LogoSize = "header",
    fallback_icon: str = "nights_stay",
) -> None:
    """Render the brand logo image, or a fallback icon when no URL is set.

    The size sets the image's height; its width follows the image's own
    proportions, so any logo shape works.

    Args:
        logo_url: Served logo URL, or ``None`` for the icon fallback.
        size: One of ``hero``, ``header``, or ``hub`` (see :data:`LOGO_SIZE`).
        fallback_icon: Quasar/Material icon name when *logo_url* is missing.
    """
    from nicegui import ui

    height = LOGO_SIZE[size]
    if logo_url:
        ui.element("img").props(f'src="{logo_url}" alt=""').style(
            f"height: {height}; width: auto; display: block; flex-shrink: 0;"
        )
    else:
        ui.icon(fallback_icon, size=height).classes(f"text-[{BRAND}]")
