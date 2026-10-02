"""Pipeline package: managers and core units."""

from __future__ import annotations

from typing import Any

__all__ = ["PipelineManager"]


def __getattr__(name: str) -> Any:
    """Lazy-load symbols so ``pipeline.units`` imports do not cycle via manager."""
    if name == "PipelineManager":
        from slumber.pipeline.manager import PipelineManager

        return PipelineManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
