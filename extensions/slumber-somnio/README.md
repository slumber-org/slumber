# slumber-somnio

SLUMBER extension for Somnio devices — ZMax headband streaming and eye-movement detection.

## Install

From PyPI (once published):

```bash
uv add slumber-somnio
```

Or for local development from this monorepo folder:

```bash
uv add --editable ./extensions/slumber-somnio
```

## Units

| Entry-point key | Class | Description |
|---|---|---|
| `zmax` | `ZMaxUnit` | Streams raw samples from the ZMax headband over TCP. |
| `eye_movement` | `EyeMovementDetectionUnit` | Detects left/right eye movements from a buffered `TimeSeries`. |
