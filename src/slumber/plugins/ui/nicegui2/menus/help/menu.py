"""Help dropdown menu."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from nicegui import ui

from slumber.plugins.ui.nicegui2.utils import load_markdown_content
from slumber.plugins.ui.nicegui2.menus.help.settings import (
    HelpMenuSettings,
    HelpMenuItem,
)

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(
    state: PageGraphState,
    refresh: Callable[[], None],
    cfg: HelpMenuSettings,
) -> None:
    """Render the Help dropdown menu.

    Args:
        state: App state
        refresh: Function to refresh UI
        cfg: Help menu configuration
    """

    def show_item(item: HelpMenuItem) -> None:
        """Show dialog with markdown content for a help item."""
        _, _, md_content = load_markdown_content(
            item, Path(__file__).parent, state.study_assets_dir, parse=False
        )

        with (
            ui.dialog() as dialog,
            ui.card().classes("bg-surface p-6 w-full max-w-2xl"),
        ):
            with ui.column().classes("w-full gap-4"):
                ui.label(item.label).classes("text-h5 font-bold text-primary")
                with (
                    ui.card()
                    .classes(
                        "w-full bg-surface border border-secondary p-4 overflow-y-auto"
                    )
                    .style("max-height: 60vh;")
                ):
                    ui.markdown(md_content).classes(
                        "w-full text-body1 text-primary overflow-x-hidden"
                    )
                ui.button("Close", on_click=dialog.close).props(
                    "unelevated rounded color=secondary text-color=primary"
                ).classes("w-full max-w-xs self-center")
        dialog.open()

    with ui.button(cfg.label, icon="help").props("flat dense text-color=primary"):
        with ui.menu().classes("bg-surface border-secondary"):
            for item in cfg.items:
                ui.menu_item(item.label, lambda i=item: show_item(i)).classes(
                    "text-primary"
                )
