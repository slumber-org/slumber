# Installation and Setup

This guide walks you through installing SLUMBER and connecting it to a Supabase backend so you can start running studies.

## System requirements

- **Python 3.10+** (3.12+ recommended for development)
- **[uv](https://docs.astral.sh/uv/)** — recommended package manager; used in all examples below

## Installing SLUMBER

### From source (recommended for development)

```bash
git clone https://github.com/slumber-org/slumber.git
cd slumber
uv sync
```

This installs all runtime dependencies into a virtual environment managed by uv. To include the optional Sentry integration:

```bash
uv sync --extra sentry
```

### From PyPI

```bash
pip install slumber
# or with uv:
uv pip install slumber
```

## Supabase setup

SLUMBER uses [Supabase](https://supabase.com) for authentication and data storage. You need a Supabase project (cloud or self-hosted) before running any commands that touch the backend.

1. Create a project at [supabase.com](https://supabase.com) (free tier is sufficient for development).
2. From the project dashboard, collect:
   - **Project URL** — `Settings → API → Project URL`
   - **Anon key** — `Settings → API → Project API keys → anon public`
   - **Service role key** — `Settings → API → Project API keys → service_role` (keep this secret)
   - **Database URI** — `Settings → Database → Connection string → URI` (for migrations)

## Environment setup

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Required for migrations
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres

# Required for all Supabase operations
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=eyJ...

# Required for admin commands (participant/session CLI, condition sync)
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Optional: Sentry error monitoring during study runs
# SENTRY_DSN=https://key@o0.ingest.sentry.io/0
```

## Apply database migrations

Once `DATABASE_URL` is set, apply the schema migrations:

```bash
uv run slumber db migrate
```

This creates all required tables (`study`, `condition`, `participant`, `session`, `run`) in your Supabase Postgres database and enables row-level security policies.

## Verify the installation

Run the doctor command to check that everything is configured correctly:

```bash
uv run slumber doctor
```

Expected output when fully configured:

```
Environment
  ✓ SUPABASE_URL           set
  ✓ SUPABASE_ANON_KEY      set
  ✓ DATABASE_URL           set
  ✓ SUPABASE_SERVICE_ROLE_KEY  set
  ...

Supabase
  ✓ connectivity           ok

Dependencies
  ✓ ezmsg                  installed

✓ No issues found.
```

A `✗` next to a required variable means that command will not work until the variable is set. A `—` next to an optional variable is fine unless you need that feature.

## Quick start

Once the installation is verified:

1. Sign in as a researcher:
   ```bash
   uv run slumber auth login --email you@example.com
   ```

2. Create your first study folder:
   ```bash
   uv run slumber study init --base-dir . --study-id my-study --name "My Study"
   ```

3. Validate the study:
   ```bash
   uv run slumber study validate --study-dir my-study
   ```

From here, see [Study Setup](../user-guide/study-setup.md) to add conditions, and [Running a Study](../user-guide/study-run.md) for the full researcher workflow including participant and session management.
