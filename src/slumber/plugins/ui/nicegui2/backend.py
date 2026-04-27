"""NiceGUI2 UI backend: schema-validated page-graph participant app."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from loguru import logger
from nicegui import ui

from slumber.plugins.ui.base import UIBackend
from slumber.plugins.ui.nicegui2.settings import NiceGUI2Settings
from slumber.plugins.ui.nicegui2.state import PageGraphState
from slumber.plugins.ui.nicegui2.router import PageRenderer

if TYPE_CHECKING:
    from pydantic import BaseModel

    from slumber.runtime.run import RunContext
    from slumber.schemas.condition import Condition
    from slumber.schemas.study import Study


class NiceGUI2Backend(UIBackend):
    """Participant UI backend for the page-graph based nicegui2 app.

    This backend currently validates ``study.ui.settings`` via ``NiceGUI2Settings``
    and asserts that each condition provides ``page_graph``. Full runtime execution
    wiring remains in progress.
    """

    ui_settings_model: ClassVar[type["BaseModel"] | None] = NiceGUI2Settings

    def run(
        self,
        study: "Study",
        condition: "Condition | None",
        context: "RunContext",
    ) -> None:
        """Run nicegui2 UI lifecycle.

        Args:
            study: Loaded study manifest.
            condition: The condition to run, or None to show welcome page for
                condition selection.
            context: Run context (IDs for study, participant, session, run).

        Raises:
            ValueError: If no conditions have page_graph.
        """
        assert isinstance(self._settings, NiceGUI2Settings)
        settings = self._settings

        # Check that at least one condition has a page_graph
        conditions_with_graph = [
            c for c in study.conditions if c.page_graph is not None
        ]
        if not conditions_with_graph:
            raise ValueError(
                "nicegui2 backend requires at least one condition with page_graph."
            )

        # Initialize page graph state with all conditions
        state = PageGraphState(
            study=study,
            conditions=study.conditions,
            context=context,
            ui_settings=settings,
        )

        logger.info(
            "Starting nicegui2 UI: study={!r} conditions_with_page_graph={}",
            study.study_id,
            len(conditions_with_graph),
        )

        @ui.page("/")
        def main_page() -> None:
            ui.query(".nicegui-content").classes("p-0 m-0")

            @ui.refreshable
            def page_content() -> None:
                renderer = PageRenderer(state, page_content.refresh)  # type: ignore[arg-type]
                renderer.render_current_page()

            page_content()

        ui.run(
            title=study.name,
            port=settings.port,
            reload=False,
            show=settings.show,
        )
