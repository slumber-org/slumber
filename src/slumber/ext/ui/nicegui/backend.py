"""NiceGUI UI backend: web-based participant app."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from starlette.responses import FileResponse, Response
from nicegui import app, ui

from slumber.constants import PACKAGE_ROOT
from slumber.ext.ui.nicegui.pages.complete import render as render_complete_page
from slumber.ext.ui.nicegui.pages.login import render as render_login_page
from slumber.ext.ui.nicegui.pages.procedure import render as render_procedure_page
from slumber.ext.ui.nicegui.pages.sleep import render as render_sleep_page
from slumber.ext.ui.nicegui.pages.welcome import render as render_welcome_page
from slumber.ext.ui.nicegui.state import AppState
from slumber.ext.ui.nicegui.theme import COLORS
from slumber.auth.client import load_session

if TYPE_CHECKING:
    from slumber.runtime.run import RunContext
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


class NiceGUIBackend:
    """Web-based participant UI backend using NiceGUI.

    Provides login, welcome, procedure execution, sleep monitoring,
    and session completion pages. Procedures are triggered by session
    events with optional guards.
    """

    def run(
        self,
        study: Study,
        condition: Condition,
        context: RunContext,
        config: dict[str, Any],
    ) -> None:
        """Run the full participant UI lifecycle.

        Starts a NiceGUI web server and blocks until the participant
        completes the session (or closes the app).

        Args:
            study: Loaded study manifest.
            condition: The condition to run.
            context: Run context (IDs for study, participant, session, run).
            config: UI backend config from ``study.ui.config``.
        """
        authenticated = _check_auth()
        logo_url = _serve_logo(config)
        state = AppState(
            study=study,
            condition=condition,
            context=context,
            config=config,
            authenticated=authenticated,
            current_page="welcome" if authenticated else "login",
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

        favicon = _find_favicon_path(config)
        ui.run(
            title=study.name,
            favicon=favicon,
            dark=config.get("dark", None),
            port=config.get("port", 8080),
            reload=False,
            show=config.get("show", True),
        )


def _find_logo_path(config: dict[str, Any]) -> Path | None:
    """Resolve the logo file path from config or default location."""
    logo_path = config.get("logo", LOGO_PATH)
    return logo_path if logo_path and logo_path.is_file() else None


def _find_favicon_path(config: dict[str, Any]) -> Path | None:
    """Resolve the favicon file path from config or default location."""
    favicon_path = config.get("favicon", FAVICON_PATH)
    return favicon_path if favicon_path and favicon_path.is_file() else None


def _serve_logo(config: dict[str, Any]) -> str | None:
    """Serve the logo file and return its URL, or None if not found."""
    path = _find_logo_path(config)
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
    try:
        session = load_session()
        return session is not None
    except Exception:
        return False
