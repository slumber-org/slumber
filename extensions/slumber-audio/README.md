# slumber-audio

SLUMBER extension for audio file playback.

Provides a cross-platform `AudioPlayer` (wrapping `sounddevice` + `soundfile`) and an ezmsg `AudioPlayerUnit` that plays audio on demand and supports mid-playback cancellation.

## Install

From PyPI (once published):

```bash
uv add slumber-audio
```

Or for local development from this monorepo folder:

```bash
uv add --editable ./extensions/slumber-audio
```

## Usage

### Standalone player

```python
from pathlib import Path
from slumber_audio import AudioPlayer

player = AudioPlayer()  # optional: device=0 to select output device
player.play(Path("tone.wav"))  # blocks until done
player.stop()  # cancel from another thread
```

### Pipeline unit

Register `AudioPlayerUnit` in a condition pipeline and wire it to a trigger source:

```yaml
# conditions/demo.yaml (excerpt)
pipelines:
  - id: cueing
    units:
      - id: audio
        type: audio_player
        settings:
          file_path: "{assets_dir}/cue.wav"
          volume: 0.8
    connections:
      - [trigger.OUTPUT_CUE, audio.INPUT_PLAY]
      - [audio.OUTPUT_DONE, logger.INPUT_EVENT]
```

#### Streams

| Stream | Type | Description |
|---|---|---|
| `INPUT_PLAY` | `AudioPlayRequest` | Triggers playback. `file_path` and `volume` fields override unit settings when set. |
| `INPUT_STOP` | `bool` | Send `True` to cancel in-progress playback immediately. |
| `OUTPUT_DONE` | `bool` | Emits `True` after each playback ends (complete or stopped). |

#### `AudioPlayRequest`

```python
from pathlib import Path

from slumber_audio import AudioPlayRequest

# Use unit defaults
request = AudioPlayRequest()

# Override file and volume for this play only
request = AudioPlayRequest(file_path=Path("alert.wav"), volume=0.5)
```

#### Settings

| Field | Type | Default | Description |
|---|---|---|---|
| `file_path` | `Path \| None` | `None` | Default audio file. Must be set here or per-request. |
| `volume` | `float` | `1.0` | Amplitude scale (0.0–1.0). |
| `device` | `int \| str \| None` | `None` | sounddevice output device. `None` = system default. |
