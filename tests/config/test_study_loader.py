"""Tests for resolve_study_dir, init_study, and load_study (slumber.config)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from slumber.config import init_study, load_study, resolve_study_dir


class TestDiscoverStudyDir:
    """Tests for resolve_study_dir."""

    def test_returns_cwd_when_study_yaml_in_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("STUDY_DIR", raising=False)
        (tmp_path / "study.yaml").write_text("study_id: s\nname: S\n", encoding="utf-8")
        with patch.object(Path, "cwd", return_value=tmp_path):
            found = resolve_study_dir()
        assert found == tmp_path

    def test_raises_when_no_study_yaml_in_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("STUDY_DIR", raising=False)
        with patch.object(Path, "cwd", return_value=tmp_path):
            with pytest.raises(FileNotFoundError, match="Study manifest"):
                resolve_study_dir()

    def test_returns_study_dir_when_explicit_and_has_manifest(
        self, tmp_path: Path
    ) -> None:
        study_dir = tmp_path / "my-study"
        study_dir.mkdir()
        (study_dir / "study.yaml").write_text(
            "study_id: my-study\nname: My Study\n", encoding="utf-8"
        )
        found = resolve_study_dir(study_dir=study_dir)
        assert found == study_dir.resolve()

    def test_raises_when_explicit_dir_has_no_manifest(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(FileNotFoundError, match="Study manifest"):
            resolve_study_dir(study_dir=empty)


class TestLoadStudy:
    """Tests for load_study."""

    def test_loads_manifest_and_conditions(
        self, tmp_path: Path, minimal_condition_yaml: str
    ) -> None:
        study_path = init_study(
            tmp_path, "s1", create_env_example=False, create_gitignore=False
        )
        cond_path = study_path / "conditions" / "control.yaml"
        cond_path.write_text(minimal_condition_yaml, encoding="utf-8")

        study = load_study(study_path)
        assert study.study_id == "s1"
        conditions = study.conditions
        assert len(conditions) == 1
        assert conditions[0].name == "condition_1"

    def test_loads_multiple_conditions_sorted_by_filename(self, tmp_path: Path) -> None:
        study_path = init_study(
            tmp_path, "s1", create_env_example=False, create_gitignore=False
        )
        for name, cond_name in [("a.yaml", "cond_a"), ("b.yaml", "cond_b")]:
            (study_path / "conditions" / name).write_text(
                f"""
name: {cond_name}
procedures:
  pre_sleep:
    steps:
      - task: instruction
dag:
  components:
    - name: MASTER
      unit_type: M
  connections: []
  process_components: []
""",
                encoding="utf-8",
            )
        study = load_study(study_path)
        conditions = study.conditions
        assert len(conditions) == 2
        assert conditions[0].name == "cond_a"
        assert conditions[1].name == "cond_b"

    def test_raises_file_not_found_when_conditions_dir_missing(
        self, tmp_path: Path
    ) -> None:
        study_path = tmp_path / "orphan"
        study_path.mkdir()
        (study_path / "study.yaml").write_text(
            "study_id: x\nname: X\nconditions_dir: no_such_dir\n",
            encoding="utf-8",
        )
        with pytest.raises(FileNotFoundError) as exc_info:
            load_study(study_path)
        assert "no_such_dir" in str(exc_info.value)

    def test_invalid_condition_raises_value_error_with_path(
        self, tmp_path: Path
    ) -> None:
        study_path = init_study(
            tmp_path, "s1", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "bad.yaml").write_text(
            "name: x\n# procedures missing\n", encoding="utf-8"
        )
        with pytest.raises(ValueError) as exc_info:
            load_study(study_path)
        assert "Condition file error" in str(exc_info.value)
        assert "bad.yaml" in str(exc_info.value)
