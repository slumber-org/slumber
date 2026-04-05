"""Tests for RunContext and layout placeholder keys."""

import dataclasses

from slumber.runtime.run import VALID_RUN_LAYOUT_KEYS, RunContext


def test_valid_run_layout_keys_match_run_context_fields() -> None:
    assert VALID_RUN_LAYOUT_KEYS == frozenset(
        f.name for f in dataclasses.fields(RunContext)
    )
