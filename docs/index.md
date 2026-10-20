![SLUMBER logo](assets/logo.png)

# Welcome to SLUMBER

SLUMBER (**S**leep **L**ogging and **U**nsupervised **M**onitoring through **B**io**E**lectrical **R**ecordings) is an open-source Python framework for conducting sleep studies outside the laboratory.

## Why use SLUMBER?

Traditional sleep studies often rely on in-lab supervision and fixed infrastructure. SLUMBER provides a flexible alternative:

- YAML-driven study packages (conditions, phases, activities, pipelines)
- Participant UI (`gui`) or browserless runs (`headless`) driven by one RunEngine
- Plugin architecture for activities and processing units
- Optional extensions (devices, audio, multi-participant backend) via entry points

SLUMBER is intended for researchers who want to run controlled studies in naturalistic (home-based) environments.

---

## Getting started

1. [Installation](getting-started/installation.md) — install and verify
2. [Study Setup](user-guide/study-setup.md) — create a study folder
3. [Running a Study](user-guide/running-a-study.md) — run a condition locally (try `examples/demo/`)

---

## Documentation overview


| Section                                                 | Contents                                 |
| ------------------------------------------------------- | ---------------------------------------- |
| [Getting Started](getting-started/installation.md)      | Install, doctor, first commands          |
| [User Guide](user-guide/index.md)                       | Study setup, validation, run layout, GUI |
| [Reference — Configuration](reference/configuration.md) | `study.yaml`, condition, phase, pipeline |
| [Reference — Plugins](reference/plugins.md)             | Entry points, contracts, built-ins       |
| [Reference — UI](reference/ui.md)                       | `gui` / `headless`, layouts, activities  |
| [Reference — CLI](reference/cli.md)                     | `study` and `doctor`                     |
| [Contributing](about/contributing.md)                   | Development setup and conventions        |


