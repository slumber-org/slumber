![SLUMBER](docs/assets/logo-lockup.png)



![Tests](https://github.com/slumber-org/slumber/actions/workflows/tests.yml/badge.svg)
![Ruff](https://github.com/slumber-org/slumber/actions/workflows/ruff.yaml/badge.svg)
![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)
![Docs](https://img.shields.io/badge/docs-slumber--org.github.io-blue)



**S**leep **L**ogging and **U**nsupervised **M**onitoring through **B**io**E**lectrical **R**ecordings

Open-source, Python-based framework for designing, deploying and managing fully automated sleep experiments in the home environment.

## Features

- **Study configuration** — Validated structure for reproducible runs in a study folder: study-wide settings, experimental conditions, and supporting assets.
- **Real-time pipelines** — Connected units for stream-based data acquisition, processing, inference, and control, including researcher-defined protocol actions.
- **Participant interface** — Activities in researcher-defined order with customisable layouts for instructions, device setup, calibration, behavioural tasks, and assessments.
- **Researcher interface** — Command-line tools for study setup, launch, and diagnostics.
- **Study management** — Optional study backend (Supabase extension) for remote participant management, sessions, and multi-night scheduling.
- **Data storage and transfer** — Structured records of signals, responses, events, and logs; local storage in core, with richer formats and optional remote transfer.
- **Device integration** — Wearable sensors and devices for physiological recording and stimulus delivery.
- **Plugin extensions** — Pluggable modules for device integrations, processing units, and participant activities.

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10–3.13.

```bash
git clone https://github.com/slumber-org/slumber.git
cd slumber
uv sync
```

For the GUI participant UI:

```bash
uv sync --extra nicegui
```

Verify the environment:

```bash
uv run slumber doctor
```

> **Warning:** SLUMBER is not published on PyPI yet. The `slumber` package currently on PyPI is an unrelated project — do not `pip install slumber`.

## Demo

Validate and run the bundled demo study:

```bash
uv run slumber study validate --study-dir examples/demo
uv run slumber study run --study-dir examples/demo --condition demo --ui headless
```

With the NiceGUI extra installed:

```bash
uv run slumber study run --study-dir examples/demo --condition demo --ui gui
```

## Documentation

Full documentation: [https://slumber-org.github.io/slumber/](https://slumber-org.github.io/slumber/)

## Survey and updates

- **[Take our brief survey](https://slumber-org.github.io/slumber/survey/)** — help shape SLUMBER by sharing how you run home-based sleep studies, which tools you use, and what you need next.
- **[Sign up for updates](https://slumber-org.github.io/slumber/updates/)** — get release announcements, roadmap progress, and news when the public alpha is ready for broader use.

## Status and roadmap

SLUMBER is in public **alpha**. Early specialised builds are already used in running studies; this repository is the general framework toward a public release.

See the [roadmap](https://slumber-org.github.io/slumber/about/roadmap/) for planned work.

## Contributing and support

- Contribution guide: [docs/about/contributing.md](docs/about/contributing.md)
- Bugs and feature requests: [GitHub Issues](https://github.com/slumber-org/slumber/issues)

