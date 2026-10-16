"""Instruction activity: show markdown/text and complete on mount."""

from __future__ import annotations

import re
from collections.abc import Callable
from html import escape
from pathlib import Path
from urllib.parse import unquote

from loguru import logger
from pydantic import BaseModel, Field

from slumber.ui.activities.base import Activity, ActivityHost

INSTRUCTION_CSS = """
.slumber-instruction {
  font-size: var(--slumber-fs);
  line-height: 1.65;
  color: var(--slumber-text);
}
.slumber-instruction > :first-child { margin-top: 0; }
.slumber-instruction > :last-child { margin-bottom: 0; }
.slumber-instruction h1 {
  margin: 0 0 12px;
  font-size: var(--slumber-h1);
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0;
  text-wrap: balance;
}
.slumber-instruction h2 {
  margin: 22px 0 8px;
  font-size: var(--slumber-h2);
  line-height: 1.3;
  font-weight: 700;
  letter-spacing: 0;
}
.slumber-instruction h3 {
  margin: 18px 0 6px;
  font-size: 1.15em;
  line-height: 1.3;
  font-weight: 700;
  letter-spacing: 0;
}
.slumber-instruction p { margin: 0 0 12px; }
.slumber-instruction ul, .slumber-instruction ol {
  margin: 0 0 12px;
  padding-left: 24px;
  line-height: 1.8;
}
.slumber-instruction a { color: var(--slumber-accent); text-underline-offset: 2px; }
.slumber-instruction a:focus-visible { outline: 2px solid var(--slumber-text); outline-offset: 2px; }
.slumber-instruction blockquote {
  margin: 16px 0;
  padding: 12px 16px;
  border: 0;
  border-radius: 8px;
  background: var(--slumber-surface-alt);
}
.slumber-instruction blockquote > :last-child { margin-bottom: 0; }
.slumber-instruction code {
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--slumber-surface-alt);
}
.slumber-instruction pre {
  margin: 12px 0;
  padding: 12px 16px;
  border-radius: 8px;
  background: var(--slumber-surface-alt);
  overflow-x: auto;
}
.slumber-instruction pre code { padding: 0; background: none; }
.slumber-instruction table {
  display: block;
  width: max-content;
  max-width: 100%;
  margin: 10px 0;
  overflow-x: auto;
  border-collapse: separate;
  border-spacing: 0 2px;
}
.slumber-instruction th, .slumber-instruction td {
  padding: 8px 14px;
  border: 0;
  text-align: left;
  white-space: nowrap;
}
.slumber-instruction td { background: var(--slumber-surface-alt); }
.slumber-instruction th {
  background: var(--slumber-page-bg);
  font-size: 0.8em;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--slumber-secondary);
}
.slumber-instruction th:first-child, .slumber-instruction td:first-child {
  border-radius: 6px 0 0 6px;
}
.slumber-instruction th:last-child, .slumber-instruction td:last-child {
  border-radius: 0 6px 6px 0;
}
.slumber-instruction hr {
  margin: 22px 0;
  height: 4px;
  border: 0;
  border-radius: 2px;
  background: var(--slumber-surface-alt);
}
.slumber-instruction img { max-width: 100%; height: auto; border-radius: 8px; }
.slumber-instruction img.slumber-image-left,
.slumber-instruction img.slumber-image-center,
.slumber-instruction img.slumber-image-right {
  display: block;
  margin-top: 12px;
  margin-bottom: 12px;
}
.slumber-instruction img.slumber-image-left { margin-right: auto; }
.slumber-instruction img.slumber-image-center { margin-left: auto; margin-right: auto; }
.slumber-instruction img.slumber-image-right { margin-left: auto; }
.slumber-instruction-empty { font-style: italic; color: var(--slumber-secondary); }
"""

# ``![alt](target "optional title"){width=300 align=center}``
_IMAGE_PATTERN = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\(\s*(?P<target>[^)\s]+)(?:\s+"(?P<title>[^"]*)")?\s*\)'
    r"(?P<options>\{[^}]*\})?"
)
# Fenced blocks and inline code: image syntax shown there is not an image.
_CODE = re.compile(r"(```.*?```|~~~.*?~~~|`[^`\n]*`)", re.DOTALL)
_WIDTH = re.compile(r"^\d+(px|%)?$")
_ALIGNMENTS = ("left", "center", "right")
# Web addresses (http:, data:, ...), protocol-relative ones and page anchors. A
# scheme needs two letters so that a Windows drive such as ``C:`` is not one.
_URL_TARGET = re.compile(r"^([a-z][a-z0-9+.-]+:|//|#)", re.IGNORECASE)

