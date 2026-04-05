"""
Crix backends for Wayland/GNOME.

This package provides backend implementations for:
- ydotool: Input simulation (keyboard, mouse)
- gnome: GNOME Shell integration via gdbus (workspaces, windows)
- clipboard: wl-clipboard wrapper
- screenshot: grim wrapper
- legacy: xdotool fallback for unsupported features (scroll)
- browser: Web automation via browser-use
"""

from . import ydotool
from . import gnome
from . import clipboard
from . import screenshot
from . import legacy
from . import browser

__all__ = [
    "ydotool",
    "gnome",
    "clipboard",
    "screenshot",
    "legacy",
    "browser",
]
