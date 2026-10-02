"""Shared fixtures for the test suite."""

import os
from pathlib import Path

import pytest

# Core-only CI (no optional extras): skip collecting modules that import
# nicegui/starlette or SQLModel/SQLAlchemy before markers are applied.
if os.environ.get("SLUMBER_PYTEST_CORE_ONLY") == "1":
    _here = Path(__file__).resolve().parent
    collect_ignore = [
        str(_here / "ext" / "ui"),
        str(_here / "slumber_supabase" / "models"),
        str(_here / "slumber_supabase" / "auth"),
        str(_here / "slumber_supabase" / "backend"),
    ]


@pytest.fixture
def minimal_condition_yaml() -> str:
    """Minimal valid condition YAML for tests that need a condition file."""
    return """
name: condition_1
entry: setup
phases:
  - id: setup
    layout:
      type: stepper
    activities:
      - id: welcome
        type: instruction
        settings:
          content: Hello
    on:
      - event: phase_completed
        do:
          - end_run
pipelines: []
"""
