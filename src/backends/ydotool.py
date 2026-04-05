"""
ydotool backend for Wayland input simulation.

ydotool works at the kernel level (/dev/uinput), making it compositor-agnostic.
Requires ydotoold daemon to be running.

Usage:
    sudo systemctl enable --now ydotoold
    # or
    systemctl --user enable --now ydotoold
"""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from keycodes import key_combo_to_ydotool_args


def _ydotool(*args: str) -> subprocess.CompletedProcess[str]:
    """
    Run a ydotool command.

    Args:
        *args: Arguments to pass to ydotool

    Returns:
        CompletedProcess with stdout/stderr
    """
    return subprocess.run(["ydotool"] + list(args), capture_output=True, text=True)


def type_text(text: str, delay_ms: int = 12) -> str:
    """
    Type text as if using a keyboard.

    Args:
        text: The text to type
        delay_ms: Delay between key events in milliseconds

    Returns:
        Success/error message
    """
    result = _ydotool("type", "--key-delay", str(delay_ms), "--", text)
    if result.returncode != 0:
        return f"Error typing: {result.stderr.strip()}"
    return f"Typed: {text!r}"


def press_key(combo: str) -> str:
    """
    Press a key or key combination.

    Args:
        combo: Key combination (e.g., 'ctrl+c', 'super+1', 'Return', 'alt+Tab')

    Returns:
        Success/error message

    Examples:
        press_key('ctrl+c')      # Copy
        press_key('ctrl+v')      # Paste
        press_key('super+1')     # Switch to workspace 1 (via keybind)
        press_key('alt+f4')      # Close window
        press_key('Return')      # Press Enter
        press_key('escape')      # Press Escape
    """
    try:
        args = key_combo_to_ydotool_args(combo)
        result = _ydotool("key", *args)
        if result.returncode != 0:
            return f"Error pressing key: {result.stderr.strip()}"
        return f"Pressed: {combo}"
    except ValueError as e:
        return f"Error: {e}"


def move_mouse(x: int, y: int, absolute: bool = True) -> str:
    """
    Move the mouse cursor.

    Args:
        x: X coordinate (pixels from left)
        y: Y coordinate (pixels from top)
        absolute: If True, move to absolute position; if False, move relative

    Returns:
        Success/error message
    """
    args = ["mousemove"]
    if absolute:
        args.append("--absolute")
    args.extend([str(x), str(y)])

    result = _ydotool(*args)
    if result.returncode != 0:
        return f"Error moving mouse: {result.stderr.strip()}"

    mode = "absolute" if absolute else "relative"
    return f"Mouse moved to ({x}, {y}) [{mode}]"


def click(x: int, y: int, button: int = 1) -> str:
    """
    Move mouse to coordinates and click.

    Args:
        x: X coordinate
        y: Y coordinate
        button: 1=left, 2=middle, 3=right

    Returns:
        Success/error message

    Note:
        ydotool click uses hex codes:
        - 0x00 = LEFT button
        - 0x01 = RIGHT button
        - 0x02 = MIDDLE button
        - 0x40 = Mouse down
        - 0x80 = Mouse up
        - 0xC0 = Click (down + up) for LEFT
        - 0xC1 = Click for RIGHT
        - 0xC2 = Click for MIDDLE
    """
    # Move to position first
    move_result = move_mouse(x, y, absolute=True)
    if "Error" in move_result:
        return move_result

    # Map button number to ydotool hex code
    button_map = {
        1: "0xC0",  # Left click (down + up + left)
        2: "0xC2",  # Middle click
        3: "0xC1",  # Right click
    }
    btn_code = button_map.get(button, "0xC0")

    result = _ydotool("click", btn_code)
    if result.returncode != 0:
        return f"Error clicking: {result.stderr.strip()}"

    btn_name = {1: "Left", 2: "Middle", 3: "Right"}.get(button, str(button))
    return f"{btn_name} clicked at ({x}, {y})"


def double_click(x: int, y: int) -> str:
    """
    Double-click at coordinates.

    Args:
        x: X coordinate
        y: Y coordinate

    Returns:
        Success/error message
    """
    # Move to position first
    move_result = move_mouse(x, y, absolute=True)
    if "Error" in move_result:
        return move_result

    # Double click with delay between clicks
    result = _ydotool("click", "--repeat", "2", "--next-delay", "100", "0xC0")
    if result.returncode != 0:
        return f"Error double-clicking: {result.stderr.strip()}"

    return f"Double-clicked at ({x}, {y})"


def mouse_down(button: int = 1) -> str:
    """
    Press and hold a mouse button.

    Args:
        button: 1=left, 2=middle, 3=right
    """
    # 0x40 = mouse down, add button offset
    btn_code = hex(0x40 + (button - 1))
    result = _ydotool("click", btn_code)
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return f"Mouse button {button} down"


def mouse_up(button: int = 1) -> str:
    """
    Release a mouse button.

    Args:
        button: 1=left, 2=middle, 3=right
    """
    # 0x80 = mouse up, add button offset
    btn_code = hex(0x80 + (button - 1))
    result = _ydotool("click", btn_code)
    if result.returncode != 0:
        return f"Error: {result.stderr.strip()}"
    return f"Mouse button {button} up"
