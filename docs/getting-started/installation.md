# Installation

This guide walks you through installing SLUMBER so you can create a study and run it locally.

## System requirements

- **Python 3.10–3.13** (3.12+ recommended for development)
- **[uv](https://docs.astral.sh/uv/)** — recommended package manager; used in all examples below

## Installing SLUMBER

### From source

```bash
git clone https://github.com/slumber-org/slumber.git
cd slumber
uv sync
```

For the GUI participant UI:

```bash
uv sync --extra nicegui
```

Each `uv sync` makes your installation match that exact command. Plain `uv sync` installs only the core packages, and uninstalls the GUI dependency if you added it before. So whenever you run `uv sync` again, for example after pulling new changes, include `--extra nicegui`.

For a full CI-like install (all extras + dev):

```bash
uv sync --all-extras --dev
```

!!! warning "Not published on PyPI yet"
    The `slumber` package currently on PyPI is an unrelated project, so do not `pip install slumber`.

## Verify the installation

```bash
uv run slumber doctor
```

Expected output when dependencies are present:

```
Environment
  — STUDY_DIR                    not set (optional; ...)
  — PARTICIPANT_ID               not set (optional; ...)

Dependencies
  ✓ ezmsg                        installed
  ✓ nicegui                      installed

✓ No issues found.
```

A `✗` next to a required check means that feature will not work until fixed. Optional skips (`—`) are fine unless you need that feature.

## Next steps

Run an example study from start to finish in [Your first study](first-study.md).
