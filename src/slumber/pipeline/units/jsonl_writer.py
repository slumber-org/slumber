"""Append pipeline messages to a JSONL file (demo / tests)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TextIO

import ezmsg.core as ez
from pydantic import Field

from slumber.pipeline.units.utils import Settings


def _to_jsonable(message: Any) -> Any:
    """Convert *message* to a JSON-serializable value."""
    if hasattr(message, "model_dump"):
        return message.model_dump()
    if isinstance(message, (str, int, float, bool, type(None))):
        return message
    if isinstance(message, (list, tuple)):
        return [_to_jsonable(item) for item in message]
    if isinstance(message, dict):
        return {str(key): _to_jsonable(value) for key, value in message.items()}
    return str(message)


class JsonlWriterSettings(Settings):
    """Settings for :class:`JsonlWriterUnit`."""

    path: str = Field(..., min_length=1, description="Output JSONL path.")


class JsonlWriterUnit(ez.Unit):
    """Append each message received on ``INPUT`` to ``settings.path``."""

    SETTINGS = JsonlWriterSettings

    INPUT = ez.InputStream(Any)

    async def initialize(self) -> None:
        """Open the output file for append (create parents if needed)."""
        path = Path(self.SETTINGS.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # ezmsg initialize runs once per unit process; sync open matches MessageLogger.
        self._file: TextIO = path.open("a", encoding="utf-8")  # noqa: ASYNC230

    async def shutdown(self) -> None:
        """Close the output file if it was opened."""
        file = getattr(self, "_file", None)
        if file is not None and not file.closed:
            file.close()

    @ez.subscriber(INPUT)
    async def on_message(self, message: Any) -> None:
        """Serialize *message* as one JSON line and flush."""
        line = json.dumps(_to_jsonable(message), ensure_ascii=False)
        self._file.write(f"{line}\n")
        self._file.flush()
