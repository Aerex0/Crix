"""
Crix voice assistant tools for GNOME on Wayland.

This module provides function tools that can be called by the AI assistant
to control the desktop environment.

Backends:
- ydotool: Keyboard and mouse input simulation
- gnome (gdbus): Workspace and window management
- wl-clipboard: Clipboard operations
- grim: Screenshots
- xdotool (legacy): Scroll only
"""

import subprocess
import shlex
import time
import os
from livekit.agents import function_tool, RunContext
from tavily import TavilyClient

from backends import ydotool, gnome, clipboard, screenshot, legacy
from backends.memory import append_memory_entry, memory_get as memory_get_snippet
from backends.memory import memory_search as memory_search_backend
from config import get_memory_default_search_limit


# ─────────────────────────────────────────────
# REALTIME TOOLS
# ─────────────────────────────────────────────


@function_tool
async def web_search(context: RunContext, query: str) -> str:
    """
    Search the web for up-to-date information.
    Use this when asked for current events, facts, or anything requiring recent data.

    Args:
        query: The search query
    """
    client = TavilyClient()
    response = client.search(query, search_depth="advanced")
    return f"Web search result: {response}"


@function_tool
async def get_time(context: RunContext) -> str:
    """
    Get the current date and time.
    Use this when asked about the current time or date.
    """
    return f"Current date and time: {time.ctime()}"


@function_tool
async def save_memory(
    context: RunContext,
    note: str,
    category: str = "general",
    confidence: float = 0.8,
) -> str:
    """
    Save durable user memory for future sessions.
    Use this for preferences, routines, decisions, and important follow-ups.

    Args:
        note: The memory text to persist
        category: Memory category (general, preference, routine, todo, session)
        confidence: Confidence score from 0.0 to 1.0
    """
    clamped_confidence = max(0.0, min(1.0, confidence))
    return append_memory_entry(
        note,
        category=category,
        source="tool",
        confidence=clamped_confidence,
    )


@function_tool
async def memory_search(
    context: RunContext, query: str, limit: int | None = None
) -> str:
    """
    Search MEMORY.md and memory/*.md for relevant prior context.

    Args:
        query: What memory to look up
        limit: Maximum number of hits
    """
    max_hits = limit if limit is not None else get_memory_default_search_limit()
    hits = memory_search_backend(query, limit=max_hits)
    if not hits:
        return "No matching memory found"

    lines = [f"Found {len(hits)} memory hits:"]
    for hit in hits:
        lines.append(f"- {hit.path}:{hit.line} (score={hit.score}) {hit.text}")
    return "\n".join(lines)


@function_tool
async def memory_get(
    context: RunContext,
    path: str,
    from_line: int = 1,
    lines: int = 20,
) -> str:
    """
    Read a focused snippet from a memory file returned by memory_search.

    Args:
        path: Relative file path (MEMORY.md or memory/*.md)
        from_line: Start line number
        lines: Number of lines to read
    """
    return memory_get_snippet(path=path, from_line=from_line, lines=lines)


# ─────────────────────────────────────────────
# KEYBOARD TOOLS (ydotool)
# ─────────────────────────────────────────────


@function_tool
async def type_text(context: RunContext, text: str) -> str:
    """
    Type text at the current cursor position, as if physically pressing keys.
    Use this to fill forms, write messages, type in terminals, search bars, etc.

    Args:
        text: The text to type.
    """
    return ydotool.type_text(text)


@function_tool
async def press_key(context: RunContext, key: str) -> str:
    """
    Press a single key or key combination.
    Examples: 'Return', 'Escape', 'ctrl+c', 'super+q', 'alt+Tab', 'ctrl+t', 'ctrl+w'
    Note: Use 'Return' or 'enter' for the Enter key. Combos like 'ctrl+c' work directly.

    Args:
        key: Key name or combo like 'ctrl+c', 'super+q'.
    """
    return ydotool.press_key(key)


@function_tool
async def type_and_submit(context: RunContext, text: str) -> str:
    """
    Type text and immediately press Enter. Useful for sending messages,
    running terminal commands, submitting searches.

    Args:
        text: Text to type before pressing Enter.
    """
    ydotool.type_text(text)
    time.sleep(0.05)  # Small delay between typing and Enter
    return ydotool.press_key("Return")


