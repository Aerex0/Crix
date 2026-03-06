import subprocess
import time
import tempfile
import os
from livekit.agents import function_tool, RunContext


def _xdo(*args) -> subprocess.CompletedProcess:
    """Run an xdotool command and return the result."""
    return subprocess.run(["xdotool"] + list(args), capture_output=True, text=True)


def _clip_copy(text: str):
    """Copy text to clipboard using xclip."""
    subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True)


def _clip_paste() -> str:
    """Read clipboard contents using xclip."""
    result = subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"],
        capture_output=True, text=True
    )
    return result.stdout

# ─────────────────────────────────────────────
# REALTIME TOOLS
# ─────────────────────────────────────────────

@function_tool
async def web_search(self, context: RunContext, query: str):
    """
    When asked for information that requires searching the web, use this tool.
    Do not use your own knowledge, always search for the most up-to-date information.

    Args:
        query: The search query
    """
    client = TavilyClient()
    response = client.search(query, search_depth="advanced")
    return f"Web search result: {response}"

@function_tool
async def get_time(self, context: RunContext):
    """
    When asked for the current date and time, use this tool.
    Do not use your own knowledge, always search for the most up-to-date information.
    """ 
    return f"Current date and time: {time.ctime()}"

# ─────────────────────────────────────────────
# KEYBOARD TOOLS
# ─────────────────────────────────────────────

@function_tool()
async def type_text(context: RunContext, text: str) -> str:
    """
    Type text at the current cursor position, as if physically pressing keys.
    Use this to fill forms, write messages, type in terminals, search bars, etc.

    Args:
        text: The text to type.
    """
    _xdo("type", "--delay", "30", "--", text)
    return f"Typed: {text!r}"


@function_tool()
async def press_key(context: RunContext, key: str) -> str:
    """
    Press a single key or key combination.
    Examples: 'Return', 'Escape', 'ctrl+c', 'ctrl+alt+t', 'super+d', 'alt+Tab', 'ctrl+shift+t'.
    Note: Use 'Return' not 'enter'. Combos like 'ctrl+c' work directly.

    Args:
        key: Key name or combo like 'ctrl+c', 'alt+F4', 'super+Left'.
    """
    _xdo("key", key)
    return f"Pressed: {key}"


@function_tool()
async def type_and_submit(context: RunContext, text: str) -> str:
    """
    Type text and immediately press Enter. Useful for sending messages,
    running terminal commands, submitting searches.

    Args:
        text: Text to type before pressing Enter.
    """
    _xdo("type", "--delay", "30", "--", text)
    _xdo("key", "Return")
    return f"Typed and submitted: {text!r}"


@function_tool()
async def paste_text(context: RunContext, text: str) -> str:
    """
    Paste text instantly using clipboard — much faster than typing for long text.
    Copies to clipboard then sends Ctrl+V.

    Args:
        text: Text to paste.
    """
    _clip_copy(text)
    time.sleep(0.05)
    _xdo("key", "ctrl+v")
    return f"Pasted {len(text)} characters via clipboard"


# ─────────────────────────────────────────────
# MOUSE TOOLS
# ─────────────────────────────────────────────

@function_tool()
async def move_mouse(context: RunContext, x: int, y: int) -> str:
    """
    Move the mouse cursor to absolute screen coordinates.

    Args:
        x: Horizontal position in pixels from left.
        y: Vertical position in pixels from top.
    """
    _xdo("mousemove", "--sync", str(x), str(y))
    return f"Mouse moved to ({x}, {y})"


@function_tool()
async def click(context: RunContext, x: int, y: int, button: int = 1) -> str:
    """
    Move mouse to coordinates and click.

    Args:
        x: Horizontal position.
        y: Vertical position.
        button: 1=left, 2=middle, 3=right (default 1).
    """
    _xdo("mousemove", "--sync", str(x), str(y))
    _xdo("click", str(button))
    btn_name = {1: "Left", 2: "Middle", 3: "Right"}.get(button, str(button))
    return f"{btn_name} clicked at ({x}, {y})"


@function_tool()
async def double_click(context: RunContext, x: int, y: int) -> str:
    """
    Double-click at given coordinates (e.g. to open files or apps).

    Args:
        x: Horizontal position.
        y: Vertical position.
    """
    _xdo("mousemove", "--sync", str(x), str(y))
    _xdo("click", "--repeat", "2", "--delay", "100", "1")
    return f"Double-clicked at ({x}, {y})"


@function_tool()
async def scroll(context: RunContext, direction: str, amount: int = 3) -> str:
    """
    Scroll the mouse wheel at the current cursor position.

    Args:
        direction: 'up' or 'down'.
        amount: Number of scroll ticks (default 3).
    """
    # xdotool: button 4 = scroll up, button 5 = scroll down
    button = "4" if direction == "up" else "5"
    _xdo("click", "--repeat", str(amount), "--delay", "50", button)
    return f"Scrolled {direction} by {amount}"


# ─────────────────────────────────────────────
# WINDOW & WORKSPACE TOOLS
# ─────────────────────────────────────────────

@function_tool()
async def switch_workspace(context: RunContext, workspace_number: int) -> str:
    """
    Switch to a specific virtual desktop/workspace by number (1-based).

    Args:
        workspace_number: Workspace to switch to (e.g. 1, 2, 3, 4).
    """
    result = _xdo("set_desktop", str(workspace_number - 1))
    if result.returncode == 0:
        return f"Switched to workspace {workspace_number}"
    return f"Error: {result.stderr}"


