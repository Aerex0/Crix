# Crix — AI Voice Assistant for Linux Desktop

> **Full documentation:** See [PROJECT.md](PROJECT.md) for complete architecture, API details, and development guide.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![LiveKit](https://img.shields.io/badge/Powered%20by-LiveKit-00BCD4?style=for-the-badge&logoColor=black)
![Tavily](https://img.shields.io/badge/Web%20Search-Tavily-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta-yellow?style=for-the-badge)

---

## Features

- 🎙️ **Real-time voice interaction** — Talk to Crix naturally
- ⌨️ **Keyboard control** — Type text, press shortcuts by voice
- 🖱️ **Mouse control** — Move, click, scroll anywhere
- 🪟 **Window & Workspace** — Switch workspaces, focus windows
- 🌐 **Browser automation** — Web tasks via natural language
- 🧠 **Persistent memory** — Remembers preferences across sessions
- 🔍 **Live web search** — Up-to-date information via Tavily
- 🔇 **Noise cancellation** — Intelligent audio filtering

---

## Quick Start

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt install ydotool wl-clipboard grim xdotool tesseract-ocr portaudio19-dev

# Enable ydotool daemon
sudo systemctl enable --now ydotoold
```

### 2. Clone and Install

```bash
git clone https://github.com/Aerex0/Crix.git
cd Crix
uv sync
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
TAVILY_API_KEY=your_tavily_key

# For browser automation (choose one):
OPENAI_API_KEY=sk-...     # Recommended
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...
# OLLAMA_MODEL=llama3.1
```

### 4. Run

```bash
# With wake word (always-on) - say "hey livekit" to activate
nohup uv run src/agent.py dev > crix.log 2>&1 &

# Or without wake word (manual mode)
uv run src/agent.py console
```

---

## Usage

### Voice Commands

```
"Open Firefox"                    → Launch app
"Switch to workspace 3"           → Change desktop
"Type hello world"                → Type text
"Search Google for AI news"       → Browser search
"Check my Gmail"                  → Open Gmail via browser
"Add mouse to Amazon cart"        → Shopping automation
"What time is it?"                → Get current time
```

### Memory Commands

```
"Remember that I prefer dark mode"    → Save preference
"What did I tell you about my name?"  → Search memory
```

---

## Wake Word Setup

Crix listens for **"hey livekit"** by default. To use a custom wake word:

```bash
# Train custom model
uv run livekit-wakeword run configs/hey_crix.yaml

# Update .env
CRIX_WAKEWORD_MODEL_PATH=models/hey_crix.onnx
```

### Run on Boot (Optional)

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

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CRIX_WAKEWORD_ENABLED` | true | Enable wake word |
| `CRIX_MEMORY_ENABLED` | true | Enable memory |
| `CRIX_CHROME_PROFILE` | Default | Chrome profile |

See [PROJECT.md](PROJECT.md) for full configuration reference.

---

## Tech Stack

| Component | Technology |
|---|---|
| Voice Framework | [LiveKit Agents](https://docs.livekit.io/agents/) |
| STT | Deepgram Nova-3 |
| LLM | OpenAI GPT-4.1 Mini |
| TTS | ElevenLabs Turbo |
| VAD | Silero |
| Input | ydotool |
| Browser | browser-use |
| Web Search | Tavily |

---

## Project Structure

```
crix/
├── src/
│   ├── agent.py              # Entry point
│   ├── tools.py              # Voice tools
│   ├── config.py             # Configuration
│   ├── wakeword/             # Wake word detection
│   └── backends/             # System backends
├── models/                   # Wake word models
├── memory/                   # Session memory
├── MEMORY.md                 # Long-term memory
├── PROJECT.md               # Full documentation
└── pyproject.toml
```

---

## License

MIT — See [LICENSE](LICENSE) file.