@function_tool
async def paste_text(context: RunContext, text: str) -> str:
    """
    Paste text instantly using clipboard — much faster than typing for long text.
    Copies to clipboard then sends Ctrl+V.

    Args:
        text: Text to paste.
    """
    clipboard.copy(text)
    time.sleep(0.05)
    ydotool.press_key("ctrl+v")
    return f"Pasted {len(text)} characters via clipboard"


# ─────────────────────────────────────────────
# MOUSE TOOLS (ydotool)
# ─────────────────────────────────────────────


@function_tool
async def move_mouse(context: RunContext, x: int, y: int) -> str:
    """
    Move the mouse cursor to absolute screen coordinates.

    Args:
        x: Horizontal position in pixels from left.
        y: Vertical position in pixels from top.
    """
    return ydotool.move_mouse(x, y, absolute=True)


@function_tool
async def click(context: RunContext, x: int, y: int, button: int = 1) -> str:
    """
    Move mouse to coordinates and click.

    Args:
        x: Horizontal position.
        y: Vertical position.
        button: 1=left, 2=middle, 3=right (default 1).
    """
    return ydotool.click(x, y, button)


@function_tool
async def double_click(context: RunContext, x: int, y: int) -> str:
    """
    Double-click at given coordinates (e.g. to open files or apps).

    Args:
        x: Horizontal position.
        y: Vertical position.
    """
    return ydotool.double_click(x, y)


@function_tool
async def scroll(context: RunContext, direction: str, amount: int = 3) -> str:
    """
    Scroll the mouse wheel at the current cursor position.
    Note: Uses xdotool fallback as ydotool doesn't support scroll.

    Args:
        direction: 'up' or 'down'.
        amount: Number of scroll ticks (default 3).
    """
    return legacy.scroll(direction, amount)


# ─────────────────────────────────────────────
# WINDOW & WORKSPACE TOOLS (gdbus/GNOME)
# ─────────────────────────────────────────────


@function_tool
async def switch_workspace(context: RunContext, workspace_number: int) -> str:
    """
    Switch to a specific virtual desktop/workspace by number (1-based).
    Uses native GNOME Shell API for reliable switching.

    Args:
        workspace_number: Workspace to switch to (e.g. 1, 2, 3, 4).
    """
    return gnome.switch_workspace(workspace_number)


@function_tool
async def list_open_windows(context: RunContext) -> str:
    """
    Open the window switcher (Alt+Tab) to show all open windows.
    The user can then navigate with Tab and select with Enter.
    Note: This is interactive - it shows the visual switcher overlay.
    """
    return gnome.list_open_windows()


@function_tool
async def focus_window(context: RunContext, app_name: str) -> str:
    """
    Search for and focus a window using GNOME Activities search.
    Opens Activities overview and types the search pattern.
    The user can press Enter to select the matching window.
    Examples: 'firefox', 'terminal', 'code', 'slack', 'discord'.

    Args:
        app_name: Partial name of the app or window title.
    """
    return gnome.focus_window(app_name)


