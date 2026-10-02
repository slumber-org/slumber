# Backend (Supabase / Postgres)

Core SLUMBER 0.1 does **not** require Supabase or Postgres. Study packages and `slumber study run` are local (YAML on disk + run directories).

Multi-participant features (Auth, condition sync, session scheduling, migrations) belong in an optional extension that registers CLI groups via `slumber.cli`. Documentation for that package will live with the extension once published.

For local work:

1. Install SLUMBER ([Installation](../getting-started/installation-setup.md))
2. Create and validate a study ([Study setup](../user-guide/study-setup.md))
3. Run a condition ([Running a study](../user-guide/study-run.md))

`slumber doctor` checks local env vars (`STUDY_DIR`, `PARTICIPANT_ID`) and dependencies (`ezmsg`, optional `nicegui`) only.
