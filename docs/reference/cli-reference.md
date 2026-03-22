# CLI reference

All commands are invoked as `slumber <command> [options]`. Use `slumber --help` or `slumber <command> --help` for context-sensitive help.

## Global options

These options are accepted before any subcommand:

| Option | Description |
|--------|-------------|
| `--env`, `-e` PATH | Load a specific environment file (overrides auto-discovered `.env`). |
| `--verbose`, `-v` | Enable verbose (DEBUG) logging. By default only WARNING-level messages are shown. Useful for diagnosing unexpected behaviour. |
| `--help` | Show help and exit. |

Example:

```bash
slumber --verbose study validate --study-dir .
slumber --env .env.dev condition sync --study-dir my-study
```

## slumber doctor

Check the environment, Supabase connectivity, and dependencies. Run this to diagnose setup issues before using other commands.

```bash
slumber doctor
```

Each check displays one of three symbols:

| Symbol | Meaning |
|--------|---------|
| ✓ | OK / set / installed |
| ✗ | Failed / missing (required) |
| — | Not set / not installed (optional) |

**Environment checks** — verifies the following variables:

| Variable | Required | Purpose |
|----------|----------|---------|
| `SUPABASE_URL` | Yes | Required for all Supabase operations. |
| `SUPABASE_ANON_KEY` | Yes | Required for auth and API access. |
| `DATABASE_URL` | Optional | Required for `slumber db upgrade` and other migration commands. |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | Required for admin commands: `participant create`, `session create/update/delete`, `condition sync`. |
| `STUDY_DIR` | Optional | Default study folder path for `study validate` and `condition sync` (replaces `--study-dir`). |
| `STUDY_ID` | Optional | Default study ID for `participant create/list` and `session create/list` (replaces `--study-id`). |
| `USER_ID` | Optional | Default auth user UUID for `participant create/list` (replaces `--user-id`). |
| `PARTICIPANT_ID` | Optional | Default participant ID for `session create/list` (replaces `--participant-id`). |
| `SLUMBER_SESSION_FILE` | Optional | Override the default session file path (`~/.config/slumber/session.json`). |
| `SENTRY_DSN` | Optional | Enables Sentry error monitoring during study runs when set. |

**Supabase connectivity** — attempts a lightweight query against the configured Supabase project. Skipped if `SUPABASE_URL` or `SUPABASE_ANON_KEY` are not set.

**Dependencies** — verifies that declared packages are importable:

| Package | Required | Notes |
|---------|----------|-------|
| `ezmsg` | Yes | Data acquisition backbone. |
| `nicegui` | No | Participant UI. Install with `pip install slumber[nicegui]` or `uv sync --extra nicegui`. |
| `sentry_sdk` | No | Enables Sentry run monitoring. Install with `pip install slumber[sentry]` or `uv sync --extra sentry`. |

**Exit codes:** `0` if all required checks pass; `1` if any required check fails, with a summary count.

## slumber study

### slumber study init

Create a new study folder:

```bash
slumber study init --base-dir . --study-id my-study --name "My Study"
```

| Option | Default | Description |
|--------|---------|-------------|
| `--base-dir`, `-b` | `.` | Parent directory; study folder is created at `<base-dir>/<study-id>/`. |
| `--study-id`, `-s` | `new_study` | Study identifier (also the folder name). |
| `--name`, `-n` | study-id | Human-readable study name (written into `study.yaml`). |
| `--no-env-example` | — | Skip creating `.env` inside the study folder. |
| `--no-gitignore` | — | Skip creating `.gitignore` inside the study folder. |

Creates `<study-id>/` with `study.yaml`, empty `conditions/` and `assets/` directories, an optional `.env` (from the study template), and `.gitignore`. Also registers the study in Supabase (requires `SUPABASE_SERVICE_ROLE_KEY`).

See [Study setup](../user-guide/study-setup.md) for full details.

### slumber study run

Run the scheduled session for the current user:

```bash
slumber study run --study-dir path/to/my-study
```

| Option | Default | Description |
|--------|---------|-------------|
| `--study-dir`, `-d` | — | Path to the study folder. Also read from `STUDY_DIR`. |

