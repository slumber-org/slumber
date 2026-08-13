# NiceGUI Participant UI

The NiceGUI UI backend provides a web-based participant application with login, procedure execution, sleep monitoring, and session completion.

## Setup

Install the NiceGUI optional dependency:

```bash
uv sync --extra nicegui
```

Set the UI backend in your `study.yaml`:

```yaml
ui:
  backend: nicegui
  config:
    port: 8080      # web server port (default: 8080)
    dark: true       # dark mode (optional)
    show: true       # auto-open browser (default: true)
```

## App Flow

The participant app follows an event-driven flow:

```
Login → Welcome → [Sleep Page ↔ Procedures] → Completion
```

1. **Login** — Shown if no valid Supabase session exists. Email/password authentication.
2. **Welcome** — Study name, participant info, and "Start Session" button.
3. **Sleep Page** — The idle hub. Fires events that trigger procedures.
4. **Procedure Runner** — Executes triggered procedures with step sidebar and navigation.
5. **Completion** — Session finished. Shuts down the app.

## Event-Driven Procedures

Procedures are triggered by **session events**, not run sequentially. Each procedure declares a `trigger` event and an optional `when` guard.

### Session Events

| Event | Fired by |
|-------|----------|
| `session_start` | Welcome page "Start Session" button |
| `sleep_start` | Sleep page "Going to Sleep" button |
| `wake_up` | Sleep page "I'm Awake" button |
| `session_end` | Sleep page "End Session" button |

### Example Condition

```yaml
name: lucid_dreaming
procedures:
  pre_sleep:
    trigger: session_start
    steps:
      - task: instruction
        settings: {text: "Welcome to the study. Prepare for sleep."}

  first_awakening:
    trigger: wake_up
    when:
      awakening_count: 1
    steps:
      - task: instruction
        settings: {text: "First awakening. Please answer some questions."}

  later_awakening:
    trigger: wake_up
    when:
      awakening_count: {gt: 1}
    steps:
      - task: instruction
        settings: {text: "You woke up again. Quick check-in."}

  post_sleep:
    trigger: session_end
    steps:
      - task: instruction
        settings: {text: "Good morning! Session complete."}

dag:
  components:
    - name: MASTER
      unit_type: Master
  connections: []
  process_components: []
```

### Guards (`when` conditions)

Guards determine whether a procedure runs when its trigger fires. Two forms:

**Declarative (YAML dict)** — simple state checks:

```yaml
# exact match
when:
  awakening_count: 1

# comparison operators: gt, gte, lt, lte
when:
  awakening_count: {gt: 1}

# multiple keys use AND logic — all must match
when:
  awakening_count: {gte: 2}
  sleep_count: 1
```

**Code-driven (Python callable)** — for complex or data-driven logic:

```yaml
when: "my_study.guards:is_rem_awakening"
```

The callable receives a `SessionState` object and returns `bool`:

```python
from slumber.runtime.events import SessionState


def is_rem_awakening(state: SessionState) -> bool:
    return state.get("last_arousal_type") == "rem"
```

### Conflict Resolution

When multiple procedures share the same trigger, **all matching** procedures run in the order they appear in the YAML. Make guards mutually exclusive if only one should run.

### Post-Procedure Flow

After triggered procedures complete:

- **`session_end`** → Completion page
- **All other events** → Back to Sleep page

## Procedure Runner

The procedure runner displays:

- **Content area**: renders the current step (placeholder in Stage 2)
- **Task sidebar**: step list with completion status (controlled by `show_task_list`)
- **Navigation**: Previous / Next / Complete buttons

### Procedure Options

```yaml
procedures:
  my_procedure:
    trigger: session_start
    show_task_list: true   # show step sidebar (default: true)
    allow_skip: false      # allow skipping steps (default: false)
    steps: [...]
```

## Sleep Page

The sleep page is the app's idle state between procedures. It provides:

- **"Going to Sleep"** button (with confirmation) → fires `sleep_start`
- **"I'm Awake"** button (with confirmation) → fires `wake_up`
- **"End Session"** button (disabled while asleep, with confirmation) → fires `session_end`
