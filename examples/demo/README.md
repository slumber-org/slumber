# Demo study

Minimal 0.1 study package: setup instruction → clock pipeline → sleep → morning → end.

```bash
# GUI (default in study.yaml; requires slumber[nicegui])
uv run slumber study run --study-dir examples/demo --condition demo

# Headless (CI / no browser)
uv run slumber study run --study-dir examples/demo --condition demo --ui headless
```