Requires `slumber auth login` first. Looks up the authenticated user's participant record in the study, finds the session whose start window contains the current time, creates a Run record in the database, and executes the session's condition via the UI backend. Condition, participant, session, and run ID are all derived from Supabase — no manual flags required. Set `SENTRY_DSN` to enable Sentry monitoring. See [Running a study](../user-guide/study-run.md).

### slumber study validate

Validate study manifest and all condition files:

```bash
slumber study validate --study-dir path/to/my-study
# or via env var:
export STUDY_DIR=path/to/my-study && slumber study validate
```

| Option | Description |
|--------|-------------|
| `--study-dir`, `-d` | Path to the study folder. Also read from `STUDY_DIR`. |

Exits `0` on success (prints study name and condition list); exits `1` with a path-specific error on any validation failure. See [Config loading and validation](../user-guide/config-validation.md).

## slumber condition

### slumber condition sync

Push condition YAML files from the study folder into Supabase:

```bash
# Sync all conditions
slumber condition sync --study-dir path/to/my-study

# Sync specific conditions only
slumber condition sync --study-dir path/to/my-study --conditions condition_1 --conditions condition_2
```

| Option | Description |
|--------|-------------|
| `--study-dir`, `-d` | Path to the study folder. Also read from `STUDY_DIR`. |
| `--conditions`, `-c` | Condition names to sync. Repeat for each name. Omit to sync all. |

Requires `SUPABASE_SERVICE_ROLE_KEY`. See [Condition sync](../user-guide/condition-sync.md).

## slumber auth

| Command | Description |
|---------|-------------|
| `slumber auth login --email E [--password P]` | Sign in; store session for subsequent commands. Prompts for password if omitted. |
| `slumber auth signup --email E --password P` | Register a new user. |
| `slumber auth logout` | Sign out and clear the stored session. |
| `slumber auth password-change [--new-password P]` | Change the current user's password (must be signed in). |
| `slumber auth status` | Show whether you are signed in and with which email. |

Session is persisted to `~/.config/slumber/session.json`. Override with `SLUMBER_SESSION_FILE`.

## slumber participant

Researcher commands — use `SUPABASE_SERVICE_ROLE_KEY`.

| Command | Description |
|---------|-------------|
| `slumber participant create --study-id S --participant-id P --user-id UUID` | Link an existing auth user to a study as a participant. |
| `slumber participant list --user-id UUID` | List participants for the given auth user. |

Options can also be set via `STUDY_ID`, `PARTICIPANT_ID`, `USER_ID` env vars.

## slumber session

Researcher commands — use `SUPABASE_SERVICE_ROLE_KEY`.

| Command | Description |
|---------|-------------|
| `slumber session create --study-id S --participant-id P --earliest-start-at ISO --latest-start-at ISO [--condition-id C]` | Create a session with an allowed start window and optional condition. |
| `slumber session list [--study-id S] [--participant-id P]` | List sessions; filter by study and/or participant. |
| `slumber session update SESSION_ID [--condition-id C] [--earliest-start-at ISO] [--latest-start-at ISO]` | Update a session's condition and/or start window. |
| `slumber session delete SESSION_ID` | Delete a session. |

Datetimes use ISO 8601 format (e.g. `2025-10-01T22:00:00+00:00` or `2025-10-01T22:00:00Z`). Options also readable from `STUDY_ID`, `PARTICIPANT_ID`.

## slumber db

Database migration commands (Alembic / Postgres). Requires `DATABASE_URL`.

| Command | Description |
|---------|-------------|
| `slumber db upgrade [REVISION]` | Apply migrations up to `REVISION` (default: `head`). |
| `slumber db migrate` | Alias for `db upgrade head`. |
| `slumber db downgrade [REVISION]` | Revert to `REVISION` (default: `-1`, one step back). |
| `slumber db current` | Show the current Alembic revision. |
| `slumber db history` | Show migration history. |
| `slumber db revision -m "Description"` | Create a new autogenerated migration file. |

See [Backend](../reference/backend.md) for migration workflow details.
