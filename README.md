# SLUMBER - Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings

SLUMBER is an open-source, Python-based framework for conducting **home-based sleep studies** with a focus on:

- **Researcher-friendly configuration** (YAML/JSON-first)
- **Extensibility** via a small stable core + optional extensions (devices, processing, UI)
- **Reproducibility** through run logging and well-defined study artifacts

## Documentation

- **Docs site**: see `docs/` (served via MkDocs)
- **Design (0.1)**: `docs/design/0.1-base.md`
- **Legacy reference**: `docs/about/legacy-reference.md`

Serve docs locally:

```bash
uv sync
uv run mkdocs serve
```

## Legacy project (reference only)

The original study-specific implementation lives in the legacy repository and is used as a migration/reference target while the framework is built here:

- Legacy repo: `https://github.com/alitsaberi/slumber`

