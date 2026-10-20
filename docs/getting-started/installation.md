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
  — nicegui                      not installed (optional; ...)

✓ No issues found.
```

A `✗` next to a required check means that feature will not work until fixed. Optional skips (`—`) are fine unless you need that feature.

## Quick start

```bash
# Create a study folder
uv run slumber study init --base-dir . --study-id my-study --name "My Study"

# Or try the bundled demo
uv run slumber study validate --study-dir examples/demo
uv run slumber study run --study-dir examples/demo --condition demo --ui headless
```

From here:

1. [Study Setup](../user-guide/study-setup.md) — add conditions and assets
2. [Running a Study](../user-guide/running-a-study.md) — GUI or headless run
3. [Configuration reference](../reference/configuration.md) — phases, pipelines, PluginSpec

A remote backend is not required for local study run.
