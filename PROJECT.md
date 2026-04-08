# Crix — Project Documentation

> Full architecture and technical details for developers and contributors.

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Pipeline Flow](#pipeline-flow)
5. [Wake Word Detection](#wake-word-detection)
6. [Memory System](#memory-system)
7. [Tool System](#tool-system)
8. [Browser Automation](#browser-automation)
9. [Configuration](#configuration)
10. [Development](#development)

---

## Overview

Crix is a voice-controlled AI assistant for Linux desktop that provides hands-free control over:
- Keyboard and mouse input
- Window and workspace management
- Web browsers via automation
- Clipboard and screenshots
- Shell commands
- Persistent memory across sessions

### Key Design Principles

1. **Always-on wake word** — Say "hey livekit" (configurable) to activate
2. **Native Linux integration** — Uses GNOME APIs and Wayland-native tools
3. **Memory-first** — Remembers preferences and context across sessions
4. **Browser-first automation** — Uses real Chrome profile for web tasks
5. **Privacy-conscious** — Local memory files, optional local LLM

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│   │  LiveKit CLI    │    │ LiveKit Client  │    │  Wake Word      │     │
│   │  (console)      │    │  (any app)      │    │  (always-on)    │     │
│   └────────┬────────┘    └────────┬────────┘    └────────┬────────┘     │
│            │                      │                      │              │
│            └──────────────────────┼──────────────────────┘              │
│                                   │                                     │
│                    LiveKit WebSocket (wss://...)                        │
│                                   │                                     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────────┐
│                           AGENT SERVER                                  │
│                                   │                                     │
│  ┌────────────────────────────────▼──────────────────────────────────┐  │
│  │                    PipelineController                             │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐   │  │
│  │  │   IDLE      │───▶│  LISTENING  │───▶│   PROCESSING         │   │  │
│  │  │ (wake word) │    │  (VAD +     │    │   (STT→LLM→TTS)      │   │  │
│  │  │  listening) │    │   mic on)   │    │                      │   │  │
│  │  └─────────────┘    └─────────────┘    └──────────────────────┘   │  │
│  │                                                    │              │  │
│  │                                                    ▼              │  │
│  │                                      ┌─────────────┐              │  │
│  │                                      │  SPEAKING   │──┐           │  │
│  │                                      │  (TTS out)  │  │           │  │
│  │                                      └─────────────┘  │           │  │
│  │                                                       │           │  │
│  └───────────────────────────────────────────────────────┼───────────┘  │
│                                                          │              │
└──────────────────────────────────────────────────────────┼──────────────┘
                                                           │
                    ┌──────────────────────────────────────▼────────────┐
                    │                   TOOLS                           │
                    │  ┌──────────┐ ┌──────────┐ ┌─────────────────┐    │
                    │  │  ydotool │ │  gdbus   │ │  browser-use    │    │
                    │  │ (input)  │ │ (GNOME)  │ │  (web)          │    │
                    │  └──────────┘ └──────────┘ └─────────────────┘    │
                    │  ┌──────────┐ ┌──────────  ┐ ┌─────────────────┐  │
                    │  │ wl-      │ │  grim      │ │  memory         │  │
                    │  │ clipboard│ │(screenshot)│ (persistent)      │  │
                    │  └──────────┘ └──────────  ┘ └─────────────────┘  │
                    └───────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Agent Server (`src/agent.py`)

The main entry point that:
- Loads configuration from environment
- Initializes the LiveKit AgentServer
- Registers all tools with the agent
- Handles job lifecycle (start/shutdown)

```python
# Simplified flow
server = AgentServer()

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    controller = PipelineController(ctx)
    await controller.run()
```

### 2. Pipeline Controller (`src/wakeword/pipeline.py`)

Controls the voice assistant state machine:

| State | Description |
|-------|-------------|
| `IDLE` | Waiting for wake word (if enabled) |
| `LISTENING` | Voice activity detection + microphone active |
| `PROCESSING` | Transcribing, thinking, generating response |
| `SPEAKING` | Playing TTS audio back to user |

Key methods:
- `run()` - Main loop
- `_run_with_wakeword()` - Uses wake word detection
- `_run_direct()` - Direct mode (no wake word)
- `_start_agent_session()` - Creates and runs a LiveKit session

### 3. Wake Word Detector (`src/wakeword/detector.py`)

Async wake word detection using `livekit-wakeword`:

```python
class WakeWordDetector:
    def __init__(
        self,
        model_path: str,      # Path to .onnx model
        threshold: float = 0.5,
        debounce: float = 2.0,
    ):
        self._model = None
        self._listener = None

    async def wait_for_wake_word(self) -> WakeWordDetection:
        """Blocks until wake word detected"""
        # Uses WakeWordListener internally
```

**How it works:**
1. Loads ONNX model at init (once)
2. Opens microphone via PortAudio
3. Continuously processes audio frames through the model
4. When confidence > threshold → returns detection
5. Debounce prevents repeated triggers

### 4. Tools (`src/tools.py`)

All voice-controllable functions the AI can call. Each tool is decorated with `@function_tool`.

Tool categories:
- **Keyboard**: type_text, press_key, type_and_submit, paste_text
- **Mouse**: move_mouse, click, double_click, scroll
- **Window**: switch_workspace, focus_window, list_open_windows, open_app
- **Clipboard**: get_clipboard, select_all_and_copy
- **Screen**: get_screen_size, read_screen_text
- **Web**: web_search, browse_web
- **Memory**: save_memory, memory_search, memory_get
- **System**: run_command_silent, get_time

### 5. Backends (`src/backends/`)

Each backend wraps a system tool:

| Backend | Tool | Description |
|---------|------|-------------|
| `ydotool.py` | Input simulation | Types, clicks, scrolls via ydotool daemon |
| `gnome.py` | GNOME APIs | Workspace switch, window focus via gdbus |
| `clipboard.py` | wl-clipboard | Copy/paste via Wayland clipboard |
| `screenshot.py` | grim | Screenshots + OCR |
| `browser.py` | browser-use | Web automation with multi-LLM support |
| `memory.py` | File I/O | Persistent memory storage and retrieval |
| `legacy.py` | xdotool | Fallback for scroll on non-Wayland |

### 6. Configuration (`src/config.py`)

Environment-based configuration with defaults:

```python
def _env_bool(name: str, default: bool) -> bool
def _env_int(name: str, default: int) -> int

# Memory config
get_memory_enabled() -> bool
get_memory_file() -> str
get_memory_dir() -> str
get_memory_max_context_chars() -> int

# Wake word config
get_wakeword_enabled() -> bool
get_wakeword_model_path() -> str
get_wakeword_threshold() -> float
get_wakeword_debounce() -> float
```

---

## Pipeline Flow

### Startup Sequence

```
1. agent.py loads .env
2. PipelineController created with JobContext
3. If wakeword enabled:
   - Load wake word model
   - Start listening loop
4. If wakeword disabled (console mode):
   - Start session immediately
```

### Voice Conversation Flow

```
User speaks
    │
    ▼
VAD (Voice Activity Detection) ──► Silence? ──► Return to IDLE
    │
    ▼
STT (Speech-to-Text) ──► Transcript
    │
    ▼
LLM (Language Model) ──► Generate reply + tools
    │
    ├──────────┐
    ▼          ▼
Execute   Generate
tools      text
    │          │
    ▼          ▼
Tool       TTS (Text-to-Speech)
results     │
    │       │
    └───────┘
         │
         ▼
    Play audio ──► Return to IDLE
```

### Memory Flow

```
Startup:
1. ensure_memory_files() → Create MEMORY.md + memory/ if missing
2. build_memory_context() → Load memory files
3. Inject into agent instructions

During conversation:
- AI can call save_memory() → append to memory/YYYY-MM-DD.md
- AI can call memory_search() → keyword search across files
- AI can call memory_get() → read specific line range

Shutdown:
- flush_session_memory() → Extract durable items from history
- Append to memory/YYYY-MM-DD.md
```

---

## Wake Word Detection

### Setup

1. Install dependencies:
   ```bash
   sudo apt install portaudio19-dev
   ```

2. Download or train model:
   - Pre-trained: `models/hey_livekit.onnx`
   - Custom: Train with `livekit-wakeword run configs/hey_crix.yaml`

3. Configure in `.env`:
   ```env
   CRIX_WAKEWORD_ENABLED=true
   CRIX_WAKEWORD_MODEL_PATH=models/hey_livekit.onnx
   CRIX_WAKEWORD_THRESHOLD=0.5
   CRIX_WAKEWORD_DEBOUNCE=2.0
   ```

### Running

```bash
# With wake word (always-on)
nohup uv run src/agent.py dev > crix.log 2>&1 &

# Without wake word (manual)
uv run src/agent.py console
```

### As Systemd Service

Create `~/.config/systemd/user/crix.service`:
```ini
[Unit]
Description=Crix Voice Assistant

[Service]
ExecStart=/home/user/.local/bin/uv run /path/to/Crix/src/agent.py dev
WorkingDirectory=/path/to/Crix
Restart=on-failure

[Install]
WantedBy=default.target
```

Enable:
```bash
systemctl --user daemon-reload
systemctl --user enable --now crix
```

---

## Memory System

### Files

| File | Purpose |
|------|---------|
| `MEMORY.md` | Long-term stable memory (preferences, routines) |
| `memory/YYYY-MM-DD.md` | Daily session memory (append-only) |

### Structure

```markdown
# MEMORY.md
# Crix Memory

## Profile
- User's name: Alex
- Preferred browser: Chrome

## Routines
- Morning brief: Check email, summarize schedule
```

```markdown
# memory/2026-04-09.md
# Memory Log 2026-04-09

- [14:30:00] category=general source=tool confidence=0.95
  User prefers to be called jojo
```

### Tools

- **save_memory(note, category, confidence)** - Save new memory
- **memory_search(query, limit)** - Search across all memory files
- **memory_get(path, from_line, lines)** - Read specific snippet

### Security

- Sensitive values (API keys, passwords, OTPs) are redacted before writing
- Memory files are gitignored by default
- User can clear memory with "forget X" commands

---

## Tool System

### Tool Definition Pattern

```python
@function_tool
async def my_tool(context: RunContext, param1: str, param2: int = 10) -> str:
    """
    Tool description for the AI.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default: 10)
    """
    # Implementation
    return "Result string"
```

### Tool Registration

Tools are registered in the `Assistant` class:

```python
class Assistant(Agent):
    def __init__(self, instructions: str = SYSTEM_PROMPT) -> None:
        super().__init__(
            instructions=instructions,
            tools=[
                type_text,
                press_key,
                # ... all tools
            ],
        )
```

### Tool Execution Flow

1. User speaks command
2. STT converts to text
3. LLM decides which tools to call and with what arguments
4. LiveKit Agents framework executes tools
5. Tool results returned to LLM
6. LLM generates final response
7. TTS speaks response

---

## Browser Automation

### Architecture

```
browse_web(task: str, max_steps: int = 20)
    │
    ▼
BrowserUseAgent (browser-use library)
    │
    ├── Initialize browser with user's Chrome profile
    ├── Create AgentWithContinue
    │
    ├── For each step:
    │   ├── AI decides action (navigate, click, type, etc.)
    │   ├── Execute action
    │   ├── Get result + screenshot
    │   └── Check if task complete
    │
    └── Return detailed step-by-step logs
```

### Features

- Uses **real Chrome profile** — stays logged into all sites
- Multi-step task execution
- Detailed logging for AI context
- Supports multiple LLM providers:
  - OpenAI (GPT-4o Mini)
  - Anthropic (Claude)
  - Google Gemini
  - Ollama (local)

### Configuration

```env
# Browser LLM (cannot use LiveKit's managed LLM)
OPENAI_API_KEY=sk-...

# Or alternatives:
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...
# OLLAMA_MODEL=llama2

# Chrome profile
CRIX_CHROME_PROFILE=Default
```

---

## Configuration

### Environment Variables

#### LiveKit (Required)
| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | WebSocket URL from LiveKit Cloud |
| `LIVEKIT_API_KEY` | API key |
| `LIVEKIT_API_SECRET` | API secret |

#### Web Search (Required)
| Variable | Description |
|----------|-------------|
| `TAVILY_API_KEY` | API key from tavily.com |

#### Browser Automation (Optional)
| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | For browser-use LLM |
| `ANTHROPIC_API_KEY` | Alternative |
| `GOOGLE_API_KEY` | Alternative |
| `OLLAMA_MODEL` | Local alternative |
| `CRIX_CHROME_PROFILE` | Chrome profile name |

#### Memory (Optional)
| Variable | Default | Description |
|----------|---------|-------------|
| `CRIX_MEMORY_ENABLED` | true | Enable memory |
| `CRIX_MEMORY_FILE` | MEMORY.md | Main memory file |
| `CRIX_MEMORY_DIR` | memory | Daily memory directory |
| `CRIX_MEMORY_MAX_CONTEXT_CHARS` | 3500 | Startup context limit |
| `CRIX_MEMORY_SEARCH_LIMIT` | 5 | Search result limit |
| `CRIX_MEMORY_FLUSH_ENABLED` | true | Flush on shutdown |

#### Wake Word (Optional)
| Variable | Default | Description |
|----------|---------|-------------|
| `CRIX_WAKEWORD_ENABLED` | true | Enable wake word |
| `CRIX_WAKEWORD_MODEL_PATH` | models/hey_livekit.onnx | Model path |
| `CRIX_WAKEWORD_THRESHOLD` | 0.5 | Detection threshold |
| `CRIX_WAKEWORD_DEBOUNCE` | 2.0 | Debounce seconds |

---

## Development

### Project Structure

```
crix/
├── src/
│   ├── agent.py              # Main entry point
│   ├── tools.py              # Tool definitions
│   ├── config.py             # Configuration
│   ├── keycodes.py           # Keycode mappings
│   ├── wakeword/
│   │   ├── __init__.py
│   │   ├── detector.py       # Wake word detection
│   │   └── pipeline.py       # Pipeline controller
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── ydotool.py        # Input simulation
│   │   ├── gnome.py         # GNOME integration
│   │   ├── clipboard.py     # Clipboard
│   │   ├── screenshot.py    # Screenshots
│   │   ├── browser.py       # Browser automation
│   │   ├── memory.py        # Memory system
│   │   └── legacy.py        # Fallbacks
│   └── prompts/
│       ├── crix.py           # System prompt
│       └── __init__.py
├── models/                   # Wake word models
├── configs/                  # Training configs
├── memory/                   # Daily memory logs
├── MEMORY.md                 # Long-term memory
└── pyproject.toml
```

### Adding New Tools

1. Define in `src/tools.py`:
   ```python
   @function_tool
   async def my_new_tool(context: RunContext, param: str) -> str:
       """Description"""
       return "result"
   ```

2. Register in `src/agent.py`:
   ```python
   from tools import my_new_tool
   
   tools=[
       # ... existing
       my_new_tool,
   ]
   ```

### Adding New Backends

1. Create `src/backends/new_backend.py`
2. Implement functions
3. Export in `src/backends/__init__.py`
4. Use in tools

### Running in Development

```bash
# Console mode (no wake word)
uv run src/agent.py console

# Dev server mode
uv run src/agent.py dev

# With live reload
uv run --watch src/agent.py dev
```

---

## License

MIT — See [LICENSE](LICENSE) file.