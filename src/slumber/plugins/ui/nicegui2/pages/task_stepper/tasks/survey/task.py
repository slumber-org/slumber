"""Survey task - embeds SurveyJS form loaded from JSON file."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from nicegui import ui, app

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


# Register static files for survey assets (done once at module load)
_ASSETS_DIR = Path(__file__).parent / "assets"
if _ASSETS_DIR.exists():
    try:
        app.add_static_files("/survey-assets", str(_ASSETS_DIR))
    except RuntimeError:
        pass  # Already registered


@dataclass
class SurveyConfig:
    """Configuration for the survey task."""

    json_path: str | None = None
    theme_path: str | None = None


def render(
    state: PageGraphState,
    on_complete: callable,
    task_cfg: SurveyConfig | None = None,
    task_index: int = 0,
) -> None:
    """Render the survey task with embedded SurveyJS using local assets.

    Args:
        state: App state
        on_complete: Callback to call when survey is completed
        task_cfg: Task configuration. If theme_path is provided, loads a SurveyJS
                  theme JSON file to customize the survey appearance.
        task_index: Index of this task within the page's task list.
    """
    if task_cfg is None:
        task_cfg = SurveyConfig()

    # Generate instance ID based on task type, page ID and task index
    # Multiple tasks on same page have different IDs (task_index)
    page_id = state.get_current_page()
    task_type = "survey"
    instance_id = f"{task_type}_{page_id}_{task_index}".replace("-", "_")

    # Load survey JSON - check study assets first, then plugin directory
    survey_file = None
    if state.study_assets_dir is not None:
        survey_file = state.study_assets_dir / task_cfg.json_path
        if not survey_file.exists():
            survey_file = None

    if survey_file is None:
        survey_file = Path(__file__).parent / task_cfg.json_path

    if not survey_file.exists():
        ui.label(f"Survey file not found: {task_cfg.json_path}").classes(
            "text-negative"
        )
        on_complete()
        return

    survey_json = json.loads(survey_file.read_text(encoding="utf-8"))

    # Load theme JSON - use default if not provided
    theme_json = None
    if task_cfg.theme_path:
        # Load custom theme from study assets or plugin directory
        theme_file = None
        if state.study_assets_dir is not None:
            theme_file = state.study_assets_dir / task_cfg.theme_path
            if not theme_file.exists():
                theme_file = None

        if theme_file is None:
            theme_file = Path(__file__).parent / task_cfg.theme_path

        if theme_file.exists():
            theme_json = json.loads(theme_file.read_text(encoding="utf-8"))
    else:
        # Load default theme
        default_theme_file = Path(__file__).parent / "default_theme.json"
        if default_theme_file.exists():
            theme_json = json.loads(default_theme_file.read_text(encoding="utf-8"))

    # Create full-width container with fixed height for scrolling
    with (
        ui.element("div")
        .classes("w-full px-8")
        .style("flex: 1; min-width: 0; min-height: 0;")
    ):
        ui.html("""
            <div id="surveyWrapper" style="width: 100%; height: 400px; overflow-y: scroll; overflow-x: hidden;">
                <div id="surveyContainer" style="width: 100%;"></div>
            </div>
        """)

    # Thank you message HTML (reused for both initial check and completion)
    thank_you_html = '<div style="text-align: center; padding: 40px;"><h2 style="color: var(--q-primary);">Thank you!</h2><p style="color: var(--q-primary); margin-top: 16px;">The survey has been completed. You can now continue to the next step.</p></div>'

    # Load SurveyJS with inline script - check if already completed first
    init_script = f"""
        (function() {{
            // Thank you message HTML
            const thankYouHtml = '{thank_you_html}';
            const instanceId = '{instance_id}';

            // If already completed for this instance, show thank you message instead of re-rendering survey
            if (window.surveyCompleted_{instance_id} && window.surveyData_{instance_id}) {{
                const wrapper = document.getElementById('surveyWrapper');
                if (wrapper) {{
                    wrapper.innerHTML = thankYouHtml;
                }}
                return;
            }}

            // Load CSS
            const css1 = document.createElement('link');
            css1.rel = 'stylesheet';
            css1.href = '/survey-assets/css/survey-core.min.css';
            document.head.appendChild(css1);

            const css2 = document.createElement('link');
            css2.rel = 'stylesheet';
            css2.href = '/survey-assets/css/survey-styles.css';
            document.head.appendChild(css2);

            // Load scripts sequentially
            const loadScript = function(src, callback) {{
                const script = document.createElement('script');
                script.src = src;
                script.onload = callback;
                script.onerror = function() {{ console.error('Failed to load:', src); }};
                document.head.appendChild(script);
            }};

            // Load dependencies then init
            loadScript('/survey-assets/js/markdown-it.min.js', function() {{
                loadScript('/survey-assets/js/survey.core.min.js', function() {{
                    loadScript('/survey-assets/js/survey-js-ui.min.js', function() {{
                        // Initialize survey
                        if (typeof Survey === 'undefined') {{
                            console.error('SurveyJS not loaded after script injection');
                            return;
                        }}

                        const surveyJson = {json.dumps(survey_json)};
                        const survey = new Survey.Model(surveyJson);

                        // Apply theme if provided
                        const themeJson = {json.dumps(theme_json) if theme_json else "null"};
                        if (themeJson) {{
                            survey.applyTheme(themeJson);
                        }}

                        survey.onComplete.add(function(sender) {{
                            window.surveyCompleted_{instance_id} = true;
                            window.surveyData_{instance_id} = sender.data;
                            console.log('Survey completed:', sender.data);
                            // Replace with thank you message in wrapper
                            const wrapper = document.getElementById('surveyWrapper');
                            if (wrapper) {{
                                wrapper.innerHTML = thankYouHtml;
                            }}
                            // Notify Python
                            window.surveyOnComplete_{instance_id} && window.surveyOnComplete_{instance_id}();
                        }});

                        const container = document.getElementById('surveyContainer');
                        if (container) {{
                            survey.render(container);
                        }} else {{
                            console.error('Survey container not found');
                        }}
                    }});
                }});
            }});
        }})();
    """

    ui.run_javascript(init_script)

    # Set up completion callback that Python can poll for
    ui.run_javascript(f"""
        window.surveyOnComplete_{instance_id} = function() {{
            window.surveyCompleted_{instance_id} = true;
        }};
    """)

    # Poll for completion - use global timer to avoid element context issues
    completion_timer = [None]

    async def check_done():
        try:
            result = await ui.run_javascript(
                f"return window.surveyCompleted_{instance_id} || false;"
            )
            if result:
                on_complete()  # Enable Next button
                completion_timer[0] = None
            else:
                completion_timer[0] = ui.timer(0.5, check_done, once=True)
        except Exception:
            # Context may be gone, stop polling
            completion_timer[0] = None

    # Only start polling if not already complete
    async def init_check():
        try:
            already_complete = await ui.run_javascript(
                f"return window.surveyCompleted_{instance_id} && window.surveyData_{instance_id} ? true : false;"
            )
            if already_complete:
                on_complete()  # Mark as completed if already done
            else:
                completion_timer[0] = ui.timer(0.5, check_done, once=True)
        except Exception:
            pass

    ui.timer(0.3, init_check, once=True)


def cleanup(instance_id: str) -> str:
    """Return JavaScript to clean up survey-specific global state.

    Args:
        instance_id: The unique instance ID for this survey (e.g., 'survey_page_0').

    Returns:
        JavaScript code to clear survey global variables.
    """
    return f"""
        // Clear survey-specific global state
        delete window.surveyCompleted_{instance_id};
        delete window.surveyData_{instance_id};
        delete window.surveyOnComplete_{instance_id};
    """
