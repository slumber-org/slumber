"""NiceGUI plugin tests require the ``nicegui`` optional dependency."""

from __future__ import annotations

import pytest

pytest.importorskip("nicegui")

pytestmark = pytest.mark.nicegui
