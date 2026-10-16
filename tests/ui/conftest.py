"""Fixtures for the GUI tests."""

from __future__ import annotations

from collections.abc import Iterator

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
