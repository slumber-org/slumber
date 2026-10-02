"""GUI UI backend: NiceGUI AppFrame + layouts + activities."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel

from slumber.schemas.study import FrameHeaderSettings, FrameSettings, GuiSettings
from slumber.ui.backend import MountedActivity, UIBackend
from slumber.ui.frame import AppFrame
from slumber.ui.layouts.base import Layout
from slumber.ui.theme import (
    apply_theme,
    default_favicon_path,
    default_logo_path,
)

if TYPE_CHECKING:
    from slumber.plugins.base import ConfiguredPlugin
    from slumber.run.engine import RunEngine
    from slumber.schemas.condition import Phase

_NICEGUI_INSTALL_HINT = (
    "ui.type 'gui' requires the NiceGUI optional dependency. "
    "Install with: pip install 'slumber[nicegui]' (or uv sync --extra nicegui)."
)


class _GuiActivityHost:
    """ActivityHost that exposes a NiceGUI container."""

    def __init__(
        self,
        engine: RunEngine,
        activity_id: str,
        container: Any,
        *,
        on_complete: Callable[[str], None],
    ) -> None:
        self._engine = engine
        self._activity_id = activity_id
        self.container = container
        self._on_complete = on_complete

    def complete(self) -> None:
        """Mark this activity finished as a layout step."""
        self._on_complete(self._activity_id)

    def emit(self, name: str) -> None:
        """Forward a study event to the engine."""
        self._engine.emit(name, source_activity_id=self._activity_id)


class _GuiLayoutHost:
    """LayoutHost backed by the AppFrame body and RunEngine."""

    def __init__(
        self,
        *,
        engine: RunEngine,
        frame: AppFrame,
    ) -> None:
        self._engine = engine
        self._frame = frame

    @property
    def container(self) -> Any:
        """AppFrame body element."""
        return self._frame.body

    def emit_phase_completed(self) -> None:
        """Emit ``phase_completed`` to the engine."""
        self._engine.emit("phase_completed")

    def make_activity_host(
        self,
        activity_id: str,
        container: Any,
        *,
        on_complete: Callable[[str], None],
    ) -> _GuiActivityHost:
        """Build a GUI activity host for *activity_id*."""
        return _GuiActivityHost(
            self._engine,
            activity_id,
            container,
            on_complete=on_complete,
        )


class GuiBackend(UIBackend):
    """Participant GUI (NiceGUI): theme, AppFrame, layouts, and activities."""

    settings_model = GuiSettings

    def __init__(self, settings: GuiSettings | BaseModel | None = None) -> None:
        super().__init__(settings)
        self._engine: RunEngine | None = None
        self._frame: AppFrame | None = None
        self._layout: Layout | None = None
        self._logo_url: str | None = None
        self._logo_path: Path | None = None
        self._favicon_path: Path | None = None
        self._entry_started = False

    @property
    def _gui_settings(self) -> GuiSettings:
        if self.settings is None:
            return GuiSettings()
        if isinstance(self.settings, GuiSettings):
            return self.settings
        return GuiSettings.model_validate(self.settings.model_dump())

    def start(self, engine: RunEngine) -> None:
        """Apply theme, mount AppFrame, start the entry phase, and block in ui.run."""
        try:
            from nicegui import app, ui
            from starlette.responses import FileResponse, Response
        except ImportError as e:
            raise RuntimeError(_NICEGUI_INSTALL_HINT) from e

        self._engine = engine
        self._entry_started = False
        self._resolve_branding()

        logo_path = self._logo_path

        @app.get("/slumber-logo")
        async def serve_logo() -> Response:
            if logo_path is None or not logo_path.is_file():
                return Response(status_code=404)
            return FileResponse(logo_path)

        self._logo_url = "/slumber-logo" if logo_path is not None else None

        study_frame = _frame_dict_without_logo_path(self._gui_settings.frame)
        self._frame = AppFrame(
            study_name=engine.study.study_name,
            logo_url=self._logo_url,
            frame=study_frame,
        )

        @ui.page("/")
        def main_page() -> None:
            ui.query(".nicegui-content").classes("p-0 m-0")
            apply_theme()
            assert self._frame is not None
            self._frame.mount()
            if not self._entry_started:
                self._entry_started = True
                logger.info(
                    "gui: starting entry phase {!r}",
                    engine.condition.entry,
                )
                engine.start_phase(engine.condition.entry)

        port = self._gui_settings.port or 8080
        favicon = self._favicon_path
        logger.info(
            "gui: starting NiceGUI  study={!r} condition={!r} port={}",
            engine.study.study_id,
            engine.condition.name,
            port,
        )
        ui.run(
            title=engine.study.study_name,
            favicon=favicon,
            dark=True,
            port=port,
            reload=False,
            show=True,
        )

    def apply_frame(self, frame: dict[str, Any]) -> None:
        """Apply merged AppFrame settings for the active phase."""
        if self._frame is not None:
            self._frame.apply_frame(frame)

    def mount_phase(
        self,
        phase: Phase,
        layout: ConfiguredPlugin,
        activities: list[MountedActivity],
    ) -> None:
        """Mount *layout* and *activities* into the AppFrame body."""
        if self._engine is None:
            raise RuntimeError("GuiBackend.start() must be called first.")
        if self._frame is None or not self._frame.mounted:
            raise RuntimeError("AppFrame is not mounted; open the GUI page first.")
        if not isinstance(layout, Layout):
            raise TypeError(
                f"GUI layout must be a Layout plugin, got {type(layout).__name__}."
            )

        self.unmount_phase()
        self._frame.clear_body()
        self._layout = layout
        host = _GuiLayoutHost(engine=self._engine, frame=self._frame)
        logger.info(
            "gui: mounting phase {!r} layout={!r} activities={}",
            phase.id,
            type(layout).__name__,
            [a.config.id for a in activities],
        )
        layout.mount(host, activities)

    def unmount_phase(self) -> None:
        """Tear down the active layout and clear the body."""
        if self._layout is not None:
            self._layout.unmount()
            self._layout = None
        if self._frame is not None and self._frame.mounted:
            self._frame.clear_body()

    def stop(self) -> None:
        """Shutdown the NiceGUI app after ``end_run``."""
        try:
            from nicegui import app
        except ImportError:
            self._engine = None
            return
        logger.info("gui: shutting down NiceGUI")
        try:
            app.shutdown()
        except RuntimeError:
            # Already stopped or never started.
            pass
        self._engine = None

    def _resolve_branding(self) -> None:
        """Resolve favicon and logo paths (study override or package default)."""
        settings = self._gui_settings
        if settings.favicon:
            favicon = Path(settings.favicon)
            self._favicon_path = (
                favicon if favicon.is_file() else default_favicon_path()
            )
        else:
            self._favicon_path = default_favicon_path()

        logo_override = _header_logo_path(settings.frame)
        if logo_override:
            logo = Path(logo_override)
            self._logo_path = logo if logo.is_file() else default_logo_path()
        else:
            self._logo_path = default_logo_path()


def _header_logo_path(frame: FrameSettings | None) -> str | None:
    """Extract optional logo path from frame header settings."""
    if frame is None or frame.header is False or frame.header is None:
        return None
    if isinstance(frame.header, FrameHeaderSettings):
        return frame.header.logo
    if isinstance(frame.header, dict):
        raw = frame.header.get("logo")
        return str(raw) if raw else None
    return None


def _frame_dict_without_logo_path(frame: FrameSettings | None) -> dict[str, Any]:
    """Study frame as a dict for AppFrame, without the logo path key."""
    if frame is None:
        return {}
    data = frame.model_dump(exclude_none=True)
    header = data.get("header")
    if isinstance(header, dict):
        header = {k: v for k, v in header.items() if k != "logo"}
        data["header"] = header or True
    return data
