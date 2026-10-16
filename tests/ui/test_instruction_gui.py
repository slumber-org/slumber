"""Mounted InstructionActivity checks (require slumber[nicegui])."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("nicegui")

from nicegui import ui
from nicegui.client import Client

from slumber.ui.activities import instruction
from slumber.ui.activities.instruction import InstructionActivity, InstructionSettings

pytestmark = pytest.mark.nicegui


class _Host:
    def __init__(self, container: Any, root: Path) -> None:
        self.container = container
        self.root = root
        self.completed = 0

    def complete(self) -> None:
        self.completed += 1

    def resolve_path(self, path: str) -> Path:
        return self.root / path

    def emit(self, name: str) -> None:
        raise AssertionError(f"unexpected emit {name}")


def _mount(content: str, root: Path = Path("/study")) -> tuple[_Host, Any]:
    container = ui.element("div")
    host = _Host(container, root)
    InstructionActivity(InstructionSettings(content=content)).mount(host)
    return host, container


def _children(container: Any) -> list[Any]:
    return list(container.default_slot.children)


def test_renders_markdown_in_the_slot_and_completes(client: Client) -> None:
    host, container = _mount("# Welcome\n\nHello")

    (markdown,) = _children(container)
    assert isinstance(markdown, ui.markdown)
    assert "slumber-instruction" in markdown.classes
    assert markdown.content == "# Welcome\n\nHello"
    assert host.completed == 1


def test_empty_content_shows_a_note_and_still_completes(client: Client) -> None:
    host, container = _mount("   ")

    (note,) = _children(container)
    assert isinstance(note, ui.label)
    assert note.text == "No instruction content."
    assert "slumber-instruction-empty" in note.classes
    assert host.completed == 1


def test_image_paths_are_resolved_through_the_host_and_served(
    client: Client, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "band.png").write_bytes(b"x")
    monkeypatch.setattr(
        instruction, "_serve_image", lambda path: f"/served/{path.name}"
    )

    _, container = _mount("![The band](assets/band.png)", tmp_path)

    (markdown,) = _children(container)
    assert markdown.content == "![The band](/served/band.png)"


def test_content_from_a_file_gets_the_same_treatment(
    client: Client, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "band.png").write_bytes(b"x")
    page_file = tmp_path / "intro.md"
    page_file.write_text("![The band](assets/band.png)\n", encoding="utf-8")
    monkeypatch.setattr(
        instruction, "_serve_image", lambda path: f"/served/{path.name}"
    )

    _, container = _mount(str(page_file), tmp_path)

    (markdown,) = _children(container)
    assert markdown.content == "![The band](/served/band.png)\n"
