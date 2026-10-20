"""Tests for resolve_settings and placeholder expansion."""

from __future__ import annotations

from pathlib import Path

from slumber.config.paths import (
    expand_placeholders,
    resolve_path,
    resolve_settings,
    run_placeholders,
    study_root_placeholders,
)


class TestExpandPlaceholders:
    def test_expands_known_keys(self) -> None:
        assert (
            expand_placeholders(
                "{assets_dir}/intro.md",
                {"assets_dir": "/study/assets"},
            )
            == "/study/assets/intro.md"
        )

    def test_leaves_unknown_keys(self) -> None:
        assert (
            expand_placeholders("{run_dir}/out.jsonl", {"assets_dir": "/a"})
            == "{run_dir}/out.jsonl"
        )


class TestResolvePath:
    def test_placeholders_expand_and_the_result_is_a_path(self, tmp_path: Path) -> None:
        resolved = resolve_path(
            "{assets_dir}/a.png",
            study_root=tmp_path,
            placeholders={"assets_dir": str(tmp_path / "assets")},
        )

        assert resolved == tmp_path / "assets" / "a.png"

    def test_relative_path_is_relative_to_the_study_root(self, tmp_path: Path) -> None:
        resolved = resolve_path("assets/a.png", study_root=tmp_path, placeholders={})

        assert resolved == (tmp_path / "assets" / "a.png").resolve()

    def test_absolute_path_is_unchanged(self, tmp_path: Path) -> None:
        absolute = tmp_path / "elsewhere" / "a.png"

        resolved = resolve_path(
            str(absolute), study_root=tmp_path / "study", placeholders={}
        )

        assert resolved == absolute

    def test_any_text_is_treated_as_a_path(self, tmp_path: Path) -> None:
        resolved = resolve_path("Next", study_root=tmp_path, placeholders={})

        assert resolved == (tmp_path / "Next").resolve()


class TestResolveSettings:
    def test_assets_placeholder_and_relative(self, tmp_path: Path) -> None:
        assets = tmp_path / "assets"
        assets.mkdir()
        placeholders = study_root_placeholders(
            tmp_path,
            study_id="s1",
            study_name="Study",
            assets_dir="assets",
        )
        resolved = resolve_settings(
            {"content": "{assets_dir}/intro.md", "label": "Hello"},
            study_root=tmp_path,
            placeholders=placeholders,
        )
        assert resolved["content"] == str((assets / "intro.md").resolve())
        assert resolved["label"] == "Hello"

    def test_relative_path_without_placeholder(self, tmp_path: Path) -> None:
        resolved = resolve_settings(
            {"content": "assets/intro.md"},
            study_root=tmp_path,
            placeholders={},
        )
        assert resolved["content"] == str((tmp_path / "assets" / "intro.md").resolve())

    def test_absolute_path_unchanged(self, tmp_path: Path) -> None:
        absolute = "/tmp/clock.jsonl"
        resolved = resolve_settings(
            {"path": absolute},
            study_root=tmp_path,
            placeholders={},
        )
        assert resolved["path"] == absolute

    def test_run_dir_left_when_missing_at_validate(self, tmp_path: Path) -> None:
        placeholders = study_root_placeholders(
            tmp_path,
            study_id="s1",
            study_name="Study",
            assets_dir="assets",
        )
        resolved = resolve_settings(
            {"path": "{run_dir}/clock.jsonl"},
            study_root=tmp_path,
            placeholders=placeholders,
        )
        assert resolved["path"] == "{run_dir}/clock.jsonl"

    def test_run_placeholders_expand_run_dir(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "runs" / "run-1"
        run_dir.mkdir(parents=True)
        placeholders = run_placeholders(
            tmp_path,
            study_id="s1",
            study_name="Study",
            assets_dir="assets",
            run_dir=run_dir,
            run_id="run-1",
            condition_id="demo",
        )
        resolved = resolve_settings(
            {"path": "{run_dir}/clock.jsonl"},
            study_root=tmp_path,
            placeholders=placeholders,
        )
        assert resolved["path"] == str((run_dir / "clock.jsonl").resolve())
