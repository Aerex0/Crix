"""
Clipboard backend using wl-clipboard for Wayland.
"""

import subprocess


def copy(text: str) -> bool:
    """
    Copy text to the clipboard.

    Args:
        text: Text to copy

    Returns:
        True if successful, False otherwise
    """
    result = subprocess.run(
        ["wl-copy", "--"], input=text, text=True, capture_output=True
    )
    return result.returncode == 0


def paste() -> str:
    """
    Get the current clipboard contents.

    Returns:
        Clipboard text, or empty string if clipboard is empty or error
    """
    result = subprocess.run(
        ["wl-paste", "--no-newline"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout
    return ""


def paste_primary() -> str:
    """
    Get the primary selection (middle-click paste) contents.

    Returns:
        Primary selection text, or empty string
    """
    result = subprocess.run(
        ["wl-paste", "--no-newline", "--primary"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout
    return ""


def copy_primary(text: str) -> bool:
    """
    Copy text to the primary selection.

    Args:
        text: Text to copy

    Returns:
        True if successful
    """
    result = subprocess.run(
        ["wl-copy", "--primary", "--"], input=text, text=True, capture_output=True
    )
    return result.returncode == 0


def clear() -> bool:
    """
    Clear the clipboard.

    Returns:
        True if successful
    """
    result = subprocess.run(["wl-copy", "--clear"], capture_output=True)
    return result.returncode == 0


def get_mime_types() -> list[str]:
    """
    Get the MIME types available in the clipboard.

    Returns:
        List of MIME type strings
    """
    result = subprocess.run(
        ["wl-paste", "--list-types"], capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip().split("\n")
    return []
