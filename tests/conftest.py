"""Shared fixtures for the test suite."""

from __future__ import annotations

import pytest


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