@function_tool()
async def focus_window(context: RunContext, app_name: str) -> str:
    """
    Find and focus a window by application name or window title.
    Examples: 'firefox', 'terminal', 'code', 'slack', 'discord'.

    Args:
        app_name: Partial name of the app or window title.
    """
    result = _xdo("search", "--onlyvisible", "--name", app_name)
    if result.stdout.strip():
        win_id = result.stdout.strip().split("\n")[0]
        _xdo("windowactivate", "--sync", win_id)
        return f"Focused window: {app_name}"

    # Fallback: try by class
    result2 = _xdo("search", "--onlyvisible", "--class", app_name)
    if result2.stdout.strip():
        win_id = result2.stdout.strip().split("\n")[0]
        _xdo("windowactivate", "--sync", win_id)
        return f"Focused window by class: {app_name}"

    return f"Could not find a window matching '{app_name}'"


@function_tool()
async def list_open_windows(context: RunContext) -> str:
    """
    List all currently open windows and their titles.
    Useful to know what apps are running before focusing one.
    """
    result = _xdo("search", "--onlyvisible", "--name", "")
    win_ids = result.stdout.strip().split("\n") if result.stdout.strip() else []

    titles = []
    for wid in win_ids[:20]:
        t = _xdo("getwindowname", wid)
        if t.stdout.strip():
            titles.append(t.stdout.strip())

    if titles:
        return "Open windows:\n" + "\n".join(f"  - {t}" for t in titles)
    return "No visible windows found"


@function_tool()
async def open_app(context: RunContext, app_command: str) -> str:
    """
    Launch an application or open a file. Runs detached so it doesn't block.
    Examples: 'firefox', 'code', 'nautilus', 'gnome-terminal', 'spotify'.

    Args:
        app_command: Shell command or app name to launch.
    """
    subprocess.Popen(
        app_command.split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    return f"Launched: {app_command}"


# ─────────────────────────────────────────────
# SCREEN READING TOOLS
# ─────────────────────────────────────────────

@function_tool()
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

        # Get screen size via xdotool
        r = subprocess.run(
            ["xdotool", "getdisplaygeometry"],
            capture_output=True, text=True
        )
        sw, sh = map(int, r.stdout.strip().split())

        region_map = {
            "full":   (0,       0,       sw,      sh),
            "top":    (0,       0,       sw,      sh // 2),
            "bottom": (0,       sh // 2, sw,      sh // 2),
            "left":   (0,       0,       sw // 2, sh),
            "right":  (sw // 2, 0,       sw // 2, sh),
        }
        x, y, w, h = region_map.get(region, region_map["full"])

        # Take screenshot with scrot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name

        subprocess.run(
            ["scrot", "-a", f"{x},{y},{w},{h}", tmp_path],
            capture_output=True
        )

        img = Image.open(tmp_path)
        text = pytesseract.image_to_string(img).strip()
        os.unlink(tmp_path)

        if not text:
            return "No text detected on screen."
        if len(text) > 800:
            text = text[:800] + "... [truncated]"

        return f"Screen text ({region}):\n{text}"

    except ImportError:
        return "Missing deps. Run: uv add pillow pytesseract && sudo apt install tesseract-ocr scrot"
    except Exception as e:
        return f"Screen read error: {e}"


@function_tool()
async def get_clipboard(context: RunContext) -> str:
    """
    Read the current clipboard contents.
    Useful to grab selected text, URLs, or copied content.
    """
    content = _clip_paste()
    if not content:
        return "Clipboard is empty."
    if len(content) > 500:
        return f"Clipboard (truncated): {content[:500]}..."
    return f"Clipboard contents: {content}"


@function_tool()
async def select_all_and_copy(context: RunContext) -> str:
    """
    Press Ctrl+A to select all, then Ctrl+C to copy.
    Returns the copied text. Great for reading message counts or full text field content.
    """
    _xdo("key", "ctrl+a")
    time.sleep(0.1)
    _xdo("key", "ctrl+c")
    time.sleep(0.15)
    content = _clip_paste()
    if not content:
        return "Nothing was copied (selection may be empty)."
    if len(content) > 600:
        return f"Copied text (truncated): {content[:600]}..."
    return f"Copied text: {content}"


# ─────────────────────────────────────────────
# SYSTEM TOOLS
# ─────────────────────────────────────────────

@function_tool()
async def run_command_silent(context: RunContext, command: str) -> str:
    """
    Run a shell command instantly and return its output.
    No user confirmation needed — executes immediately.
    Keep commands safe and non-destructive (reads, status checks, etc).

    Args:
        command: Shell command to run (e.g. 'ls ~/Downloads', 'whoami', 'date').
    """
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=8
        )
        output = result.stdout.strip() or result.stderr.strip() or "(no output)"
        if len(output) > 600:
            output = output[:600] + "... [truncated]"
        return f"Command output: {output}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 8 seconds."
    except Exception as e:
        return f"Error: {e}"


@function_tool()
async def get_screen_size(context: RunContext) -> str:
    """
    Get the current screen resolution.
    Useful before clicking or moving mouse to specific positions.
    """
    r = subprocess.run(
        ["xdotool", "getdisplaygeometry"],
        capture_output=True, text=True
    )
    w, h = r.stdout.strip().split()
    return f"Screen size: {w}x{h} pixels"


@function_tool()
async def get_mouse_position(context: RunContext) -> str:
    """
    Get the current mouse cursor position on screen.
    """
    r = _xdo("getmouselocation", "--shell")
    lines = dict(line.split("=") for line in r.stdout.strip().split("\n") if "=" in line)
    x, y = lines.get("X", "?"), lines.get("Y", "?")
    return f"Mouse is at ({x}, {y})"