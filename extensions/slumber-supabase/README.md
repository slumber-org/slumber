# slumber-supabase

SLUMBER extension for Supabase Auth, study backend helpers, and Alembic migrations.

Attaches CLI groups (`auth`, `db`, `participant`, `session`, `condition`) via the
`slumber.cli` entry-point group. Local `slumber study run` does not require this
package.

## Install

From the monorepo (recommended while developing):

```bash
uv sync --extra supabase --dev
```

Or add the package directly:

```bash
uv add --editable ./extensions/slumber-supabase
```

Once published:

```bash
pip install slumber-supabase
# or
pip install 'slumber[supabase]'
```

## CLI

With the extension installed, the root `slumber` CLI gains:

| Group | Purpose |
| --- | --- |
| `auth` | Sign in / sign up / sign out / password change |
| `db` | Alembic migrations against Postgres / Supabase |
| `participant` | Create and list participants |
| `session` | Create, list, update, and delete sessions |
| `condition` | Sync local condition files to the backend |

## Environment

| Variable | Role |
| --- | --- |
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | Anon key for Auth / REST |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional; admin operations |
| `DATABASE_URL` | Postgres URI for Alembic |
| `SLUMBER_SESSION_FILE` | Optional override for persisted Auth session |

## Migrations

Run from anywhere once the package is installed; `slumber db …` uses this
package’s `alembic.ini` and `migrations/` tree.
