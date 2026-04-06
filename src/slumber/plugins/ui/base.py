"""Base class for UI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from slumber.runtime.run import RunContext
    from slumber.schemas.condition import Condition
    from slumber.schemas.study import Study


class UIBackend(ABC):
    """UI backend: parse `study.ui.settings`, then run the participant UI.

    Subclasses set ``ui_settings_model`` to a Pydantic model, or ``None`` if
    the backend accepts no settings (manifest must omit or leave ``ui.settings`` empty).
    """

    ui_settings_model: ClassVar[type[BaseModel] | None] = None

    _settings: BaseModel | None

    def __init__(self) -> None:
        model = self.ui_settings_model
        self._settings = model() if model is not None else None

    def configure(self, settings: dict[str, Any]) -> None:
        """Validate and store settings from the study manifest."""
        model = self.ui_settings_model
        if model is None:
            if settings:
                raise ValueError(
                    "This UI backend does not support ui.settings; "
                    "remove ui.settings from study.yaml or use a backend that accepts settings."
                )
            return
        self._settings = model.model_validate(settings)

    @abstractmethod
    def run(
        self,
        study: "Study",
        condition: "Condition",
        context: "RunContext",
    ) -> None:
        """Run the full UI lifecycle for a condition."""
        ...
