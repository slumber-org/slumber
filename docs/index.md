# Welcome to SLUMBER

SLUMBER (**S**leep **L**ogging and **U**nsupervised **M**onitoring through **B**io**E**lectrical **R**ecordings) is an open-source, Python-based framework designed for conducting sleep studies outside of the laboratory environment.

## Why use SLUMBER?

Traditional sleep studies often rely on in-lab supervision and fixed-infrastructure hardware. SLUMBER provides a flexible alternative by offering:

- Real-time acquisition of physiological signals through wearable devices
- Automated guidance for study participants through calibration, instructions, and nightly procedures
- Configurable experimental protocols, including multi-night scheduling and condition assignment
- Support for stimulus delivery (e.g., sound) during sleep based on incoming physiological data
- Integrated logging for reproducibility, data auditing, and study validation

SLUMBER is intended for researchers who want to run controlled studies in naturalistic (home-based) environments, without direct supervision.

---

## Getting started

New to SLUMBER? Start here:

1. [Installation and Setup](getting-started/installation-setup.md) — install, configure Supabase, verify
2. [Study Setup](user-guide/study-setup.md) — create your first study folder
3. [Running a Study](user-guide/study-run.md) — full researcher workflow with walkthrough

---

## Documentation overview

| Section | Contents |
|---------|----------|
| [Getting Started](getting-started/installation-setup.md) | Install, Supabase setup, environment config, first commands |
| [User Guide](user-guide/index.md) | Study setup, condition sync, run layout, CLI reference |
| [Reference — Schemas](reference/schemas.md) | `study.yaml`, condition, procedure, DAG field reference |
| [Reference — Plugins](reference/plugins.md) | Entry-point groups, plugin contracts, built-in plugins |
| [Reference — Backend](reference/backend.md) | Supabase/Postgres, migrations, auth, participant/session management |
| [Contributing](about/contributing.md) | Development setup, git flow, testing and documentation conventions |
