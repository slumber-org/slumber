# Roadmap

## Current status

SLUMBER is in public **alpha**. Local study workflows (`study init` / `validate` / `run`), `doctor`, built-in `instruction` and `sleep` activities, `clock` and `jsonl_writer` units, gui/headless UI, and the demo study are available today. APIs and configuration may still change.

Early specialised builds are already used in running studies. This repository is the general framework toward a public release.

## Next

Focus for the next public version — study-usable capabilities beyond the demo core:

- **Device integration** — ZMax and CGX support, connection-test activity, LSL
- **Data storage** — beyond demo JSONL (e.g. HDF5 / richer records)
- **SurveyJS** — survey activity
- **Sleep scoring**

## Toward release

- **Packaging** — publishable package
- **Documentation** — complete for release
- **Publication**

## Later

Stimulation and cueing (auditory / visual / tactile), event and audit logging, optional multi-participant backend (scheduling, auth, condition sync), and additional devices (e.g. Polar).