"""
Legacy xdotool backend for features not available in ydotool.

Currently only used for scroll functionality, which ydotool doesn't support.
"""

import subprocess


def _xdotool(*args: str) -> subprocess.CompletedProcess[str]:
    """Run an xdotool command."""
    return subprocess.run(["xdotool"] + list(args), capture_output=True, text=True)


def scroll(direction: str, amount: int = 3) -> str:
    """
    Scroll the mouse wheel at the current cursor position.

    Note: ydotool doesn't support scroll, so we fall back to xdotool.
    This works via XWayland on most Wayland compositors.

    Args:
        direction: 'up' or 'down'
        amount: Number of scroll ticks (default 3)

    Returns:
        Success/error message
    """
    # xdotool: button 4 = scroll up, button 5 = scroll down
    button = "4" if direction.lower() == "up" else "5"

    result = _xdotool("click", "--repeat", str(amount), "--delay", "50", button)

    if result.returncode != 0:
        return f"Error scrolling: {result.stderr.strip()}"

    return f"Scrolled {direction} by {amount}"


def scroll_at(x: int, y: int, direction: str, amount: int = 3) -> str:
    """
    Move mouse to position and scroll.

    Args:
        x: X coordinate
        y: Y coordinate
        direction: 'up' or 'down'
        amount: Number of scroll ticks

    Returns:
        Success/error message
    """
    # Move mouse first
    move_result = _xdotool("mousemove", str(x), str(y))
    if move_result.returncode != 0:
        return f"Error moving mouse: {move_result.stderr.strip()}"

    # Then scroll
    return scroll(direction, amount)
