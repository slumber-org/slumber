# Backend features (extension)

Multi-participant backend features — auth, condition sync to a remote database, session scheduling, and participant management — are **not part of core 0.1**. Local study authoring and `slumber study run` work from files only.

Those capabilities are intended for an optional package (e.g. `slumber-supabase`) that attaches Typer apps via the `slumber.cli` entry-point group. Until that extension is installed and documented, use:

- `slumber study init` / `validate` / `run --condition`
- `slumber doctor` for local environment checks

See [Running a study](study-run.md) and the [CLI reference](../reference/cli-reference.md).
