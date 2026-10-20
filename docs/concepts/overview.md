# Overview

SLUMBER runs sleep studies at home from a folder of YAML files. This page shows how the parts of a study fit together when it runs. For what each term means, see the [Glossary](glossary.md). For how to write the YAML, see the [User guide](../user-guide/index.md), and for every field, the [Configuration reference](../reference/configuration.md).

## How a run fits together

[![Diagram of a SLUMBER run in three rows. Study definition: a study with its conditions. Run execution: the researcher CLI launches a condition on the RunEngine, which presents phases in the participant UI, receives its events, and starts and stops pipelines that exchange data with devices. Run outputs: recordings, run metadata, logs and responses are stored locally.](../assets/diagrams/run-overview.svg)](../assets/diagrams/run-overview.svg)

*Click the diagram to open it full size.*

**Study definition.** A [study](glossary.md#study) is one folder: `study.yaml` with the study-wide settings, one file per [condition](glossary.md#condition) in `conditions/`, and files such as instruction texts in `assets/`. A condition describes the [phases](glossary.md#phase), [layouts](glossary.md#layout), [activities](glossary.md#activity) and [pipelines](glossary.md#pipeline) of one version of the protocol, and [handlers](glossary.md#handler) that connect [events](glossary.md#event) to [actions](glossary.md#action).

**Run execution.** You start a [run](glossary.md#run) of one condition from the command line. The [RunEngine](glossary.md#runengine) loads and checks the study, then starts the [entry phase](glossary.md#entry-phase). Each phase shows its activities to the participant in a layout, in the browser window ([`gui`](glossary.md#ui)) or without a window (`headless`). Activities report events back, and the handlers decide what happens next, such as which phase comes next or when a pipeline starts. Pipelines run in the background, for example to record from a device during sleep.

**Run outputs.** Everything from one run ends up in its own folder: `run.json`, the logs and the recorded data.

Activities, layouts and pipeline [units](glossary.md#unit) are [plugins](glossary.md#plugin): you choose them by name in the YAML, and [extensions](glossary.md#extension) can add more. For the order in which things happen during a run, see [Run lifecycle](run-lifecycle.md).

## Current scope

- Runs are started locally from the command line. No backend or account is needed.
- Runs can use the `gui` or `headless` UI.
- The built-in activities are `instruction` and `sleep`.
- The built-in units `clock` and `jsonl_writer` are for testing; they don't read from devices. Devices come from extensions.
- A study backend and stimulation during sleep are not part of the core.

For a complete example, see `examples/demo/` in the repository.
