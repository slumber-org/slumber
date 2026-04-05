# Backend (Supabase / Postgres)

The framework uses **Postgres** for persistence. Supabase provides hosted Postgres plus Auth; you can use Supabase cloud or self-hosted Postgres.

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | Yes (for migrations and DB access) | Postgres connection URI. For Supabase: project dashboard → **Connect** → **URI** (Session pooler or Direct). |
| `SUPABASE_URL` | Yes (for Auth and API) | Supabase project URL, e.g. `https://<project-ref>.supabase.co`. Used by condition sync and participant CLI. |
| `SUPABASE_ANON_KEY` | Yes (for Auth and API) | Supabase anonymous key. |
| `SUPABASE_SERVICE_ROLE_KEY` | No | Service role key for admin operations. Keep secret. |

**Researcher** `.env` — copy from `.env.example` in the project root:

```bash
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # For participant/session CLI (researcher)
```

**Study folder** `.env` — created by `slumber study init` from the study env template in config (`slumber.config.templates`). It contains only `SUPABASE_URL` and `SUPABASE_ANON_KEY` (no `DATABASE_URL` or service role). The study folder `.gitignore` created by init ensures `.env` and `.env.*` are ignored.

**Optional researcher env vars** (used by the CLI via Typer when the corresponding option is not passed): `STUDY_DIR` (study folder path, for validation), `STUDY_ID` (study id), `USER_ID` (auth user UUID for `participant list`), `PARTICIPANT_ID` (participant table id for session commands).

## Database schema

Tables (see `src/slumber/supabase/models.py`):

- **study** — Study manifest registration (`id` string PK, `name`).
- **condition** — Condition config per study (`study_id`, `name`, `procedures` JSONB, `dag` JSONB).
- **participant** — Participant in a study; `auth_user_id` links to Supabase Auth (`auth.users.id`).
- **session** — Scheduled session for a participant (optional condition, date, time window, start/end times).
- **run** — A single run for a session (`status`, `run_directory`, optional `parent_run_id`).

Migrations are in `migrations/versions/` and are applied with Alembic.

## Migration workflow

No study directory is required. From any directory where `.env` (or environment) provides `DATABASE_URL`:

```bash
# Apply all pending migrations
slumber db migrate
# or explicitly
slumber db upgrade head

# Show current revision
slumber db current

# Show history
slumber db history

# Revert one revision
slumber db downgrade -1
```

You can also run Alembic directly:

```bash
cd /path/to/slumber
export PYTHONPATH=src
alembic upgrade head
```

New migrations (after changing `src/slumber/supabase/models.py`):

```bash
alembic revision --autogenerate -m "Description"
# Edit the generated file in migrations/versions/ if needed, then
slumber db upgrade head
```

## Local Postgres (optional)

For local development without Supabase:

1. Run Postgres (e.g. Docker: `docker run -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres`).
2. Create a database and set `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/slumber`.
3. Run `slumber db migrate`.

Supabase Auth is not available locally unless you use Supabase local dev or point to a cloud project.

## Authentication

The framework uses **Supabase Auth** for identity. One auth user can be linked to **many participants** (one participant record per study). Participant rows store `auth_user_id` (Supabase `auth.users.id`); row-level security (RLS) ensures users only see and create their own participants and sessions.

### Researcher vs participant

- **Researchers** use `study`, `db`, `participant`, and `session` commands. These do **not** require running from a study directory (except `study validate`, which requires `--study-dir` or `STUDY_DIR`). Participant and session commands use `SUPABASE_SERVICE_ROLE_KEY` so the researcher can create participants (and optionally create auth users), list participants by user, and manage sessions. Options can be supplied via env vars when not passed: `STUDY_DIR`, `STUDY_ID`, `USER_ID`, `PARTICIPANT_ID`.
- **Participants** use the same Supabase project when running the participant app; they sign in with credentials created for them by the researcher (or sign up if self-registration is enabled). Each participant links one auth user to one study via a participant row (`study_id` + `participant_id`).

### Session persistence (CLI)

After `slumber auth login`, the session is stored in a file so other commands (e.g. `slumber participant create`) run as that user. Default path: `~/.config/slumber/session.json`. Override with `SLUMBER_SESSION_FILE`.

### Auth commands

| Command | Purpose |
|--------|---------|
| `slumber auth login --email <e> --password <p>` | Sign in; store session for other commands. Omit `--password` to be prompted. |
| `slumber auth signup --email <e> --password <p>` | Register a new user. |
| `slumber auth logout` | Sign out and clear the stored session. |
| `slumber auth password-change [--new-password <p>]` | Change the current user's password (must be signed in). |
| `slumber auth status` | Show whether you are signed in and with which email. |

## Condition sync (researcher)

Pushes condition YAML files from the study folder into the Supabase `condition` table. Requires `SUPABASE_SERVICE_ROLE_KEY`. See the [Condition sync guide](../user-guide/condition-sync.md) for full details.

| Command | Purpose |
|--------|---------|
| `slumber condition sync --study-dir <path>` | Upsert all conditions from the study's `conditions/` directory into Supabase. |
| `slumber condition sync --study-dir <path> --conditions <name>` | Upsert only the named condition(s). Repeat `--conditions` for multiple names. |

`--study-dir` may be replaced by the `STUDY_DIR` environment variable.

## Participant and session commands (researcher)

These use `SUPABASE_SERVICE_ROLE_KEY`; no study directory or auth login required. Set options via env when not passed: `STUDY_DIR`, `STUDY_ID`, `USER_ID`, `PARTICIPANT_ID`.

### Participant

| Command | Purpose |
|--------|---------|
| `slumber participant create --study-id <id> --participant-id <id> --user-id <uuid>` | Create a participant by linking an existing auth user (`--user-id`) to a study and participant id. Uses `SUPABASE_SERVICE_ROLE_KEY`. |
| `slumber participant list --user-id <uuid>` | List participants for the given auth user (or set `USER_ID`). Uses `SUPABASE_SERVICE_ROLE_KEY`. |

### Session

| Command | Purpose |
|--------|---------|
| `slumber session create --study-id <id> --participant-id <id> --earliest-start-at ISO_DATETIME --latest-start-at ISO_DATETIME [--condition-id <id>]` | Create a session for a participant with a start window (`earliest-start-at`, `latest-start-at`) and optional condition id. Uses `SUPABASE_SERVICE_ROLE_KEY`. |
| `slumber session list [--study-id <id>] [--participant-id <id>]` | List sessions; optionally filter by study and/or participant (`STUDY_ID`, `PARTICIPANT_ID`). |
| `slumber session update <session_id> [--condition-id <id>] [--earliest-start-at ISO_DATETIME] [--latest-start-at ISO_DATETIME]` | Update a session’s condition and/or start window. |
| `slumber session delete <session_id>` | Delete a session. |

### Linking user and participant

- **Researcher creates participant**: Run `slumber participant create --study-id X --participant-id sub-001 --email p@example.com --password secret` to create a new auth user and a participant row linking that user to study X. Or pass `--user-id <uuid>` to link an existing auth user.
- **List participants for a user**: `slumber participant list --user-id <auth-user-uuid>` (or set `USER_ID`).
- **Sessions**: Sessions belong to a participant. Use `participant list` to get participant table `id` values, then pass that `id` as `--participant-id` to `slumber session create`.
