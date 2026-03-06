"""Tests for config error formatting."""

from pathlib import Path

import pytest
from pydantic import BaseModel, Field, ValidationError

from slumber.utils.errors import format_validation_error


class _SampleModel(BaseModel):
    """Minimal model for testing validation errors."""

    required_str: str = Field(..., min_length=1)
    optional_int: int = 0


class TestFormatValidationError:
    """Tests for format_validation_error."""

    def test_includes_path_when_given(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _SampleModel.model_validate({"optional_int": "not_an_int"})
        out = format_validation_error(
            exc_info.value, path=Path("study.yaml"), prefix="Study manifest error"
        )
        assert "Study manifest error: study.yaml" in out
        assert "optional_int" in out

    def test_includes_all_error_locations(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _SampleModel.model_validate({})
        out = format_validation_error(exc_info.value)
        assert "required_str" in out
        assert "msg" in out or "error" in out.lower()

    def test_no_path_when_path_is_none(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            _SampleModel.model_validate({"required_str": ""})
        out = format_validation_error(exc_info.value, path=None, prefix="Error")
        assert out.startswith("Error:")
        assert "required_str" in out or "min_length" in out or "str" in out
