"""Tests for study folder init (init_study and slumber study init CLI)."""

from importlib.resources import as_file, files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.schemas.study import DEFAULT_ASSETS_DIR_NAME, DEFAULT_CONDITIONS_DIR_NAME
from slumber.study.init import (
    ENV_EXAMPLE_FILENAME,
    STUDY_YAML_FILENAME,
    init_study,
)


class TestInitStudy:
    """Tests for init_study()."""

    def test_creates_layout(self, tmp_path: Path) -> None:
        """Init creates study_id dir with study.yaml, conditions/, assets/."""
        study_path = init_study(
            tmp_path, "my-study", create_env_example=False, create_gitignore=False
        )
        assert study_path == tmp_path / "my-study"
        assert study_path.is_dir()
        assert (study_path / STUDY_YAML_FILENAME).is_file()
        assert (study_path / DEFAULT_CONDITIONS_DIR_NAME).is_dir()
        assert (study_path / DEFAULT_ASSETS_DIR_NAME).is_dir()

    def test_study_yaml_content(self, tmp_path: Path) -> None:
        """Generated study.yaml contains study_id and name."""
        study_path = init_study(
            tmp_path,
            "ld-2025",
            name="Lucid Dreaming Pilot",
            create_env_example=False,
            create_gitignore=False,
        )
        content = (study_path / STUDY_YAML_FILENAME).read_text(encoding="utf-8")
        assert "study_id: ld-2025" in content
        assert "name: Lucid Dreaming Pilot" in content
        assert "conditions_dir: conditions" in content
        assert "backend: headless" in content

    def test_name_defaults_to_study_id(self, tmp_path: Path) -> None:
        """When name is omitted, study name equals study_id."""
        study_path = init_study(
            tmp_path, "foo-study", create_env_example=False, create_gitignore=False
        )
        content = (study_path / STUDY_YAML_FILENAME).read_text(encoding="utf-8")
        assert "name: foo-study" in content

    def test_raises_when_dir_exists(self, tmp_path: Path) -> None:
        """FileExistsError when study directory already exists."""
        (tmp_path / "existing-study").mkdir()
        with pytest.raises(FileExistsError) as exc_info:
            init_study(
                tmp_path,
                "existing-study",
                create_env_example=False,
                create_gitignore=False,
            )
        assert "already exists" in str(exc_info.value)

    def test_creates_env_example_inside_study_folder_when_requested(
        self, tmp_path: Path
    ) -> None:
        """With create_env_example=True, .env.example is created inside the study folder."""
        study_path = init_study(
            tmp_path, "s1", create_env_example=True, create_gitignore=False
        )
        env_example = study_path / ".env.example"
        assert env_example.is_file()
        content = env_example.read_text(encoding="utf-8")
        assert "SUPABASE_URL" in content
        ref = files("slumber.study.templates") / ENV_EXAMPLE_FILENAME
        with as_file(ref) as path:
            expected = path.read_text(encoding="utf-8")
        assert content == expected
        assert study_path == tmp_path / "s1"

    def test_skips_env_example_when_requested(self, tmp_path: Path) -> None:
        """With create_env_example=False, .env.example is not created."""
        study_path = init_study(
            tmp_path, "s1", create_env_example=False, create_gitignore=False
        )
        assert not (study_path / ".env.example").exists()

    def test_creates_gitignore_inside_study_folder_when_requested(
        self, tmp_path: Path
    ) -> None:
        """With create_gitignore=True, .gitignore is created inside the study folder."""
        study_path = init_study(
            tmp_path, "s1", create_env_example=False, create_gitignore=True
        )
        gitignore = study_path / ".gitignore"
        assert gitignore.is_file()
        content = gitignore.read_text(encoding="utf-8")
        assert ".env" in content
        assert ".env.*" in content

    def test_skips_gitignore_when_requested(self, tmp_path: Path) -> None:
        """With create_gitignore=False, .gitignore is not created."""
        study_path = init_study(
            tmp_path, "s1", create_env_example=False, create_gitignore=False
        )
        assert not (study_path / ".gitignore").exists()


class TestStudyInitCLI:
    """Tests for slumber study init command (non-interactive)."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_non_interactive_creates_layout(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """CLI with --base-dir and --study-id creates correct layout without prompts."""
        result = runner.invoke(
            app,
            [
                "study",
                "init",
                "--base-dir",
                str(tmp_path),
                "--study-id",
                "cli-study",
                "--name",
                "cli-study",
            ],
        )
        assert result.exit_code == 0
        study_path = tmp_path / "cli-study"
        assert study_path.is_dir()
        assert (study_path / STUDY_YAML_FILENAME).is_file()
        assert (study_path / DEFAULT_CONDITIONS_DIR_NAME).is_dir()
        assert (study_path / DEFAULT_ASSETS_DIR_NAME).is_dir()
        assert "Created study at" in result.output

    def test_non_interactive_creates_env_example_and_gitignore_inside_study_folder(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """CLI creates .env.example and .gitignore inside the study folder by default."""
        result = runner.invoke(
            app,
            [
                "study",
                "init",
                "--base-dir",
                str(tmp_path),
                "--study-id",
                "proj-study",
                "--name",
                "proj-study",
            ],
        )
        assert result.exit_code == 0
        study_path = tmp_path / "proj-study"
        assert (study_path / ".env.example").is_file()
        assert (study_path / ".gitignore").is_file()
        assert "SUPABASE_URL" in (study_path / ".env.example").read_text(
            encoding="utf-8"
        )
        content = (study_path / ".gitignore").read_text(encoding="utf-8")
        assert ".env" in content
        assert ".env.*" in content

    def test_non_interactive_with_name(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI --name is reflected in study.yaml."""
        result = runner.invoke(
            app,
            [
                "study",
                "init",
                "--base-dir",
                str(tmp_path),
                "--study-id",
                "x",
                "--name",
                "My Study Name",
            ],
        )
        assert result.exit_code == 0
        content = (tmp_path / "x" / STUDY_YAML_FILENAME).read_text(encoding="utf-8")
        assert "name: My Study Name" in content

    def test_exits_when_dir_exists(self, runner: CliRunner, tmp_path: Path) -> None:
        """CLI exits with code 1 when study directory already exists."""
        (tmp_path / "existing").mkdir()
        result = runner.invoke(
            app,
            [
                "study",
                "init",
                "--base-dir",
                str(tmp_path),
                "--study-id",
                "existing",
                "--name",
                "existing",
            ],
        )
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_no_env_example_omits_env_example_in_study_folder(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """CLI --no-env-example does not create .env.example inside the study folder."""
        result = runner.invoke(
            app,
            [
                "study",
                "init",
                "--base-dir",
                str(tmp_path),
                "--study-id",
                "y",
                "--name",
                "y",
                "--no-env-example",
            ],
        )
        assert result.exit_code == 0
        assert not (tmp_path / "y" / ".env.example").exists()

    def test_no_gitignore_skips_gitignore_in_study_folder(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """CLI --no-gitignore does not create .gitignore inside the study folder."""
        result = runner.invoke(
            app,
            [
                "study",
                "init",
                "--base-dir",
                str(tmp_path),
                "--study-id",
                "z",
                "--name",
                "z",
                "--no-gitignore",
            ],
        )
        assert result.exit_code == 0
        assert not (tmp_path / "z" / ".gitignore").exists()
