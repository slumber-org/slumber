#!/usr/bin/env python
"""Demo script to manually test the NiceGUI participant UI.

Boots the app with a fake study/condition so you can click through all
pages without needing Supabase, a database, or any .env config.

Usage:
    uv run python scripts/demo_nicegui.py

Then open http://localhost:8080 in your browser.

Flow to test:
    Welcome -> "Start Session" -> pre_sleep procedure -> Sleep page
    -> "Going to Sleep" -> Sleep page (asleep state)
    -> "I'm Awake" -> first_awakening procedure -> Sleep page
    -> "I'm Awake" again -> later_awakening procedure -> Sleep page
    -> "End Session" -> post_sleep procedure -> Completion page
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nicegui import app, ui

from slumber.plugins.ui.nicegui.layouts import centered_fullscreen_layout
from slumber.plugins.ui.nicegui.pages.complete import render as render_complete_page
from slumber.plugins.ui.nicegui.pages.procedure import render as render_procedure_page
from slumber.plugins.ui.nicegui.pages.sleep import render as render_sleep_page
from slumber.plugins.ui.nicegui.pages.welcome import render as render_welcome_page
from slumber.plugins.ui.nicegui.state import AppState
from slumber.plugins.ui.nicegui.theme import COLORS
from slumber.schemas.condition import Condition
from slumber.schemas.dag import DAG, Component
from slumber.schemas.procedure import Procedure, Step
from slumber.schemas.study import Study


def _demo_login_page(state: AppState, refresh: object) -> None:
    """Login page that accepts any credentials (demo only)."""
    from slumber.plugins.ui.nicegui.theme import (
        INDIGO_LIGHT,
        SURFACE_LIGHT,
        SURFACE_MID,
        TEXT_SECONDARY,
    )

    with centered_fullscreen_layout(content_gap=None):
        if state.logo_url:
            ui.image(state.logo_url).classes("w-24 h-24 rounded-xl")
        else:
            ui.icon("nights_stay", size="64px").classes(f"text-[{INDIGO_LIGHT}]")
        ui.label("SLUMBER").classes("text-h3 font-bold mt-2")
        ui.label("Sign in to continue").classes(
            f"text-subtitle1 text-[{TEXT_SECONDARY}]"
        )

        with (
            ui.card()
            .classes(
                f"w-96 mt-6 px-6 py-5 bg-[{SURFACE_MID}] border border-[{SURFACE_LIGHT}]"
            )
            .props("flat bordered")
        ):
            ui.input("Email", value="demo@slumber.io").classes("w-full")
            ui.input(
                "Password", value="demo", password=True, password_toggle_button=True
            ).classes("w-full")

            def handle_login() -> None:
                state.authenticated = True
                state.current_page = "welcome"
                refresh()  # type: ignore[operator]

            ui.button("Sign In", icon="login", on_click=handle_login).classes(
                "w-full mt-2"
            ).props("rounded unelevated color=primary").style("letter-spacing: 1px")


_PAGE_RENDERERS = {
    "login": _demo_login_page,
    "welcome": render_welcome_page,
    "procedure": render_procedure_page,
    "sleep": render_sleep_page,
    "complete": render_complete_page,
}


@dataclass
class FakeRunContext:
    study_id: str = "demo_study"
    run_id: str = "run-001"
    condition_id: str = "demo_condition"
    participant_id: str = "sub-001"
    session_id: str = "ses-01"


def build_demo_condition() -> Condition:
    """Build a condition with event-driven procedures for manual testing."""
    return Condition(
        name="demo_condition",
        procedures={
            "pre_sleep": Procedure(
                title="Pre-Sleep Routine",
                trigger="session_start",
                steps=[
                    Step(
                        task_type="instruction",
                        title="Welcome",
                        settings={"text": "Welcome! Prepare for sleep."},
                    ),
                    Step(
                        task_type="survey",
                        title="Evening Questionnaire",
                        settings={
                            "questions": [
                                "How are you feeling?",
                                "Rate your sleepiness (1-10)",
                            ]
                        },
                    ),
                ],
            ),
            "first_awakening": Procedure(
                title="First Awakening Protocol",
                trigger="wake_up",
                when={"awakening_count": 1},
                steps=[
                    Step(
                        task_type="instruction",
                        title="Dream Report",
                        settings={
                            "text": "First awakening! Please answer a few questions."
                        },
                    ),
                ],
            ),
            "later_awakening": Procedure(
                title="Awakening Check-in",
                trigger="wake_up",
                when={"awakening_count": {"gt": 1}},
                steps=[
                    Step(
                        task_type="instruction",
                        title="Quick Report",
                        settings={"text": "Another awakening — quick check-in."},
                    ),
                ],
            ),
            "post_sleep": Procedure(
                title="Morning Debrief",
                trigger="session_end",
                steps=[
                    Step(
                        task_type="instruction",
                        title="Good Morning",
                        settings={"text": "Good morning! Session complete."},
                    ),
                    Step(
                        task_type="survey",
                        title="Sleep Quality Survey",
                        settings={
                            "questions": [
                                "How did you sleep?",
                                "Any dreams?",
                            ]
                        },
                    ),
                ],
            ),
        },
        dag=DAG(
            components=[Component(name="MASTER", unit_type="Master")],
            connections=[],
            process_components=[],
        ),
    )


def main() -> None:
    study = Study(study_id="demo_study", name="SLUMBER Demo Study")
    condition = build_demo_condition()
    context = FakeRunContext()

    logo_url = None
    assets_dir = Path(__file__).resolve().parents[1] / "docs" / "assets"
    logo_path = assets_dir / "logo.png"
    favicon_path = assets_dir / "favicon.png"
    if logo_path.is_file():
        app.add_static_files("/logo", str(logo_path.parent))
        logo_url = f"/logo/{logo_path.name}"

    state = AppState(
        study=study,
        condition=condition,
        context=context,  # type: ignore[arg-type]
        authenticated=False,
        current_page="login",
        logo_url=logo_url,
    )

    @ui.page("/")
    def main_page() -> None:
        ui.query(".nicegui-content").classes("p-0 m-0")
        ui.colors(**COLORS)

        @ui.refreshable
        def page_content() -> None:
            renderer = _PAGE_RENDERERS.get(state.current_page)
            if renderer is None:
                ui.label(f"Unknown page: {state.current_page}").classes("text-negative")
                return
            renderer(state, page_content.refresh)

        page_content()

    print("Starting demo at http://localhost:8080")
    print("Press Ctrl+C to stop.\n")
    ui.run(
        title="SLUMBER Demo",
        favicon=favicon_path if favicon_path.is_file() else None,
        port=8080,
        reload=False,
        show=False,
        dark=True,
    )


if __name__ == "__main__":
    main()
