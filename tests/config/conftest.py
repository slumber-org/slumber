"""Shared fixtures for config tests."""

import pytest


@pytest.fixture
def minimal_condition_yaml() -> str:
    """Minimal valid condition YAML for tests that need a condition file."""
    return """
name: condition_1
procedures:
  pre_sleep:
    tasks:
      - type: instruction
        title: Read instructions
dag:
  components:
    - name: MASTER
      unit_type: Master
  connections: []
  process_components: []
"""
