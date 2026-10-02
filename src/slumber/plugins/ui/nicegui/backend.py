"""NiceGUI UI backend: web-based participant app."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from loguru import logger
from nicegui import app, ui
from starlette.responses import FileResponse, Response

from slumber.constants import PACKAGE_ROOT
from slumber.plugins.ui.base import UIBackend
from slumber.plugins.ui.nicegui.config import NiceGUISettings
from slumber.plugins.ui.nicegui.pages.complete import render as render_complete_page
from slumber.plugins.ui.nicegui.pages.login import render as render_login_page
from slumber.plugins.ui.nicegui.pages.procedure import render as render_procedure_page
from slumber.plugins.ui.nicegui.pages.sleep import render as render_sleep_page
from slumber.plugins.ui.nicegui.pages.welcome import render as render_welcome_page
from slumber.plugins.ui.nicegui.state import AppState
from slumber.plugins.ui.nicegui.theme import COLORS
from slumber.supabase.auth.client import load_session
from slumber.supabase.utils import SUPABASE_INSTALL_HINT, is_supabase_extra_installed

if TYPE_CHECKING:
    from pydantic import BaseModel

    from slumber.run import RunContext
    from slumber.schemas.condition import Condition
    from slumber.schemas.study import Study

_PAGE_RENDERERS = {
    "login": render_login_page,
    "welcome": render_welcome_page,
    "procedure": render_procedure_page,
    "sleep": render_sleep_page,
    "complete": render_complete_page,
}

LOGO_PATH = PACKAGE_ROOT / "docs/assets/logo.png"
FAVICON_PATH = PACKAGE_ROOT / "docs/assets/favicon.png"


class NiceGUIBackend(UIBackend):
    """Web-based participant UI backend using NiceGUI.

    Provides login, welcome, procedure execution, sleep monitoring,
    and session completion pages. Procedures are triggered by session
    events with optional guards.
    """

    ui_settings_model: ClassVar[type[BaseModel] | None] = NiceGUISettings

    def run(
        self,
        study: Study,
        condition: Condition,
        context: RunContext,
    ) -> None:
        """Run the full participant UI lifecycle.

        Starts a NiceGUI web server and blocks until the participant
        completes the session (or closes the app).

        Args:
            study: Loaded study manifest.
            condition: The condition to run.
            context: Run context (IDs for study, participant, session, run).
        """
        assert isinstance(self._settings, NiceGUISettings)
        nicegui_cfg = self._settings

        authenticated = False
        first_page = "welcome"
        if nicegui_cfg.require_login:
            if not is_supabase_extra_installed():
                raise RuntimeError(
                    "NiceGUI login requires the Supabase optional dependency. "
                    f"{SUPABASE_INSTALL_HINT}"
                )

            authenticated = _check_auth()
            first_page = "login" if not authenticated else "welcome"

        logo_url = _serve_logo()
        state = AppState(
            study=study,
            condition=condition,
            context=context,
            ui_settings=nicegui_cfg,
            authenticated=authenticated,
            current_page=first_page,
            logo_url=logo_url,
        )

        logger.info(
            "Starting NiceGUI UI: study={!r} condition={!r} authenticated={}",
            study.study_id,
            condition.name,
            authenticated,
        )

        @ui.page("/")
        def main_page() -> None:
            ui.query(".nicegui-content").classes("p-0 m-0")
            ui.colors(**COLORS)

            @ui.refreshable
            def page_content() -> None:
                renderer = _PAGE_RENDERERS.get(state.current_page)
                if renderer is None:
                    ui.label(f"Unknown page: {state.current_page}").classes(
                        "text-negative"
                    )
                    return
                renderer(state, page_content.refresh)  # type: ignore[attr-defined]

            page_content()

        favicon = _default_favicon_path()
        ui.run(
            title=study.name,
            favicon=favicon,
            dark=nicegui_cfg.dark,
            port=nicegui_cfg.port,
            reload=False,
            show=nicegui_cfg.show,
        )


def _default_logo_path() -> Path | None:
    """Package logo used for the NiceGUI UI (not study-configurable)."""
    return LOGO_PATH if LOGO_PATH.is_file() else None


def _default_favicon_path() -> Path | None:
    """Package favicon used for the NiceGUI UI (not study-configurable)."""
    return FAVICON_PATH if FAVICON_PATH.is_file() else None


def _serve_logo() -> str | None:
    """Serve the SLUMBER package logo and return its URL, or None if not found."""
    path = _default_logo_path()
    if path is None:
        return None

    @app.get("/logo")
    def serve_logo() -> Response:
        if path is None or not path.is_file():
            return Response(status_code=404)
        return FileResponse(path)

    return "/logo"


def _check_auth() -> bool:
    """Check if a valid Supabase session exists."""
    return load_session() is not None
