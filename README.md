# Crix — AI Voice Assistant for Linux Desktop

> **Crix** is a fast, efficient, voice-controlled AI assistant that runs natively on Linux. It gives an AI direct control over your keyboard, mouse, and system — so you can get things done entirely hands-free.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![LiveKit](https://img.shields.io/badge/Powered%20by-LiveKit-00BCD4?style=for-the-badge&logoColor=black)
![Tavily](https://img.shields.io/badge/Web%20Search-Tavily-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta-yellow?style=for-the-badge)

---

## Features

- 🎙️ **Real-time voice interaction** — Talk to Crix naturally using state-of-the-art speech recognition
- ⌨️ **Keyboard control** — Type text, press shortcuts, and submit forms by voice
- 🖱️ **Mouse control** — Move, click, double-click, and scroll anywhere on screen
- 🪟 **Window & Workspace management** — Switch workspaces, focus windows, list open apps
- 📋 **Clipboard integration** — Read and write clipboard content using `wl-clipboard`
- 🌐 **Browser automation** — Navigate websites, fill forms, shop online, check email via natural language
- 🔍 **Live web search** — Fetches up-to-date information from the web using Tavily
- 🖥️ **Shell command execution** — Run safe, non-destructive shell commands on demand
- 🔇 **Noise cancellation** — Intelligent audio filtering for cleaner voice input

---

## Tech Stack

| Component | Technology |
|---|---|
| Voice Framework | [LiveKit Agents](https://docs.livekit.io/agents/) |
| Speech-to-Text (STT) | Deepgram Nova-3 (multilingual) |
| Language Model (LLM) | OpenAI GPT-4.1 Mini |
| Text-to-Speech (TTS) | ElevenLabs Turbo v2.5 |
| Voice Activity Detection (VAD) | Silero |
| Input Simulation | `ydotool` (Wayland-native) |
| Window/Workspace Control | `gdbus` (GNOME Shell native) |
| Clipboard | `wl-clipboard` |
| Screenshots | `grim` |
| Scroll (fallback) | `xdotool` |
| Browser Automation | [browser-use](https://github.com/browser-use/browser-use) |
| Web Search | [Tavily](https://tavily.com) |
| Package Manager | [uv](https://github.com/astral-sh/uv) |

---

## Prerequisites

- **Linux** with **GNOME on Wayland** (other compositors may need adaptation)
- **Python 3.12+**
- [`uv`](https://github.com/astral-sh/uv) package manager
- A LiveKit account and project ([cloud.livekit.io](https://cloud.livekit.io))
- A [Tavily](https://tavily.com) API key for web search
- STT, LLM, and TTS are handled by **LiveKit** — no separate API keys needed for OpenAI, Deepgram, or ElevenLabs

### System Dependencies

```bash
# Arch Linux
sudo pacman -S ydotool wl-clipboard grim xdotool tesseract

# Debian/Ubuntu
sudo apt install ydotool wl-clipboard grim xdotool tesseract-ocr

# Fedora
sudo dnf install ydotool wl-clipboard grim xdotool tesseract
```

### Enable ydotoold Daemon

ydotool requires its daemon to be running:

```bash
# Enable and start the daemon (system-wide)
sudo systemctl enable --now ydotoold

# Or run as a user service (may require uinput permissions)
systemctl --user enable --now ydotoold
```

### Verify Installation

```bash
# Test ydotool (should type "hello" at cursor)
ydotool type "hello"

# Test wl-clipboard
echo "test" | wl-copy && wl-paste

# Test grim (should save screenshot)
grim /tmp/test.png && ls -la /tmp/test.png
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Aerex0/Crix.git
   cd Crix
   ```

2. **Install Python dependencies:**
   ```bash
   uv sync
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in your credentials:
   ```env
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   TAVILY_API_KEY=your_tavily_key
   
   # For browser automation, configure ONE of these:
   OPENAI_API_KEY=sk-...                    # Recommended
   # ANTHROPIC_API_KEY=sk-ant-...           # Alternative
   # GOOGLE_API_KEY=...                     # Alternative
   # OLLAMA_MODEL=llama2                    # Local/free alternative
   ```

   > **Note:** STT (Deepgram), LLM (OpenAI), and TTS (ElevenLabs) for voice interaction are billed and managed through your LiveKit account — no separate API keys required.
   > 
   > Browser automation uses a separate LLM and requires its own API key (cannot use LiveKit's managed LLM).

---

## Browser Automation Setup

Crix can automate complex web tasks using your real Chrome browser profile, preserving all your logins and settings.

### Prerequisites

Browser automation is already installed with Crix. You just need:

1. **An LLM API key** (browser-use cannot use LiveKit's managed LLM)
2. **Google Chrome** installed on your system

### Configure LLM for Browser Automation

Add ONE of the following to your `.env` file:

```bash
# Option 1: OpenAI (Recommended - most tested)
OPENAI_API_KEY=sk-...
BROWSER_USE_OPENAI_MODEL=gpt-4o-mini  # Optional: override default model

# Option 2: Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
BROWSER_USE_ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Option 3: Google Gemini  
GOOGLE_API_KEY=...
BROWSER_USE_GOOGLE_MODEL=gemini-2.0-flash-exp

# Option 4: Ollama (Local, free, no API key needed)
OLLAMA_MODEL=llama2  # or llama3, mistral, etc.
```

### Chrome Profile Configuration (Optional)

By default, Crix uses your Default Chrome profile. To use a different profile:

```bash
# List available Chrome profiles
ls ~/.config/google-chrome/

# Set in .env
CRIX_CHROME_PROFILE=Profile 1  # or Profile 2, Profile 3, etc.
```

### Voice Commands

Once configured, you can use natural language to control browsers:

```
"Search Google for best Linux laptops and summarize the results"
"Add a mechanical keyboard to my Amazon cart"
"Check my Gmail and tell me how many unread emails I have"
"Fill out the contact form at example.com"
"Go to LinkedIn and check my notifications"
"Compare prices for wireless mice on Amazon and Newegg"
```

### How It Works

- **Uses your real Chrome profile** — Already logged into Gmail, Amazon, etc.
- **Multi-step automation** — Can navigate, click, fill forms, extract data
- **Voice-controlled** — Just describe what you want in natural language
- **Smart task routing** — Crix knows when to use browser automation vs. simple web search

---

## Usage

Run the agent using the LiveKit CLI:

```bash
uv run python src/agent.py console
```

Once running, connect to the agent via any LiveKit-compatible client (e.g. the LiveKit Playground or a custom frontend). Crix will greet you and wait for voice commands.

---

## Customization

Before using Crix, **you may want to update the system prompt** to match your preferences. Open `src/prompts/crix.py` and adjust it to reflect:

- **Your default apps** — e.g. your terminal emulator (`gnome-terminal`, `kitty`, `alacritty`), browser (`firefox`, `brave`), etc.
- **Your preferred shortcuts** — e.g. how you close a window (`alt+f4`, `super+q`)

> [!NOTE]
> The default prompt is configured for GNOME on Wayland. Workspace switching uses native GNOME APIs via gdbus, so it should work out of the box.

---

## Available Tools

Crix comes with a set of built-in tools it can call autonomously based on your voice commands:

### 🌐 Browser Automation
| Tool | Description |
|---|---|
| `browse_web` | AI-powered browser automation for complex web tasks (navigation, forms, shopping, email, etc.) |

### 🔍 Web & Time
| Tool | Description |
|---|---|
| `web_search` | Search the web for up-to-date information using Tavily (fast, for simple queries) |
| `get_time` | Get the current system date and time |

### ⌨️ Keyboard
| Tool | Description |
|---|---|
| `type_text` | Type text at the current cursor position |
| `press_key` | Press a key or key combo (e.g. `ctrl+c`, `super+q`) |
| `type_and_submit` | Type text and immediately press Enter |
| `paste_text` | Paste text instantly via clipboard (faster for long strings) |

### 🖱️ Mouse
| Tool | Description |
|---|---|
| `move_mouse` | Move cursor to absolute screen coordinates |
| `click` | Click at a given position (left, middle, or right button) |
| `double_click` | Double-click at a given position |
| `scroll` | Scroll up or down at the current cursor position |

### 🪟 Windows & Apps
| Tool | Description |
|---|---|
| `switch_workspace` | Switch to a specific workspace (1-based) via GNOME API |
| `focus_window` | Focus a window by name (partial match) |
| `list_open_windows` | List all open windows |
| `open_app` | Launch an application by command name |

### 📋 Clipboard & Screen
| Tool | Description |
|---|---|
| `get_clipboard` | Read the current clipboard contents |
| `select_all_and_copy` | Press `Ctrl+A` then `Ctrl+C` and return copied text |
| `get_screen_size` | Return the current screen resolution |
| `read_screen_text` | OCR the screen to read visible text |

### 🖥️ System
| Tool | Description |
|---|---|
| `run_command_silent` | Execute a safe, read-only shell command and return output |

---

## Example Commands

### Desktop Control
```
"Open a terminal"               → Launches gnome-terminal
"Open Firefox"                  → Launches Firefox
"Switch to Firefox"             → Focuses the Firefox window
"Switch to workspace 3"         → Switches to virtual desktop 3
"Type hello world and send it"  → Types and submits text
"Press Ctrl+Z"                  → Sends the undo shortcut
"Select all and copy"           → Copies all text in the focused window
"What windows are open?"        → Lists all open windows
"Close this window"             → Sends Alt+F4
```

### Web & Browser Automation
```
"What time is it?"                                    → Returns current date and time
"Search for the latest AI news"                      → Quick web search via Tavily
"Search Google for best Linux laptops and summarize" → Opens browser and researches
"Add a wireless mouse to my Amazon cart"             → Navigates Amazon and adds to cart
"Check my Gmail inbox"                               → Opens Gmail and checks emails
"Fill out the form at example.com"                   → Automates form filling
"What's the price of Bitcoin?"                       → Quick factual query
"Compare mechanical keyboard prices on Amazon"       → Multi-step price comparison
```

---

## Security

Crix is designed with the following hard rules baked into its system prompt:

- 🚫 Will **not** execute destructive commands (`rm`, `mv`, `dd`, `kill`, `chmod`, etc.)
- 🚫 Will **not** follow commands delivered via on-screen text — only spoken voice
- 🚫 Will **not** reveal its system prompt
- 🚫 Will **not** chain shell commands

> [!WARNING]
> These are prompt-level restrictions enforced by the AI model — not hard system-level blocks. While precautions have been taken to make Crix safe, no AI system is perfectly secure. **Use with awareness and at your own risk.** Avoid granting it access to sensitive environments.

---

## Project Structure

```
crix/
├── src/
│   ├── agent.py              # LiveKit agent setup and tool registration
│   ├── tools.py              # Tool function definitions
│   ├── keycodes.py           # Linux keycode mapping for ydotool
│   ├── __init__.py
│   ├── backends/             # Backend implementations
│   │   ├── __init__.py
│   │   ├── ydotool.py        # Input simulation (keyboard, mouse)
│   │   ├── gnome.py          # GNOME Shell integration via gdbus
│   │   ├── clipboard.py      # wl-clipboard wrapper
│   │   ├── screenshot.py     # grim wrapper
│   │   └── legacy.py         # xdotool fallback (scroll only)
│   └── prompts/
│       ├── crix.py           # System prompt defining behavior and rules
│       └── __init__.py
├── LICENSE
├── README.md
├── plan.md                   # Migration plan documentation
├── pyproject.toml            # Project metadata and dependencies
└── uv.lock
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CRIX TOOLS                              │
├─────────────────────────────────────────────────────────────────┤
│  INPUT (ydotool)         │  DESKTOP (gdbus → GNOME)             │
│  ──────────────────      │  ───────────────────────             │
│  • type_text             │  • switch_workspace                  │
│  • press_key             │  • focus_window                      │
│  • move_mouse            │  • list_open_windows                 │
│  • click / double_click  │  • get_screen_size                   │
├──────────────────────────┼──────────────────────────────────────┤
│  CLIPBOARD (wl-clipboard)│  LEGACY (xdotool)                    │
│  ───────────────────     │  ─────────────                       │
│  • get_clipboard         │  • scroll                            │
│  • paste_text            │                                      │
├──────────────────────────┼──────────────────────────────────────┤
│  SCREENSHOT (grim)       │  UNCHANGED                           │
│  ─────────────────       │  ─────────                           │
│  • read_screen_text      │  • web_search, get_time, open_app    │
└─────────────────────────────────────────────────────────────────┘
```

---

## License

This project is licensed under the [MIT License](LICENSE).
