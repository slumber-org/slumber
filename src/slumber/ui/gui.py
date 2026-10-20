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
    mount_fonts,
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
        self._default_logo_url: str | None = None
        self._logo_path: Path | None = None
        self._favicon_path: Path | None = None
        self._logo_urls: dict[Path, str] = {}
        self._missing_logos: set[Path] = set()
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
        except ImportError as e:
            raise RuntimeError(_NICEGUI_INSTALL_HINT) from e

        self._engine = engine
        self._entry_started = False
        self._resolve_branding()
        mount_fonts(app)
        self._default_logo_url = self._serve_logo(self._logo_path)
        self._frame = AppFrame(
            study_name=engine.study.study_name,
            logo_url=self._default_logo_url,
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

    def apply_frame(self, frame: dict[str, Any], phase: Phase) -> None:
        """Apply merged AppFrame settings for the phase being started."""
        if self._frame is not None:
            self._frame.apply_frame(
                frame,
                phase_title=phase.display_title,
                logo_url=self._header_logo_url(frame),
            )

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

    def _header_logo_url(self, frame: dict[str, Any]) -> str | None:
        """Served URL for the frame's header logo.

        A missing file falls back to the study logo, or to the packaged logo when
        the study sets none or its file is missing too.
        """
        header = frame.get("header")
        logo = header.get("logo") if isinstance(header, dict) else None
        if not logo:
            return self._default_logo_url
        path = Path(logo)
        if not path.is_file():
            if path not in self._missing_logos:
                self._missing_logos.add(path)
                logger.warning(
                    "gui: header logo {} not found; using the study or packaged logo",
                    path,
                )
            return self._default_logo_url
        return self._serve_logo(path)

    def _serve_logo(self, path: Path | None) -> str | None:
        """Serve *path* as a static file once and return its URL."""
        if path is None:
            return None
        url = self._logo_urls.get(path)
        if url is None:
            from nicegui import app

            url = app.add_static_file(local_file=path)
            self._logo_urls[path] = url
        return url


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
