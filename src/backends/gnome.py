"""
GNOME Shell backend using ydotool keypresses.

Provides GNOME desktop integration for:
- Workspace management (Super+number, Ctrl+Alt+arrows)
- Window management (Alt+Tab, Super+Tab)
- Screen information (via Mutter DisplayConfig)

Since GNOME Shell's Eval method is restricted in GNOME 49+,
this backend uses ydotool to simulate GNOME keyboard shortcuts.
"""

import subprocess
import re
import time

from keycodes import key_combo_to_ydotool_args


def _ydotool_key(combo: str) -> str:
    """
    Execute a key combination via ydotool.

    Args:
        combo: Key combination like 'super+1', 'alt+tab', 'ctrl+alt+right'

    Returns:
        Success/error message
    """
    try:
        args = key_combo_to_ydotool_args(combo)
        result = subprocess.run(
            ["ydotool", "key", *args],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return "success"
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


# ─────────────────────────────────────────────
# WORKSPACE MANAGEMENT
# ─────────────────────────────────────────────


def switch_workspace(workspace_number: int) -> str:
    """
    Switch to a workspace by number (1-4).

    Uses Super+<number> shortcut.

    Args:
        workspace_number: Workspace number (1-4)

    Returns:
        Success/error message
    """
    if workspace_number < 1 or workspace_number > 9:
        return f"Error: Workspace number must be between 1 and 9"

    combo = f"super+{workspace_number}"
    result = _ydotool_key(combo)

    if result == "success":
        return f"Switched to workspace {workspace_number}"
    return result


def switch_workspace_relative(direction: str) -> str:
    """
    Switch to adjacent workspace.

    Uses Ctrl+Alt+<arrow> shortcuts.

    Args:
        direction: 'left', 'right', 'up', or 'down'

    Returns:
        Success/error message
    """
    direction = direction.lower()
    if direction not in ("left", "right", "up", "down"):
        return f"Error: Direction must be left, right, up, or down"

    combo = f"ctrl+alt+{direction}"
    result = _ydotool_key(combo)

    if result == "success":
        return f"Switched workspace {direction}"
    return result


# ─────────────────────────────────────────────
# WINDOW MANAGEMENT
# ─────────────────────────────────────────────


def list_open_windows() -> str:
    """
    Show the window switcher (Alt+Tab) to see open windows.

    Note: This opens the visual switcher, user can then navigate.
    Release happens automatically after showing.

    Returns:
        Message about the window switcher
    """
    result = _ydotool_key("alt+tab")
    if result == "success":
        return "Opened window switcher (Alt+Tab). Press Tab to cycle, Enter to select, or Escape to cancel."
    return result


def show_app_grid() -> str:
    """
    Show the GNOME application grid.

    Uses Super+A shortcut.

    Returns:
        Success/error message
    """
    result = _ydotool_key("super+a")
    if result == "success":
        return "Opened application grid"
    return result


def show_activities() -> str:
    """
    Show GNOME Activities overview.

    Uses just the Super key (press and release).

    Returns:
        Success/error message
    """
    # Just press and release Super to toggle activities
    result = subprocess.run(
        ["ydotool", "key", "125:1", "125:0"],  # Super key
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return "Toggled Activities overview"
    return f"Error: {result.stderr.strip()}"


def focus_window(title_pattern: str) -> str:
    """
    Focus a window by opening Activities and typing to search.

    This opens Activities overview and types the search pattern.
    User can then press Enter or click to select the window.

    Args:
        title_pattern: Text to search for

    Returns:
        Success/error message
    """
    # Open Activities
    show_activities()
    time.sleep(0.3)

    # Type the search pattern
    result = subprocess.run(
        ["ydotool", "type", "--", title_pattern],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return f"Searching for '{title_pattern}' in Activities. Press Enter to select."
    return f"Error: {result.stderr.strip()}"


def close_active_window() -> str:
    """
    Close the currently focused window.

    Uses Alt+F4 shortcut.

    Returns:
        Success/error message
    """
    result = _ydotool_key("alt+f4")
    if result == "success":
        return "Closed active window"
    return result


def minimize_active_window() -> str:
    """
    Minimize the currently focused window.

    Uses Super+H shortcut.

    Returns:
        Success/error message
    """
    result = _ydotool_key("super+h")
    if result == "success":
        return "Minimized active window"
    return result


def maximize_toggle() -> str:
    """
    Toggle maximize state of the current window.

    Uses Super+Up shortcut.

    Returns:
        Success/error message
    """
    result = _ydotool_key("super+up")
    if result == "success":
        return "Toggled window maximize"
    return result


def tile_window_left() -> str:
    """
    Tile the current window to the left half of the screen.

    Uses Super+Left shortcut.

    Returns:
        Success/error message
    """
    result = _ydotool_key("super+left")
    if result == "success":
        return "Tiled window to left"
    return result


def tile_window_right() -> str:
    """
    Tile the current window to the right half of the screen.

    Uses Super+Right shortcut.

    Returns:
        Success/error message
    """
    result = _ydotool_key("super+right")
    if result == "success":
        return "Tiled window to right"
    return result


# ─────────────────────────────────────────────
# SCREEN INFORMATION
# ─────────────────────────────────────────────


def get_screen_size() -> tuple[int, int]:
    """
    Get the primary screen resolution.

    Uses Mutter's DisplayConfig interface for accurate information.

    Returns:
        Tuple of (width, height) in pixels
    """
    result = subprocess.run(
        [
            "gdbus",
            "call",
            "--session",
            "--dest",
            "org.gnome.Mutter.DisplayConfig",
            "--object-path",
            "/org/gnome/Mutter/DisplayConfig",
            "--method",
            "org.gnome.Mutter.DisplayConfig.GetCurrentState",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return 1920, 1080  # Fallback

    output = result.stdout

    # Look for the current mode (marked with 'is-current': <true>)
    # Format: '1920x1080@144.003', 1920, 1080, ... 'is-current': <true>
    match = re.search(
        r"'(\d+)x(\d+)@[\d.]+',\s*(\d+),\s*(\d+).*?'is-current': <true>", output
    )

    if match:
        width = int(match.group(3))
        height = int(match.group(4))
        return width, height

    return 1920, 1080  # Fallback


def get_screen_size_str() -> str:
    """
    Get screen size as a formatted string.

    Returns:
        String like "Screen size: 1920x1080 pixels"
    """
    width, height = get_screen_size()
    return f"Screen size: {width}x{height} pixels"


def get_monitor_count() -> int:
    """
    Get the number of connected monitors.

    Returns:
        Number of monitors (fallback: 1)
    """
    # Use xrandr as a simple fallback that works on most systems
    result = subprocess.run(
        ["xrandr", "--query"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        # Count lines containing " connected "
        connected = sum(
            1 for line in result.stdout.split("\n") if " connected " in line
        )
        return max(1, connected)

    return 1
