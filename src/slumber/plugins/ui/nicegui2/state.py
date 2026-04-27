"""Reactive app state for the NiceGUI2 participant UI.

All pages read/write :class:`PageGraphState`. Page navigation is driven by
setting :attr:`PageGraphState.current_page_id` and firing routing events.

Architecture:
- Global pages: welcome, farewell (study-level, not in page_graph)
- Condition pages: interaction, task_stepper (condition-level, in page_graph)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, TYPE_CHECKING, Any

from loguru import logger
from nicegui import ui

if TYPE_CHECKING:
    from slumber.runtime.run import RunContext
    from slumber.schemas.condition import Condition, PageGraph
    from slumber.schemas.study import Study
    from slumber.plugins.ui.nicegui2.settings import NiceGUI2Settings


@dataclass
class PageGraphState:
    """Central state for nicegui2 navigation through SLUMBER."""

    study: Study
    conditions: list[Condition]
    context: RunContext
    ui_settings: NiceGUI2Settings

    # Currently selected condition (set by welcome page)
    current_condition: Condition | None = field(default=None)

    # Navigation state
    current_page_id: str = field(init=False, default="welcome")
    page_data: dict[str, Any] = field(default_factory=dict)
    _refresh_callback: Callable[[], None] | None = field(default=None, repr=False)

    # Session state (for tracking completion, etc.)
    session_started: bool = False
    session_ended: bool = False

    def __post_init__(self) -> None:
        """Register study assets directory as static files after initialization."""
        if self.study.path is not None:
            assets_dir = self.study.path / self.study.assets_dir
            if assets_dir.exists():
                try:
                    from nicegui import app

                    # Use the configured assets_dir name for the URL path
                    app.add_static_files(f"/{self.study.assets_dir}", str(assets_dir))
                    logger.info(
                        "Registered study assets directory: {} at /{}",
                        assets_dir,
                        self.study.assets_dir,
                    )
                except RuntimeError:
                    pass  # Already registered

    @property
    def page_graph(self) -> PageGraph | None:
        """Get the page_graph of the current condition."""
        if self.current_condition is None:
            return None
        return self.current_condition.page_graph

    @property
    def study_assets_dir(self) -> Path | None:
        """Get the study assets directory path, or None if study path is unknown."""
        if self.study.path is None:
            return None
        return self.study.path / self.study.assets_dir

    def select_condition(self, condition_name: str) -> None:
        """Select a condition and navigate to its first page.

        Args:
            condition_name: Name of the condition to select.

        Raises:
            ValueError: If condition not found or lacks page_graph.
        """
        for cond in self.conditions:
            if cond.name == condition_name:
                if cond.page_graph is None:
                    raise ValueError(f"Condition {condition_name!r} has no page_graph.")
                self.current_condition = cond
                self.current_page_id = cond.page_graph.first_page
                self.session_started = True
                logger.info(
                    "Selected condition: {}, first page: {}",
                    condition_name,
                    self.current_page_id,
                )
                return
        raise ValueError(
            f"Condition {condition_name!r} not found. Available: {[c.name for c in self.conditions]}"
        )

    def navigate_to(self, page_id: str) -> None:
        """Navigate to a specific page by ID.

        Args:
            page_id: Target page ID.
                - 'welcome': Global welcome page
                - 'farewell': Global farewell page
                - Other: Must exist in current condition's page_graph

        Raises:
            ValueError: If page_id is not valid for current state.
        """
        if page_id == "welcome":
            logger.info("Navigating to welcome page")
            self.current_page_id = "welcome"
            self.current_condition = None
            return

        if page_id == "farewell":
            logger.info("Navigating to farewell page")
            self.current_page_id = "farewell"
            self.session_ended = True
            return

        # Navigate within condition page_graph
        if self.page_graph is None:
            raise ValueError(
                "Cannot navigate to condition page: no condition selected."
            )

        if page_id not in self.page_graph.pages:
            raise ValueError(
                f"Invalid page_id {page_id!r}. "
                f"Must be one of: {sorted(self.page_graph.pages.keys())}, 'welcome', or 'farewell'."
            )

        logger.info("Navigating to page: {}", page_id)
        self.current_page_id = page_id

        # Clear any page-specific data to ensure fresh start
        keys_to_delete = [k for k in self.page_data.keys() if k.startswith(page_id)]
        for key in keys_to_delete:
            del self.page_data[key]

    def set_refresh_callback(self, callback: Callable[[], None] | None) -> None:
        """Set the refresh callback to trigger UI updates after navigation.

        Args:
            callback: Function to call to refresh the UI, or None to clear.
        """
        self._refresh_callback = callback

    def _trigger_refresh(self) -> None:
        """Trigger the refresh callback if set."""
        if self._refresh_callback is not None:
            self._refresh_callback()

    def fire_routing_event(self, event_key: str) -> None:
        """Fire a routing event for the current page.

        For global pages (welcome, farewell), this handles special logic.
        For condition pages, this looks up the event in the page's routing dict.
        Automatically triggers a UI refresh after navigation.

        Args:
            event_key: The routing event key (e.g., 'start', 'next', 'complete').

        Raises:
            ValueError: If event_key is not found in current page's routing,
                or if the destination is invalid.
        """
        if self.current_page_id == "welcome":
            # Welcome page events select a condition
            # event_key should be the condition name
            self.select_condition(event_key)
            self._trigger_refresh()
            return

        if self.current_page_id == "farewell":
            logger.warning("Ignoring routing event {} on farewell page", event_key)
            return

        # Handle condition page routing
        if self.page_graph is None:
            raise ValueError("Cannot fire routing event: no condition selected.")

        current_page = self.page_graph.pages.get(self.current_page_id)
        if current_page is None:
            raise ValueError(
                f"Current page {self.current_page_id!r} not found in page_graph."
            )

        if event_key not in current_page.routing:
            raise ValueError(
                f"Routing event {event_key!r} not found in page {self.current_page_id!r}. "
                f"Available events: {sorted(current_page.routing.keys())}"
            )

        destination = current_page.routing[event_key]
        self.navigate_to(destination)
        self._trigger_refresh()

    def get_current_page(self) -> str:
        """Get the current page ID."""
        return self.current_page_id

    def is_welcome(self) -> bool:
        """Check if currently on the welcome page."""
        return self.current_page_id == "welcome"

    def is_farewell(self) -> bool:
        """Check if currently on the farewell page."""
        return self.current_page_id == "farewell"

    def is_in_condition(self) -> bool:
        """Check if currently navigating within a condition's page_graph."""
        return self.current_condition is not None and not self.is_farewell()

    def set_page_data(self, key: str, value: Any) -> None:
        """Store page-specific data.

        Args:
            key: Data key.
            value: Data value.
        """
        self.page_data[key] = value

    def get_page_data(self, key: str, default: Any = None) -> Any:
        """Retrieve page-specific data.

        Args:
            key: Data key.
            default: Default value if key not found.

        Returns:
            The stored value or default.
        """
        return self.page_data.get(key, default)
