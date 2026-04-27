"""Farewell page - exit point. Loads content from markdown."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from nicegui import ui

from slumber.plugins.ui.nicegui2.shell.shell import render_shell
from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.pages.farewell.settings import FarewellSettings
from slumber.plugins.ui.nicegui2.utils import load_markdown_content

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(
    state: PageGraphState,
    refresh: Callable[[], None],
    shell_cfg: ShellSettings | None = None,
    page_cfg: FarewellSettings | None = None,
) -> None:
    """Render farewell page from markdown config."""
    if shell_cfg is None:
        shell_cfg = ShellSettings()
    if page_cfg is None:
        page_cfg = FarewellSettings()

    title, subtitle, body_md = load_markdown_content(
        page_cfg, Path(__file__).parent, state.study_assets_dir
    )

    def content() -> None:
        with ui.column().classes("w-full h-full items-center justify-center p-8 gap-6"):
            # Icon
            ui.icon(page_cfg.icon, size=page_cfg.icon_size).classes("text-positive")

            # Title from markdown
            ui.label(title).classes("text-h3 font-bold text-center text-primary")

            # Subtitle from markdown
            if subtitle:
                ui.label(subtitle).classes("text-subtitle1 text-secondary text-center")

            # Body content card (renders markdown with full formatting)
            with ui.card().classes(
                "w-full mx-8 bg-surface border border-secondary p-6 mt-4"
            ):
                ui.markdown(body_md).classes("w-full text-body1 text-primary")

            # Action button
            with ui.column().classes("w-full max-w-md gap-3 mt-6"):
                ui.button(
                    page_cfg.button_text,
                    icon=page_cfg.button_icon,
                    on_click=lambda: ui.notify(
                        f"TODO - shut down software in a graceful manner"
                    ),
                ).props(
                    "size=lg rounded unelevated color=positive text-color=primary"
                ).classes("w-full")

    render_shell(state, refresh, shell_cfg, content)  # type: ignore[arg-type]
