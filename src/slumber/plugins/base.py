"""Shared plugin base for activities, layouts, and UI adapters."""

from __future__ import annotations

from abc import ABC
from typing import ClassVar

from pydantic import BaseModel


class ConfiguredPlugin(ABC):
    """Shared ``settings_model`` contract for activities, layouts, and UI adapters.

    Subclasses set ``settings_model`` to a Pydantic model used to validate
    ``PluginSpec.settings``, or ``None`` when the plugin accepts no settings.
    """

    settings_model: ClassVar[type[BaseModel] | None] = None

    def __init__(self, settings: BaseModel | None = None) -> None:
        self.settings = settings
