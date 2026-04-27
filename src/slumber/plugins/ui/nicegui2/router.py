"""Page router for dynamic page rendering based on page_graph.

This module handles loading and rendering pages based on their type
(interaction, task_stepper, welcome, farewell).
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Callable

from loguru import logger

from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.utils import to_pascal_case

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState
    from slumber.plugins.ui.nicegui2.settings import NiceGUI2Settings
    from slumber.schemas.condition import PageNode, InteractionPage, TaskStepperPage


class PageRenderer:
    """Handles dynamic page rendering based on page_graph node types."""

    def __init__(self, state: PageGraphState, refresh: Callable[[], None]) -> None:
        """Initialize the page renderer.

        Args:
            state: The PageGraphState instance.
            refresh: Function to refresh the UI.
        """
        self.state = state
        self.refresh = refresh
        # Set the refresh callback on state so routing events trigger UI updates
        state.set_refresh_callback(refresh)

    def render_current_page(self) -> None:
        """Render the current page based on state.current_page_id."""
        page_id = self.state.get_current_page()

        # Handle special global pages (not in page_graph)
        if page_id == "welcome":
            self._render_welcome()
            return
        if page_id == "farewell":
            self._render_farewell()
            return

        # All other pages must be in page_graph
        page_node = self.state.page_graph.pages.get(page_id)
        if page_node is None:
            raise ValueError(f"Page {page_id!r} not found in page_graph.pages")

        if page_node.type == "interaction":
            self._render_interaction_page(page_id, page_node)
        elif page_node.type == "task_stepper":
            self._render_task_stepper_page(page_id, page_node)
        else:
            raise ValueError(f"Unknown page type: {page_node.type!r}")

    def _render_welcome(self) -> None:
        """Render the welcome page."""
        logger.info("Rendering welcome page")

        # Build shell config from settings
        shell_cfg = self._build_shell_config()

        # Import and render the welcome page
        try:
            page_module = importlib.import_module(
                "slumber.plugins.ui.nicegui2.pages.welcome.page"
            )
            settings_module = importlib.import_module(
                "slumber.plugins.ui.nicegui2.pages.welcome.settings"
            )
            welcome_cfg = settings_module.WelcomeSettings(
                default_condition=self.state.ui_settings.welcome.default_condition
            )

            if hasattr(page_module, "render"):
                page_module.render(self.state, self.refresh, shell_cfg, welcome_cfg)
            else:
                raise ImportError("welcome page has no render() function")
        except Exception as e:
            logger.error("Failed to load welcome page: {}", e)
            from nicegui import ui

            def content() -> None:
                with ui.column().classes("w-full h-full items-center justify-center"):
                    ui.label(f"Error loading welcome page: {e}").classes(
                        "text-negative"
                    )

            from slumber.plugins.ui.nicegui2.shell.shell import render_shell

            render_shell(self.state, self.refresh, shell_cfg, content)  # type: ignore[arg-type]

    def _render_interaction_page(self, page_id: str, page: InteractionPage) -> None:
        """Render an interaction page.

        Interaction pages are loaded dynamically from the pages/ directory
        based on the page_id. For example, page_id='sleep' loads from
        slumber.plugins.ui.nicegui2.pages.sleep.page.

        Args:
            page_id: The page ID (maps to pages/{page_id}/page.py).
            page: The InteractionPage definition.
        """
        logger.info("Rendering interaction page: {}", page_id)

        # Build shell config from settings
        shell_cfg = self._build_shell_config()

        # Try to load the page module dynamically
        try:
            page_module = importlib.import_module(
                f"slumber.plugins.ui.nicegui2.pages.{page_id}.page"
            )
            settings_module = importlib.import_module(
                f"slumber.plugins.ui.nicegui2.pages.{page_id}.settings"
            )
            settings_class_name = f"{to_pascal_case(page_id)}Settings"
            settings_class = getattr(settings_module, settings_class_name, None)
            page_cfg = settings_class() if settings_class else None

            if hasattr(page_module, "render"):
                page_module.render(self.state, self.refresh, shell_cfg, page_cfg)
            else:
                raise ImportError(f"{page_id} page has no render() function")
        except ImportError as e:
            logger.error("Failed to load interaction page {}: {}", page_id, e)
            # Show error in shell only, don't render placeholder UI
            from nicegui import ui

            def content() -> None:
                with ui.column().classes("w-full h-full items-center justify-center"):
                    ui.label(f"Error: Failed to load page '{page_id}'").classes(
                        "text-negative text-h5"
                    )

            from slumber.plugins.ui.nicegui2.shell.shell import render_shell

            render_shell(self.state, self.refresh, shell_cfg, content)  # type: ignore[arg-type]

    def _render_task_stepper_page(self, page_id: str, page: TaskStepperPage) -> None:
        """Render a task stepper page.

        Args:
            page_id: The page ID.
            page: The TaskStepperPage definition.
        """
        logger.info("Rendering task_stepper page: {}", page_id)

        # Build shell config from settings
        shell_cfg = self._build_shell_config()

        # Import and render the task_stepper page
        try:
            page_module = importlib.import_module(
                "slumber.plugins.ui.nicegui2.pages.task_stepper.page"
            )
            settings_module = importlib.import_module(
                "slumber.plugins.ui.nicegui2.pages.task_stepper.settings"
            )

            # Build task stepper settings from page definition
            task_config = settings_module.TaskStepperSettings(
                tasks=[task.type for task in page.tasks],
                task_settings={task.type: task.settings or {} for task in page.tasks},
            )

            if hasattr(page_module, "render"):
                # Wrap the refresh to trigger navigation on completion
                original_refresh = self.refresh

                def wrapped_refresh() -> None:
                    original_refresh()

                page_module.render(self.state, wrapped_refresh, shell_cfg, task_config)
            else:
                raise ImportError("task_stepper page has no render() function")
        except Exception as e:
            logger.error("Failed to load task_stepper page: {}", e)
            from nicegui import ui

            def content() -> None:
                with ui.column().classes("w-full h-full items-center justify-center"):
                    ui.label(f"Error loading task_stepper page: {e}").classes(
                        "text-negative"
                    )

            from slumber.plugins.ui.nicegui2.shell.shell import render_shell

            render_shell(self.state, self.refresh, shell_cfg, content)  # type: ignore[arg-type]

    def _render_farewell(self) -> None:
        """Render the farewell page."""
        logger.info("Rendering farewell page")

        # Build shell config from settings
        shell_cfg = self._build_shell_config()

        # Import and render the farewell page
        try:
            page_module = importlib.import_module(
                "slumber.plugins.ui.nicegui2.pages.farewell.page"
            )
            settings_module = importlib.import_module(
                "slumber.plugins.ui.nicegui2.pages.farewell.settings"
            )
            farewell_cfg = settings_module.FarewellSettings()

            if hasattr(page_module, "render"):
                page_module.render(self.state, self.refresh, shell_cfg, farewell_cfg)
            else:
                raise ImportError("farewell page has no render() function")
        except Exception as e:
            logger.error("Failed to load farewell page: {}", e)
            from nicegui import ui

            def content() -> None:
                with ui.column().classes("w-full h-full items-center justify-center"):
                    ui.label(f"Error loading farewell page: {e}").classes(
                        "text-negative"
                    )
                    ui.button("Close", on_click=lambda: ui.navigate.to("/")).props(
                        "rounded"
                    )

            from slumber.plugins.ui.nicegui2.shell.shell import render_shell

            render_shell(self.state, self.refresh, shell_cfg, content)  # type: ignore[arg-type]

    def _build_shell_config(self) -> ShellSettings:
        """Build ShellSettings from NiceGUI2Settings."""
        settings = self.state.ui_settings
        return settings.shell
