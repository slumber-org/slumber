"""Root pytest hooks (apply to core and extension test trees)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent
_SUPABASE_TESTS = _REPO_ROOT / "extensions" / "slumber-supabase" / "tests"


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Skip slumber-supabase tests when running core-only CI."""
    if os.environ.get("SLUMBER_PYTEST_CORE_ONLY") != "1":
        return None
    try:
        path = collection_path.resolve()
        path.relative_to(_SUPABASE_TESTS.resolve())
    except (OSError, ValueError):
        return None
    return True
