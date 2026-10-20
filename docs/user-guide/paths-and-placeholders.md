# Paths and placeholders

Study YAML files often point to other files: the instruction text an activity shows, a logo, the file a pipeline writes to, or a log file. This page shows how to write those paths so that they point to the right file: in your study, in the run folder, or anywhere else.

## The rule

1. **Placeholders expand first.** Names in curly braces, such as `{assets_dir}`, are replaced with their values.
2. **Relative paths resolve against the study root**, the folder that contains `study.yaml`.
3. **Absolute paths are used as they are.**

There are no hidden base folders. A relative path never means "inside `assets/`" or "inside the run folder" on its own. To point there, use a placeholder.

## Placeholders

| Placeholder | Expands to |
|-------------|------------|
| `{assets_dir}` | The study's assets folder (absolute path) |
| `{run_dir}` | This run's folder (absolute path) |
| `{run_id}` | The run id |
| `{study_id}` | The study id from `study.yaml` |
| `{study_name}` | The study's display name |
| `{condition_id}` | The name of the condition being run |
| `{participant_id}` | The `PARTICIPANT_ID` environment variable, when it is set |
| `{session_id}` | The session id, when one is set (local runs don't set one) |

In `runs.layout`, only `{study_id}`, `{run_id}`, `{condition_id}`, `{participant_id}` and `{session_id}` can be used.

!!! note "Placeholders during validation"
    Only `{assets_dir}`, `{study_id}` and `{study_name}` are known before a run starts. When `slumber study validate` checks a study, it leaves the other placeholders as written, so it can't check paths that use them, such as `{run_dir}/clock.jsonl`.

## Examples

```yaml
# Placeholder → <study>/assets/intro.md
settings: { content: "{assets_dir}/intro.md" }

# Placeholder → <run_dir>/clock.jsonl
settings: { path: "{run_dir}/clock.jsonl" }

# Relative, no placeholder → <study>/assets/intro.md
settings: { content: assets/intro.md }

# Absolute → unchanged
settings: { path: /tmp/clock.jsonl }
```

Placeholders also work in text that is not a path, such as a title:

```yaml
frame:
  header:
    title: "{study_name}"
```

## Which values are treated as paths

In plugin `settings` (UI, layouts, activities and units), every string has its placeholders expanded. After that, a string is treated as a path only if it contains a `/` (or `\`). Other strings, such as button labels and titles, are left as text.

This means a bare file name is **not** resolved against the study root: `content: intro.md` is passed on as just `intro.md`. Write `{assets_dir}/intro.md` or `assets/intro.md` instead.

Log sinks in `study.logging` are always treated as paths, so `sink: "{run_id}.log"` writes to `<study>/<run_id>.log`. Use `{run_dir}/{run_id}.log` to write into the run folder. See [Run output and logging](run-output-and-logging.md).

The run folder itself follows its own rule: `runs.layout` is joined under `runs.directory`, so the default `run-{run_id}` gives `<study>/runs/run-<run_id>/`.

## Plugins receive resolved paths

Plugins never join paths against the assets folder or the run folder themselves. By the time an activity or unit receives its settings, every placeholder has been expanded and every relative path has been resolved. An activity that gets `content: "{assets_dir}/intro.md"` sees the full absolute path to `intro.md`.