# Image files already served, so each file gets one URL.
_SERVED_IMAGES: dict[Path, str] = {}


class InstructionSettings(BaseModel):
    """Settings for :class:`InstructionActivity`."""

    content: str = Field(
        default="",
        description="Inline text/markdown or a resolved path to a content file.",
    )


def load_instruction_content(content: str) -> str:
    """Return file contents when *content* is an existing path, else the string."""
    if not content:
        return ""
    path = Path(content)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return content


def _image_options(options: str) -> tuple[str | None, str | None]:
    """Read ``{width=300 align=center}`` into a CSS width and an alignment.

    Unknown or invalid options are ignored with a warning.
    """
    width: str | None = None
    align: str | None = None
    for item in options.strip("{}").replace(",", " ").split():
        key, _, value = item.partition("=")
        if key == "width" and _WIDTH.match(value):
            width = value if value.endswith(("px", "%")) else f"{value}px"
        elif key == "align" and value in _ALIGNMENTS:
            align = value
        else:
            logger.warning("instruction: ignoring image option {!r}", item)
    return width, align


def _image_html(
    url: str, alt: str, title: str | None, width: str | None, align: str | None
) -> str:
    """An ``<img>`` for an image that has options."""
    parts = [f'src="{escape(url)}"', f'alt="{escape(alt)}"']
    if title is not None:
        parts.append(f'title="{escape(title)}"')
    if align is not None:
        parts.append(f'class="slumber-image-{align}"')
    if width is not None:
        parts.append(f'style="width: {width}"')
    return f"<img {' '.join(parts)}>"


def rewrite_image_paths(
    markdown: str,
    resolve: Callable[[str], Path],
    serve: Callable[[Path], str],
) -> str:
    """Point markdown images at files served to the browser.

    An image path is resolved like any other path in a study: placeholders such as
    ``{assets_dir}`` are expanded and a relative path is relative to the study
    root. Web addresses are left as written, and so is an image that does not
    name a file (with a warning, unless it looks like a server path).

    An image can be followed by options in braces, ``{width=300 align=center}``:
    ``width`` is pixels or a percentage and ``align`` is ``left``, ``center`` or
    ``right``. An image with options becomes an ``<img>``. Images written inside
    code (inline or fenced) are left alone.

    Args:
        markdown: Markdown text.
        resolve: Expands placeholders in a path and resolves it against the study
            root (``ActivityHost.resolve_path``).
        serve: Makes a file available to the browser and returns its URL.

    Returns:
        The markdown with image paths replaced by served URLs.
    """

    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        url = target
        if not _URL_TARGET.match(target):
            path = resolve(unquote(target))
            if path.is_file():
                url = serve(path)
            elif not target.startswith("/"):
                logger.warning(
                    "instruction: image {} not found; leaving it as written", path
                )

        alt, title, options = match.group("alt", "title", "options")
        if options is not None:
            width, align = _image_options(options)
            return _image_html(url, alt, title, width, align)
        if url == target:
            return match.group(0)
        titled = "" if title is None else f' "{title}"'
        return f"![{alt}]({url}{titled})"

    # Splitting on a capturing group puts the code segments at the odd indexes.
    parts = _CODE.split(markdown)
    return "".join(
        part if index % 2 else _IMAGE_PATTERN.sub(replace, part)
        for index, part in enumerate(parts)
    )


def _serve_image(path: Path) -> str:
    """Serve an image file once and return its URL."""
    from nicegui import app

    url = _SERVED_IMAGES.get(path)
    if url is None:
        url = app.add_static_file(local_file=path)
        _SERVED_IMAGES[path] = url
    return url


class InstructionActivity(Activity):
    """Render instruction content; calls ``host.complete()`` on mount."""

    settings_model = InstructionSettings
    css = INSTRUCTION_CSS

    def mount(self, activity_host: ActivityHost) -> None:
        """Render when a GUI container is present; always complete as a step."""
        settings = self.settings
        assert isinstance(settings, InstructionSettings)
        body = load_instruction_content(settings.content)

        if activity_host.container is not None:
            from nicegui import ui

            with activity_host.container:
                if body.strip():
                    body = rewrite_image_paths(
                        body, activity_host.resolve_path, _serve_image
                    )
                    ui.markdown(body).classes("slumber-instruction")
                else:
                    ui.label("No instruction content.").classes(
                        "slumber-instruction slumber-instruction-empty"
                    )

        activity_host.complete()
