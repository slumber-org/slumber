"""Tests for run directory layout (resolve_run_dir, create_run_dir)."""

from pathlib import Path


from slumber.runtime import RunContext, create_run_dir, resolve_run_dir
from slumber.schemas.study import RunLayout, Study


def _study(
    layout: str = "sub-{participant_id}/ses-{session_id}/run-{run_id}",
    base: str = "runs",
) -> Study:
    return Study(
        study_id="s1",
        name="S1",
        runs=RunLayout(base_directory=base, layout=layout),
    )


def _ctx(**overrides: str) -> RunContext:
    defaults = dict(
        study_id="s1",
        participant_id="001",
        session_id="ses01",
        run_id="r001",
        condition_id="ctrl",
    )
    return RunContext(**{**defaults, **overrides})  # type: ignore[arg-type]


class TestResolveRunDir:
    def test_default_layout(self, tmp_path: Path) -> None:
        result = resolve_run_dir(_study(), _ctx(), tmp_path)
        assert (
            result
            == (tmp_path / "runs" / "sub-001" / "ses-ses01" / "run-r001").resolve()
        )

    def test_custom_layout(self, tmp_path: Path) -> None:
        study = _study(layout="{study_id}/{condition_id}/{run_id}")
        result = resolve_run_dir(study, _ctx(), tmp_path)
        assert result == (tmp_path / "runs" / "s1" / "ctrl" / "r001").resolve()

    def test_custom_base_directory(self, tmp_path: Path) -> None:
        study = _study(base="output", layout="{participant_id}")
        result = resolve_run_dir(study, _ctx(participant_id="P42"), tmp_path)
        assert result == (tmp_path / "output" / "P42").resolve()

    def test_does_not_create_directory(self, tmp_path: Path) -> None:
        result = resolve_run_dir(_study(), _ctx(), tmp_path)
        assert not result.exists()

    def test_returns_absolute_path(self, tmp_path: Path) -> None:
        result = resolve_run_dir(_study(), _ctx(), tmp_path)
        assert result.is_absolute()


class TestCreateRunDir:
    def test_creates_directory(self, tmp_path: Path) -> None:
        result = create_run_dir(_study(), _ctx(), tmp_path)
        assert result.is_dir()

    def test_returns_same_path_as_resolve(self, tmp_path: Path) -> None:
        study = _study()
        ctx = _ctx()
        result = create_run_dir(study, ctx, tmp_path)
        assert result == resolve_run_dir(study, ctx, tmp_path)

    def test_creates_nested_parents(self, tmp_path: Path) -> None:
        study = _study(layout="a/b/c/{run_id}")
        result = create_run_dir(study, _ctx(), tmp_path)
        assert result.is_dir()

    def test_idempotent(self, tmp_path: Path) -> None:
        study = _study()
        ctx = _ctx()
        create_run_dir(study, ctx, tmp_path)
        result = create_run_dir(study, ctx, tmp_path)
        assert result.is_dir()
