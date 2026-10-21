![SLUMBER logo](assets/logo.png){width=200}

# Welcome to SLUMBER

SLUMBER (**S**leep **L**ogging and **U**nsupervised **M**onitoring through **B**io**E**lectrical **R**ecordings) is an open-source Python framework for conducting sleep studies outside the laboratory.

## Why SLUMBER?

- **Laboratory limits**: Equipment, facilities and overnight supervision limit how many people a sleep study can include, and sleep in a laboratory may differ from sleep at home.
- **Wearables enable home studies**: Lightweight devices that participants put on themselves make high-quality sleep recordings possible at home, night after night.
- **Automation requires software**: Without a researcher in the room, software has to run the protocol: guide the participant, analyse the recording in real time, deliver stimulation and collect the data.

SLUMBER is that software, for researchers who want to run controlled sleep studies in participants' homes.

## What SLUMBER offers

- **Study configuration** — Validated structure for reproducible runs in a study folder: study-wide settings, experimental conditions, and supporting assets.
- **Real-time pipelines** — Connected units for stream-based data acquisition, processing, inference, and control, including researcher-defined protocol actions.
- **Participant interface** — Activities in researcher-defined order with customisable layouts for instructions, device setup, calibration, behavioural tasks, and assessments.
- **Researcher interface** — Command-line tools for study setup, launch, and diagnostics.
- **Study management** — Optional study backend (Supabase extension) for remote participant management, sessions, and multi-night scheduling.
- **Data storage and transfer** — Structured records of signals, responses, events, and logs; local storage in core, with richer formats and optional remote transfer.
- **Device integration** — Wearable sensors and devices for physiological recording and stimulus delivery.
- **Plugin extensions** — Pluggable modules for device integrations, processing units, and participant activities.

---

## Getting started

1. [Installation](getting-started/installation.md): install SLUMBER and check that it works.
2. [Your first study](getting-started/first-study.md): run an example sleep study from start to finish.
3. [Study setup](user-guide/study-setup.md): create your own study.

---

## Documentation overview

| Section | What you find there |
|---------|---------------------|
| [Getting started](getting-started/installation.md) | Installing SLUMBER and running a first example study |
| [Concepts](concepts/overview.md) | How SLUMBER works: the parts of a study, what happens during a run, and a glossary |
| [User guide](user-guide/index.md) | How to set up, write, validate and run a study, configure the participant UI, and find a run's output |
| [Reference](reference/configuration.md) | Every setting, command and plugin: configuration, CLI, UI and plugins |
| [About](about/roadmap.md) | What SLUMBER can do today, what is planned next, and how to contribute |
