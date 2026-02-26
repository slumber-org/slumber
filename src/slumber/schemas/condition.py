"""Condition schema: study-specific procedures and DAG."""

from pydantic import BaseModel, Field

from slumber.schemas.dag import DAG
from slumber.schemas.procedure import Procedure


class Condition(BaseModel):
    """A single condition: named procedures plus DAG."""

    name: str = Field(
        ..., min_length=1, description="Condition name (e.g. condition_1)."
    )
    procedures: dict[str, Procedure] = Field(
        ...,
        min_length=1,
        description="Mapping from procedure name to Procedure (e.g. pre_sleep, awakening, post_sleep, etc.).",
    )
    dag: DAG = Field(..., description="Processing DAG for this condition.")
