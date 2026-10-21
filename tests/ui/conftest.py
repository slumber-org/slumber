"""Fixtures for the GUI tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
from typing import Any

import pytest


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[object]:
    """A NiceGUI page to build elements in, without a server or a browser."""
    pytest.importorskip("nicegui")
    from nicegui import ui
    from nicegui.client import Client
    from nicegui.page import page

    # Scrolling the card to the top needs a connected browser.
    monkeypatch.setattr(ui, "run_javascript", lambda *args, **kwargs: None)
    with Client(page("/")) as client:
        yield client


@pytest.fixture
def press(client: object, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    """Press a configurable button by its label, the way a click does.

    The click handler of every button built from settings is recorded by its
    label, so a test can run it without a browser. A label shown again later (a
    toggle that swapped back) uses the newest button.
    """
    from slumber.ui.widgets import buttons as module

    handlers: dict[str, Callable[[], Any]] = {}

    def recording(real: Callable[..., Any]) -> Callable[..., Any]:
        def build(label: str, *, on_click: Callable[[], Any], **kwargs: Any) -> Any:
            handlers[label] = on_click
            return real(label, on_click=on_click, **kwargs)

        return build

    monkeypatch.setattr(module, "primary_button", recording(module.primary_button))
    monkeypatch.setattr(module, "outline_button", recording(module.outline_button))

    def press_button(label: str) -> None:
        asyncio.run(handlers[label]())

    return press_button
