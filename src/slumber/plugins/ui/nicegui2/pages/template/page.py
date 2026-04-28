"""Layout Template - Quick Guide for Designing Pages.

QUICK START:
1. Copy this folder to a new page (e.g., `my_page/`)
2. Edit the layout between the markers below
3. Add your page to the page_graph in condition.yaml

PAGE STRUCTURE:
- The shell (menu bar + indicators) wraps your content automatically
- Your content goes in the `content()` function
- Use `w-full h-full` for full-page content
- Use `items-center justify-center` to center content

COMMON LAYOUT PATTERNS:

1. CENTERED CONTENT (default):
   with ui.column().classes("w-full h-full items-center justify-center p-8 gap-6"):
       ui.icon("icon_name", size="80px")
       ui.label("Title").classes("text-h3 text-center")
       ui.label("Description").classes("text-subtitle1 text-center")

2. LEFT-ALIGNED CONTENT:
   with ui.column().classes("w-full h-full p-8 gap-6"):
       ui.label("Title").classes("text-h3")
       ui.label("Body text...").classes("text-body1")

3. TWO-COLUMN LAYOUT:
   with ui.row().classes("w-full h-full p-8 gap-6"):
       with ui.column().classes("w-1/2"):
           ui.label("Left side")
       with ui.column().classes("w-1/2"):
           ui.label("Right side")

4. CARD-BASED LAYOUT:
   with ui.column().classes("w-full h-full items-center p-8 gap-6"):
       with ui.card().classes("w-full max-w-md p-6"):
           ui.label("Card Title").classes("text-h6")
           ui.input("Enter value")

CREATING A CUSTOM PAGE CONFIG:
1. Add a new @dataclass in `config.py` (e.g., `class MyPageConfig`)
2. Include `markdown_path: str = "my_page.md"` attribute
3. Import your config class and `load_markdown_content` from utils.py
4. Use: `title, subtitle, body = load_markdown_content(page_cfg)`
5. Render with: `ui.markdown(body)` (preserves bold, lists, etc.)

Example config class in config.py:
    @dataclass
    class MyPageConfig:
        markdown_path: str = "my_page.md"
        primary_button: str = "Continue"
        show_extra_info: bool = True

See `welcome/` and `farewell/` for examples using shared `utils.load_markdown_content()`.

AVAILABLE ICONS (Material Design):
Common icons: "home", "settings", "person", "check", "close", "menu",
"arrow_back", "arrow_forward", "refresh", "add", "delete", "edit",
"info", "warning", "error", "help", "search", "favorite", "star"
Full list: https://fonts.google.com/icons

COLORS (Quasar color names - mapped via theme):
- primary: Main brand color
- secondary: Accent color
- positive: Success/good state
- negative: Error/bad state
- warning: Caution state
- dark: Background color
- Use text-primary, text-secondary for text colors

TEXT STYLES (Tailwind/Quasar classes):
- text-h1 through text-h6: Headings (h1 largest)
- text-subtitle1, text-subtitle2: Subtitles
- text-body1, text-body2: Body text
- text-caption: Small text
- text-overline: Very small uppercase

BUTTON STYLES:
- .props("unelevated"): Filled button
- .props("flat"): No background
- .props("outline"): Bordered
- .props("rounded"): Rounded corners
- .classes("w-full"): Full width

SPACING:
- p-4, p-8: Padding (1rem = 16px, 2rem = 32px)
- gap-2, gap-4, gap-6: Gap between elements
- m-0, m-4: Margins

WIDTH/HEIGHT:
- w-full: 100% width
- h-full: 100% height
- max-w-md: Max width ~448px
- max-w-lg: Max width ~512px
"""

from __future__ import annotations

from typing import Callable

from nicegui import ui

from typing import TYPE_CHECKING

from slumber.plugins.ui.nicegui2.shell.shell import render_shell
from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.pages.template.settings import TemplateSettings

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(
    state: PageGraphState,
    refresh: Callable[[], None],
    shell_cfg: ShellSettings | None = None,
    page_cfg: TemplateSettings | None = None,
) -> None:
    """Render the page.

    This is your canvas - modify the layout between the markers below.
    The shell (menu bar + indicators) wraps everything automatically.
    """
    if shell_cfg is None:
        shell_cfg = ShellSettings()
    if page_cfg is None:
        page_cfg = TemplateSettings()

    def content() -> None:
        # ============================================================
        # YOUR LAYOUT STARTS HERE
        # ============================================================

        # Example: Centered content layout
        with ui.column().classes("w-full h-full items-center justify-center p-8 gap-6"):
            # Title
            ui.label(page_cfg.title).classes("text-h4 font-bold text-primary")

            # Description
            ui.label(page_cfg.description).classes("text-body1 text-secondary")

            # Subtitle/description
            ui.label("Your page description goes here").classes(
                "text-subtitle1 text-secondary text-center max-w-md"
            )

            # Content card
            with ui.card().classes(
                "w-full max-w-md bg-surface border border-secondary p-6"
            ):
                ui.label("Card Content").classes("text-h6 font-bold text-primary mb-4")

                # Form elements example
                ui.input("Your input").classes("w-full text-primary")
                ui.checkbox("Your checkbox").classes("text-primary mt-4")

            # Action buttons
            with ui.row().classes("gap-3 mt-4"):
                ui.button(
                    "Primary Action",
                    icon="check",
                    on_click=lambda: ui.notify("Clicked!"),
                ).props("rounded unelevated color=primary text-color=primary")

                ui.button(
                    "Secondary",
                    icon="close",
                    on_click=lambda: ui.notify("Cancelled"),
                ).props("flat rounded text-color=primary")

        # ============================================================
        # YOUR LAYOUT ENDS HERE
        # ============================================================

    # The shell wraps your content with the menu bar and indicators
    render_shell(state, refresh, shell_cfg, content)  # type: ignore[arg-type]
