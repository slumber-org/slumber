"""Condition schema: study procedures, optional page graph, and DAG."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from slumber.schemas.dag import DAG
from slumber.schemas.procedure import Procedure
from slumber.utils.errors import format_validation_error
from slumber.utils.yaml import load_and_validate
from slumber.utils.yaml import EXTENSIONS


class Condition(BaseModel):
    """A single condition: procedures, optional UI page graph, and DAG."""

    name: str = Field(
        ..., min_length=1, description="Condition name (e.g. condition_1)."
    )
    procedures: dict[str, Procedure] | None = Field(
        default=None,
        description=(
            "Optional backend procedure mapping (used by headless and legacy nicegui). "
            "At least one of procedures or page_graph must be provided."
        ),
    )
    page_graph: "PageGraph | None" = Field(
        default=None,
        description=(
            "Optional GUI page graph for UI-specific page/task routing "
            "(used by nicegui2-style backends)."
        ),
    )
    dag: DAG = Field(..., description="Processing DAG for this condition.")

    @model_validator(mode="after")
    def validate_navigation_sources(self) -> "Condition":
        """Require at least one execution/navigation source."""
        has_procedures = bool(self.procedures)
        has_page_graph = self.page_graph is not None
        if not has_procedures and not has_page_graph:
            raise ValueError(
                "condition must define at least one of 'procedures' or 'page_graph'."
            )
        return self


class TaskStep(BaseModel):
    """A task entry in a task_stepper page."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., min_length=1, description="Task plugin key.")
    title: str | None = Field(
        default=None,
        description="Optional display title for this task instance.",
    )
    path: str | None = Field(
        default=None,
        description="Optional asset path relative to study assets_dir.",
    )
    settings: dict[str, object] = Field(
        default_factory=dict,
        description="Task-instance settings passed to the task renderer/plugin.",
    )
    allow_skip: bool = Field(
        default=False,
        description="Whether this task can be skipped in the stepper UI.",
    )


class InteractionPage(BaseModel):
    """A custom interaction page definition."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        default="interaction",
        description="Page type. Must be 'interaction'.",
    )
    title: str | None = Field(default=None, description="Optional page title.")
    path: str | None = Field(
        default=None,
        description="Optional asset path for page content/implementation.",
    )
    settings: dict[str, object] = Field(
        default_factory=dict,
        description="Page-instance settings.",
    )
    routing: dict[str, str] = Field(
        default_factory=dict,
        description="Map event/action keys to destination page ids or 'farewell'.",
    )

    @model_validator(mode="after")
    def validate_type(self) -> "InteractionPage":
        """Ensure the interaction page type is explicit and valid."""
        if self.type != "interaction":
            raise ValueError("interaction pages must set type='interaction'.")
        return self


class TaskStepperPage(BaseModel):
    """A task stepper page definition."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        default="task_stepper",
        description="Page type. Must be 'task_stepper'.",
    )
    title: str | None = Field(default=None, description="Optional page title.")
    tasks: list[TaskStep] = Field(
        ...,
        min_length=1,
        description="Ordered task list shown by the task stepper page.",
    )
    settings: dict[str, object] = Field(
        default_factory=dict,
        description="Page-instance settings.",
    )
    routing: dict[str, str] = Field(
        default_factory=dict,
        description="Map event/action keys to destination page ids or 'farewell'.",
    )

    @model_validator(mode="after")
    def validate_type(self) -> "TaskStepperPage":
        """Ensure the task stepper page type is explicit and valid."""
        if self.type != "task_stepper":
            raise ValueError("task stepper pages must set type='task_stepper'.")
        return self


PageNode = InteractionPage | TaskStepperPage


class PageGraph(BaseModel):
    """GUI page graph for a condition."""

    model_config = ConfigDict(extra="forbid")

    first_page: str = Field(
        ...,
        min_length=1,
        description="Entry page id when this condition begins in the GUI.",
    )
    pages: dict[str, PageNode] = Field(
        ...,
        min_length=1,
        description="Map of page id -> page definition.",
    )

    @model_validator(mode="after")
    def validate_routes(self) -> "PageGraph":
        """Validate page references in first_page and routing destinations."""
        page_ids = set(self.pages.keys())
        if self.first_page not in page_ids:
            raise ValueError(
                f"first_page {self.first_page!r} is not defined in pages: {sorted(page_ids)}."
            )

        for page_id, page in self.pages.items():
            for route_key, destination in page.routing.items():
                if destination == "farewell":
                    continue
                if destination not in page_ids:
                    raise ValueError(
                        "invalid routing target "
                        f"{destination!r} in page {page_id!r} route {route_key!r}; "
                        "target must be another page id or 'farewell'."
                    )
        return self


def load_conditions_from_dir(conditions_dir: Path) -> list[Condition]:
    """Load and validate all condition YAML files from a conditions directory.

    Args:
        conditions_dir: Path to the directory containing condition YAML files.

    Returns:
        List of validated Condition instances, sorted by filename.

    Raises:
        FileNotFoundError: If the conditions directory does not exist.
        ValueError: If any condition file fails validation (message includes path).
    """
    if not conditions_dir.is_dir():
        raise FileNotFoundError(f"Conditions directory not found: {conditions_dir}")
    condition_files = sorted(
        f
        for f in conditions_dir.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONS
    )
    conditions: list[Condition] = []
    for file_path in condition_files:
        try:
            conditions.append(load_and_validate(file_path, Condition))
        except ValidationError as e:
            msg = format_validation_error(
                e, path=file_path, prefix="Condition file error"
            )
            raise ValueError(msg) from e
    return conditions
