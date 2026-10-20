# UI reference

Lookup tables for the `ui` section of `study.yaml` and the built-in layouts and activities. For how to use them, see [Participant UI](../user-guide/participant-ui.md).

## UI types

Set with `ui.type`. Both use the same RunEngine; they only differ in presentation.

| `type` | Description |
|--------|-------------|
| `gui` | Participant window in the browser (NiceGUI): AppFrame, layouts and activities. Requires the `nicegui` extra. |
| `headless` | No window. Used for testing; see [Headless behaviour](#headless-behaviour). Default for new studies. |

`slumber study run --ui gui|headless` overrides `ui.type` for one run. `--ui headless` ignores all `ui.settings`.

## GUI settings

Under `ui.settings` when `ui.type` is `gui`. All are optional.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `port` | integer | `8080` | Port the GUI runs on. |
| `favicon` | path | SLUMBER favicon | Browser tab icon. |
| `frame` | [Frame settings](#frame-settings) | header and footer shown | Default AppFrame for every phase. |
| `layouts.stepper` | [Stepper settings](#stepper) | see table | Default settings for every `stepper` phase. |

## Frame settings

Under `ui.settings.frame` (study default) or a phase's `frame` (override for that phase). A phase's `frame` is merged on top of the study's.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `header` | `false` or mapping | shown | `false` hides the header. |
| `header.logo` | path | SLUMBER logo | Logo in the header. If the file doesn't exist, a warning is logged and the study's or the SLUMBER logo is shown. |
| `header.title` | string | `study_name` | Title in the header. |
| `header.show_phase_title` | boolean | `false` | Also show the current phase's `title` in the middle of the header. |
| `footer` | boolean | shown | `false` hides the footer. |

## Layouts

Set with a phase's `layout.type`. A phase's `layout.settings` is merged on top of the study's `ui.settings.layouts.<type>`.

| `type` | Description |
|--------|-------------|
| `stepper` | Ordered activities with **Previous**, **Next** and **Complete** buttons, an optional list of steps and a progress bar. |
| `hub` | One activity filling the body, centred, with no navigation. |

For when each layout sends `phase_completed`, see [Run lifecycle](../concepts/run-lifecycle.md#when-a-phase-is-completed).

### Stepper

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `previous_button` | string | `Previous` | Label of the button to the previous step. |
| `next_button` | string | `Next` | Label of the button to the next step. |
| `complete_button` | string | `Complete` | Label of the button on the last step, which completes the phase. |
| `show_activity_list` | boolean | `true` | Show the list of steps next to the activity (above it on narrow windows). |
| `show_progress_bar` | boolean | `true` | Show a progress bar between the **Previous** and **Next** buttons. |
| `show_step_count` | boolean | `true` | Show "Step x of y" above the progress bar. Needs `show_progress_bar`. |
| `show_step_name` | boolean | `false` | Show the current step's title above the progress bar. Needs `show_progress_bar`. |
| `number_steps` | boolean | `false` | Number the steps in the list. |
| `allow_skip` | boolean | `false` | Let the participant open any step from the list and complete the phase without finishing every step. |

Each step is **not started**, **current** or **done** (its activity called `complete()`); the list and the progress bar show these states. A step is **available** when every step before it is done. Unavailable steps are dimmed in the list and can't be opened, and **Complete** is enabled once every step is done. With `allow_skip`, every step is available and **Complete** is always enabled.

Long content scrolls inside the activity card, while the header, buttons and footer stay in place. Below 800 px wide, the list of steps becomes a strip above the activity.

### Hub

No settings.

## Activities

Activities report back with `complete()` and `emit(name)`; see [How activities signal](../concepts/run-lifecycle.md#how-activities-signal).

| Key | Behaviour |
|-----|-----------|
| `instruction` | Renders markdown or text; calls `complete()` on mount. |
| `sleep` | Wake / end buttons → `emit("marked_awake")` / `emit("end_sleep")`. Does not complete. |

### Activity settings

Set under the activity's `settings:`. All are optional.

| Activity | Setting | Default | Description |
|----------|---------|---------|-------------|
| `instruction` | `content` | `""` | Markdown text, or a path to a Markdown file (usually `{assets_dir}/…`). If the value is not an existing file, it is shown as text. Empty content shows "No instruction content." |
| `sleep` | `wake_button` | `I'm Awake` | Label of the button that emits `marked_awake`. |
| `sleep` | `end_button` | `End Session` | Label of the button that emits `end_sleep`. |

For how to use them in a condition, see [Writing conditions](../user-guide/writing-conditions.md#add-activities).

#### How instruction text is shown

The text fills the activity area; long content scrolls inside it.

| Markdown | Shown as |
|----------|----------|
| `# Heading`, `## Heading`, `### Heading` | Headings |
| Paragraphs, `-` and `1.` lists | Body text |
| `[text](https://example.org)` | A link |
| `> a note` | A highlighted callout box |
| `` `code` `` | A small highlighted chip |
| A fenced code block | A highlighted code block that scrolls sideways |
| A table | A highlighted table that scrolls sideways when it is wide |
| `![alt](path)` | An image, scaled down to fit. See below. |

#### Images in instruction texts

| Syntax | Effect |
|--------|--------|
| `![alt](path)` | Shows the image. `path` follows the [path rules](../user-guide/paths-and-placeholders.md): placeholders are expanded and a relative path is relative to the **study root**, not to the Markdown file. Web addresses are used as they are. |
| `![alt](path){width=300 align=center}` | Same, with options, written directly after the image with no space before the braces. |

| Option | Values |
|--------|--------|
| `width` | Pixels (`300` or `300px`) or a percentage of the text width (`50%`). The image is never wider than the text. |
| `align` | `left`, `center` or `right`. Without it, the image is shown where it is written. |

Separate options with spaces or commas. An option that isn't recognised is ignored, with a warning in the run log. If an image file doesn't exist, a warning is logged and the image is left as written.

## Headless behaviour

| Key | Headless |
|-----|----------|
| `instruction` | Completes on mount, as in the GUI. |
| `sleep` | Emits `end_sleep` shortly after mounting. Never emits `marked_awake`. |

For how headless runs a condition overall, see [gui and headless](../concepts/run-lifecycle.md#gui-and-headless).
