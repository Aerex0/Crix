# Task: Integrate livekit-wakeword into Voice Assistant

## Goal
Add always-on wake word detection to the voice assistant pipeline using `livekit-wakeword`. The wake word is **"hey crix"**.

## Steps

### Step 1 — Train and export the wake word model

Install livekit-wakeword:
```bash
uv add git+https://github.com/livekit/livekit-wakeword.git
```

Install system dependencies:
```bash
sudo apt install espeak-ng libsndfile1 ffmpeg sox portaudio19-dev
```

Download base models:
```bash
uv run livekit-wakeword setup
```

Create `configs/hey_crix.yaml`:
```yaml
model_name: hey_crix
target_phrases:
  - "hey crix"

n_samples: 10000
model:
  model_type: conv_attention
  model_size: small
steps: 50000
target_fp_per_hour: 0.2
```

Train and export:
```bash
uv run livekit-wakeword run configs/hey_crix.yaml
```

This produces `hey_crix.onnx`. Place it in `models/hey_crix.onnx`.

---

### Step 2 — Implement `wake_word/detector.py`

Create a `WakeWordDetector` class that:
- Loads `WakeWordModel` with `hey_crix.onnx` once at init (not per-call)
- Exposes an async method `wait_for_wake_word()` that blocks until detection fires
- Uses `WakeWordListener` as an async context manager internally
- Accepts a configurable `threshold` (default `0.5`) and `debounce` (default `2.0` seconds)

```python
from livekit.wakeword import WakeWordModel, WakeWordListener

class WakeWordDetector:
    def __init__(self, model_path: str, threshold: float = 0.5, debounce: float = 2.0):
        ...

    async def wait_for_wake_word(self) -> str:
        # returns the name of the detected wake word
        ...
```

---

### Step 3 — Wire into `pipeline/controller.py`

The pipeline state machine should:

1. Start in `IDLE` state
2. Call `detector.wait_for_wake_word()` — this blocks until wake word fires
3. On detection → transition to `LISTENING` state, start VAD + audio recording
4. Rest of pipeline continues as normal (STT → LLM → TTS)
5. After TTS finishes → return to `IDLE`, call `wait_for_wake_word()` again

```
IDLE
  └── await wait_for_wake_word()
        └── LISTENING → TRANSCRIBING → THINKING → SPEAKING
              └── (done) → IDLE
```

The wake word detector must keep listening during SPEAKING state too — if wake word fires mid-response, interrupt TTS and go back to LISTENING.

---

### Step 4 — Config

Add to `.env`:
```env
WAKE_WORD_MODEL_PATH=models/hey_crix.onnx
WAKE_WORD_THRESHOLD=0.5
WAKE_WORD_DEBOUNCE=2.0
```

Load in `config.py` alongside existing env vars.

---

## Notes
- `WakeWordListener` opens the mic stream internally via portaudio — do NOT open a separate sounddevice stream simultaneously or there will be a conflict. Close the wake word listener before opening the recording stream, then reopen it after TTS finishes.
- Model loads once at startup, not per detection cycle.
- `livekit-wakeword` is backward compatible with `openWakeWord` — `.onnx` models are interchangeable if needed.
- Training is a one-time step. Once `hey_crix.onnx` exists, skip Step 1.