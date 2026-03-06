"""Format validation and other errors for CLI/logs."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError


def format_validation_error(
    error: ValidationError,
    *,
    path: Path | str | None = None,
    prefix: str = "Validation error",
) -> str:
    """Format a Pydantic ValidationError with optional file path and clear messages.

    Produces path-specific, human-readable output suitable for CLI or logs.

    Args:
        error: The ValidationError from model_validate() or similar.
        path: Optional path to the config file (study.yaml or condition file).
        prefix: Short label before the path (e.g. "Validation error").

    Returns:
        Multi-line string: path (if given), then each error location and message.
    """
    lines: list[str] = []
    lines.append(f"{prefix}: {path}" if path else prefix + ":")

    for err in error.errors():
        loc = " -> ".join(str(x) for x in err["loc"])
        msg = err.get("msg", "validation error")
        lines.append(f"  {loc}: {msg}")

    return "\n".join(lines)
