# Backend (Supabase / Postgres)

The framework uses **Postgres** for persistence. Supabase provides hosted Postgres plus Auth; you can use Supabase cloud or self-hosted Postgres.

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | Yes (for migrations and DB access) | Postgres connection URI. For Supabase: project dashboard → **Connect** → **URI** (Session pooler or Direct). |
| `SUPABASE_URL` | Yes (for Auth and API) | Supabase project URL, e.g. `https://<project-ref>.supabase.co`. Used by condition sync and participant CLI. |
| `SUPABASE_ANON_KEY` | Yes (for Auth and API) | Supabase anonymous key. |
| `SUPABASE_SERVICE_ROLE_KEY` | No | Service role key for admin operations. Keep secret. |

Example `.env` (copy from `config/templates/env.example`):

```bash
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=eyJ...
```

Do not commit `.env`; add it to `.gitignore`.

## Database schema

Tables (see `src/slumber/db/models.py`):

- **study** — Study manifest registration (`id` string PK, `name`).
- **condition** — Condition config per study (`study_id`, `name`, `procedures` JSONB, `dag` JSONB).
- **participant** — Participant in a study; `auth_user_id` links to Supabase Auth (`auth.users.id`).
- **session** — Scheduled session for a participant (optional condition, date, time window, start/end times).
- **run** — A single run for a session (`status`, `run_directory`, optional `parent_run_id`).

Migrations are in `migrations/versions/` and are applied with Alembic.

## Migration workflow

From the project root (with `DATABASE_URL` set):

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

New migrations (after changing `src/slumber/db/models.py`):

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
