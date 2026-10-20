# Contributing to SLUMBER

Thanks for helping improve SLUMBER. Contributions are welcome, including:

- Code changes via pull requests
- Documentation improvements
- Bug reports and feature requests

## Setup

### Prerequisites

- **Python**: SLUMBER supports Python **3.10–3.13**; for local development we recommend **Python 3.12+** (see `.python-version`).
- **uv**: Install the [uv](https://docs.astral.sh/uv/) package manager.

### Installation

1\. Clone the repository

```bash
git clone https://github.com/slumber-org/slumber.git
cd slumber
```

2\. Install dependencies

```bash
uv sync --all-extras --dev
```

3\. Set up pre-commit hooks

```bash
uv run pre-commit install
```

## GitHub Flow

This project follows [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow) for branching and releases.

### Branches

- **`main`**: the only long-lived branch; always the integration target. Releases are tags on `main` (e.g. `v0.1.0`).
- **`feature/<name>`**: new features branched from `main`.
- **`fix/<name>`**: bug fixes branched from `main`.
- **`docs/<name>`**: documentation-only changes branched from `main`.
- **`chore/<name>`**: maintenance and tooling changes branched from `main`.

### Development workflow

1. Update your local `main` from the remote `main`.
2. Create a `feature/`, `fix/`, `docs/`, or `chore/` branch from `main`.
3. Make your changes and commit them on your branch.
4. Open a PR from your branch into `main`.

#### Tips and Conventions

- Commit messages should start with a **capitalized action verb** (imperative) and be descriptive, e.g. `Add logging for debug output`, `Fix crash on empty config`, `Update contributing guide`.
- Rebase your branch on the latest `main` to minimize merge conflicts.
- Make PR titles/descriptions clear and request review from the appropriate reviewer(s).
- Address review feedback with follow-up commits (e.g. `Address review feedback (round 2)`) and push updates to the same branch.
- Keep PRs focused; avoid bundling unrelated changes.
- Prefer a PR small enough that **one commit** tells the whole story. If you need multiple commits before review, keep them **independent**: each is a self-contained logical unit that does not fix or rewrite an earlier commit on the same branch (no pre-review "fix previous commit" stacks). Review follow-up commits are fine.

## Linting and Formatting

SLUMBER uses [Ruff](https://docs.astral.sh/ruff/) for both linting and code formatting. If you've set up pre-commit hooks, linting and formatting will run automatically before each commit.

### Run the linter

```bash
uv run ruff check .
```

Fix issues automatically when possible:

```bash
uv run ruff check --fix .
```

### Format code

```bash
uv run ruff format .
```

### Pre-commit (manual run)

You can also run all pre-commit checks manually:

```bash
uv run pre-commit run --all-files
```

## Testing

SLUMBER uses [pytest](https://docs.pytest.org/) for tests.

### Run tests

```bash
uv run pytest
```

### Test conventions

- **Location**: Mirror the package layout with one subfolder per package: `tests/cli/` → `slumber.cli`, `tests/config/` → `slumber.config`, `tests/schemas/` → `slumber.schemas`, and so on (e.g., `src/slumber/config/paths.py` → `tests/config/test_paths.py`). Use top-level `tests/` only for cross-cutting smoke or integration tests (e.g., `tests/test_smoke.py`).
- **Naming**: Use `test_*.py` files and `test_*` functions. Name tests by behavior (`test_parses_empty_file`) rather than implementation.
- **Structure**: Use **Arrange–Act–Assert** and keep each test focused on one behavior.
- **Fixtures**: Prefer `pytest` fixtures for setup/teardown (and reuse). Avoid shared global state between tests.
- **Isolation**: Tests should be deterministic and run in any order. Avoid network calls and reliance on the local machine/user environment.
- **I/O**: Use `tmp_path` for filesystem work; don’t write into the repo tree.
- **Assertions**: Prefer simple `assert` statements; use `pytest.raises(...)` for error cases.
- **Speed**: Keep unit tests fast; if you add slow/integration tests, document how to run them and register any custom markers in `pyproject.toml`.

## Documentation

This repo uses [MkDocs](https://www.mkdocs.org/) for documentation.

Serve docs locally:

```bash
uv run mkdocs serve
```

### Main documentation sections

The documentation is organized into the following high-level sections:

- **Home**  
  High-level introduction to SLUMBER and its purpose.

- **Getting Started**  
  Minimal steps required to install dependencies and run the project for the first time.

- **User Guide**  
  Study packages, validation, local run, and participant UI.

- **Reference**  
  Schemas, plugins, UI, and CLI for the 0.1 surface.

- **About**  
  Contributing guidelines.


### Docstrings

All public modules, functions, classes, and methods should include docstrings. SLUMBER follows the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstring formatting.

Where appropriate, API and reference documentation should be generated automatically using **MkDocstrings**. Auto-generated reference documentation is intended to complement narrative documentation, not replace it.

### Writing conventions

- Use **kebab-case** for file names (e.g., `running-a-study.md`)
- Place files in the appropriate subfolder under `docs/`
- Use a single top-level heading (`#`) per page
- Use `##`, `###`, etc. for subsections
- Use **relative links** when linking between documentation pages
- Keep paths stable to avoid broken links
- Use fenced code blocks with a language identifier where possible:

```python
def example_function():
    pass
```

- Keep pages focused and concise
- Prefer multiple small pages over one very long page
- Write in clear, direct language

## TODOs and issue tracking

SLUMBER uses a lightweight convention for TODOs so that follow-up work (docs, tests, refactors, etc.) stays visible and actionable.

- **Source of truth**: Anything non-trivial should be tracked as a **GitHub issue** (use the issue templates when possible).
- **In-code TODOs**: Allowed. Prefer linking to an issue/ticket for anything that won't be handled immediately.
- **Author is optional**: You may write `TODO:` or `TODO(name):`.

### TODO format (Python)

Prefer one of these forms:

```python
# TODO: [tests] Add regression test for empty config.

# TODO(ali): [docs] Explain config precedence.
```

Notes:

- Use a short tag like `[docs]`, `[tests]`, `[refactor]`, `[logging]`, `[config]` at the start of the description.
- If applicable, add an issue reference on the next line (URL) or a ticket id like `ABC-123`.

### TODO format (Markdown)

Use HTML comments so TODOs don't render in the docs:

```md
<!-- TODO: [docs] Add example CLI usage. -->
```

### Suggested labels

If you maintain labels in the GitHub repo, these tend to work well:

- **Area**: `docs`, `tests`, `cli`, `logging`, `config`
- **Type**: `bug`, `tech-debt`
- **Priority**: `priority:high`, `priority:medium`, `priority:low`
