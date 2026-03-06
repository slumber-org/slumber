"""Plugin-related exceptions."""

from __future__ import annotations


class PluginNotFoundError(LookupError):
    """Raised when a plugin is requested by key but not found in the registry."""

    def __init__(self, group: str, key: str, available: list[str]) -> None:
        self.group = group
        self.key = key
        self.available = available
        super().__init__(
            f"Plugin {group!r} not found for key {key!r}. "
            f"Available: {', '.join(sorted(available)) or '(none)'}."
        )