@function_tool
async def open_app(context: RunContext, app_command: str) -> str:
    """
    Launch an application or open a file. Runs detached so it doesn't block.
    Examples: 'alacritty', 'firefox', 'brave-browser', 'antigravity'.

    Args:
        app_command: Shell command or app name to launch.
    """
    try:
        subprocess.Popen(
            shlex.split(app_command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return f"Launched: {app_command}"
    except Exception as e:
        return f"Error launching app: {e}"


# ─────────────────────────────────────────────
# CLIPBOARD & SCREEN TOOLS
# ─────────────────────────────────────────────


@function_tool
async def get_clipboard(context: RunContext) -> str:
    """
    Read the current clipboard contents.
    Useful to grab selected text, URLs, or copied content.
    """
    content = clipboard.paste()
    if not content:
        return "Clipboard is empty."
    if len(content) > 500:
        return f"Clipboard (truncated): {content[:500]}..."
    return f"Clipboard contents: {content}"


@function_tool
async def select_all_and_copy(context: RunContext) -> str:
    """
    Press Ctrl+A to select all, then Ctrl+C to copy.
    Returns the copied text. Great for reading message counts or full text field content.
    """
    ydotool.press_key("ctrl+a")
    time.sleep(0.1)
    ydotool.press_key("ctrl+c")
    time.sleep(0.15)

    content = clipboard.paste()
    if not content:
        return "Nothing was copied (selection may be empty)."
    if len(content) > 600:
        return f"Copied text (truncated): {content[:600]}..."
    return f"Copied text: {content}"


@function_tool
async def read_screen_text(context: RunContext, region: str = "full") -> str:
    """
    Take a screenshot and extract all visible text using OCR (tesseract).
    Use this to 'see' what's on screen — count messages, read notifications, check app state.

    Args:
        region: 'full' for entire screen, or 'top', 'bottom', 'left', 'right' for half-screen.
    """
    try:
        import pytesseract
        from PIL import Image

        # Get screen size dynamically
        width, height = gnome.get_screen_size()

        # Capture screenshot
        tmp_path = screenshot.capture_screen(region=region, width=width, height=height)

        # OCR the image
        img = Image.open(tmp_path)
        text = pytesseract.image_to_string(img).strip()
        os.unlink(tmp_path)

        if not text:
            return "No text detected on screen."
        if len(text) > 800:
            text = text[:800] + "... [truncated]"

        return f"Screen text ({region}):\n{text}"

    except ImportError:
        return "Missing deps. Run: uv add pillow pytesseract && sudo apt install tesseract-ocr grim"
    except Exception as e:
        return f"Screen read error: {e}"


@function_tool
async def get_screen_size(context: RunContext) -> str:
    """
    Get the current screen resolution.
    """
    return gnome.get_screen_size_str()


# ─────────────────────────────────────────────
# SYSTEM TOOLS
# ─────────────────────────────────────────────

# Blocked commands for safety
BLOCKED_COMMANDS = {
    "rm",
    "mv",
    "dd",
    "mkfs",
    "kill",
    "killall",
    "pkill",
    "chmod",
    "chown",
    "sudo",
    "su",
    "shutdown",
    "reboot",
    "systemctl",
    "init",
    "halt",
    "poweroff",
}


@function_tool
async def run_command_silent(context: RunContext, command: str) -> str:
    """
    Run a shell command instantly and return its output.
    No user confirmation needed — executes immediately.
    Keep commands safe and non-destructive (reads, status checks, etc).

    Args:
        command: Shell command to run (e.g. 'ls ~/Downloads', 'whoami', 'date').
    """
    # Safety check
    first_word = command.strip().split()[0] if command.strip() else ""
    if first_word in BLOCKED_COMMANDS:
        return f"Blocked: '{first_word}' is not allowed for safety reasons"

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=8
        )
        output = result.stdout.strip() or result.stderr.strip() or "(no output)"
        if len(output) > 600:
            output = output[:600] + "... [truncated]"
        return f"{command} output: {output}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 8 seconds."
    except Exception as e:
        return f"Error: {e}"


# ─────────────────────────────────────────────
# BROWSER AUTOMATION TOOLS (browser-use)
# ─────────────────────────────────────────────

from backends.browser import execute_browser_task


@function_tool
async def browse_web(context: RunContext, task: str, max_steps: int = 30) -> str:
    """
    Perform complex web automation tasks using an AI browser agent.
    This tool can navigate websites, click buttons, fill forms, extract information,
    and complete multi-step workflows automatically.

    Use this for tasks that require:
    - Navigating multiple pages
    - Interacting with web forms and buttons
    - Shopping online (adding items to cart, comparing prices)
    - Checking social media or email
    - Filling out applications or surveys
    - Extracting structured data from websites
    - Any complex browser-based workflow

    Examples:
        "Search Google for 'best mechanical keyboards' and summarize the top 3 results"
        "Go to Amazon and add a Logitech MX Master 3S mouse to my cart"
        "Fill out the contact form at example.com with my info"
        "Check my Gmail and tell me how many unread emails I have"
        "Go to LinkedIn and summarize my latest notifications"

    Note: This uses your real Chrome browser profile, so you'll already be
    logged into websites like Gmail, Amazon, LinkedIn, etc.

    Args:
        task: Natural language description of what to accomplish
        max_steps: Maximum steps the browser agent can take (default 30)
    """
    return await execute_browser_task(task, max_steps)
