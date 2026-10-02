"""Mark Supabase-stack tests so core-only CI can deselect them.

``test_get_database_url.py`` stays unmarked: it only exercises
:mod:`slumber_supabase.utils` and does not require the ``supabase`` PyPI package.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SUPABASE_TESTS_ROOT = Path(__file__).resolve().parent


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        path = Path(item.path).resolve()
        if not (
            path.parent == _SUPABASE_TESTS_ROOT or _SUPABASE_TESTS_ROOT in path.parents
        ):
            continue
        if path.name == "test_get_database_url.py":
            continue
        item.add_marker(pytest.mark.supabase)
