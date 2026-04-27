"""Welcome page - entry point. Loads content from markdown."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from nicegui import ui

from slumber.plugins.ui.nicegui2.shell.shell import render_shell
from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.pages.welcome.settings import WelcomeSettings
from slumber.plugins.ui.nicegui2.utils import load_markdown_content

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(
    state: PageGraphState,
    refresh: Callable[[], None],
    shell_cfg: ShellSettings | None = None,
    page_cfg: WelcomeSettings | None = None,
) -> None:
    """Render welcome page from markdown config."""
    if shell_cfg is None:
        shell_cfg = ShellSettings()
    if page_cfg is None:
        page_cfg = WelcomeSettings()

    title, subtitle, body_md = load_markdown_content(
        page_cfg, Path(__file__).parent, state.study_assets_dir
    )

    def on_button_click(condition_name: str | None) -> None:
        """Handle button click - select condition or use backend scheduling."""
        if condition_name is not None:
            # Explicit condition selected from config
            state.select_condition(condition_name)
        else:
            # No default condition configured - show condition selection UI
            # For now, select first available condition as fallback
            conditions_with_graph = [
                c for c in state.conditions if c.page_graph is not None
            ]
            if conditions_with_graph:
                state.select_condition(conditions_with_graph[0].name)
        # Trigger UI refresh to navigate to selected condition
        refresh()

    def content() -> None:
        with ui.column().classes("w-full h-full items-center justify-center p-8 gap-6"):
            # Title from markdown
            ui.label(title).classes("text-h3 font-bold text-center text-primary")

            # Subtitle from markdown
            if subtitle:
                ui.label(subtitle).classes("text-subtitle1 text-secondary text-center")

            # Body content card (full width with margins)
            with ui.card().classes(
                "w-full mx-8 bg-surface border border-secondary p-6 mt-4"
            ):
                ui.markdown(body_md).classes("w-full text-body1 text-primary")

            # Primary action button
            ui.button(
                page_cfg.button_text,
                icon=page_cfg.button_icon,
                on_click=lambda: on_button_click(page_cfg.default_condition),
            ).props(
                "size=lg rounded unelevated color=positive text-color=primary"
            ).classes("w-full max-w-md mt-6")

    render_shell(state, refresh, shell_cfg, content)  # type: ignore[arg-type]
