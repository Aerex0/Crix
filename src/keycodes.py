"""
Linux input-event-codes mapping for ydotool.
Source: /usr/include/linux/input-event-codes.h

ydotool uses raw Linux keycodes, not X11 keysyms.
Format for ydotool key command: <keycode>:<pressed>
  - :1 = key down
  - :0 = key up

Example: Ctrl+C = "29:1 46:1 46:0 29:0"
  - Press Ctrl (29:1)
  - Press C (46:1)
  - Release C (46:0)
  - Release Ctrl (29:0)
"""

# Mapping from friendly names to Linux input-event-codes
KEYCODES: dict[str, int] = {
    # ─────────────────────────────────────────────
    # Letters (lowercase)
    # ─────────────────────────────────────────────
    "a": 30,
    "b": 48,
    "c": 46,
    "d": 32,
    "e": 18,
    "f": 33,
    "g": 34,
    "h": 35,
    "i": 23,
    "j": 36,
    "k": 37,
    "l": 38,
    "m": 50,
    "n": 49,
    "o": 24,
    "p": 25,
    "q": 16,
    "r": 19,
    "s": 31,
    "t": 20,
    "u": 22,
    "v": 47,
    "w": 17,
    "x": 45,
    "y": 21,
    "z": 44,
    # ─────────────────────────────────────────────
    # Numbers (top row)
    # ─────────────────────────────────────────────
    "1": 2,
    "2": 3,
    "3": 4,
    "4": 5,
    "5": 6,
    "6": 7,
    "7": 8,
    "8": 9,
    "9": 10,
    "0": 11,
    # ─────────────────────────────────────────────
    # Modifiers
    # ─────────────────────────────────────────────
    "ctrl": 29,
    "control": 29,
    "leftctrl": 29,
    "rightctrl": 97,
    "shift": 42,
    "leftshift": 42,
    "rightshift": 54,
    "alt": 56,
    "leftalt": 56,
    "rightalt": 100,
    "super": 125,
    "meta": 125,
    "win": 125,
    "leftmeta": 125,
    "rightmeta": 126,
    # ─────────────────────────────────────────────
    # Special Keys
    # ─────────────────────────────────────────────
    "return": 28,
    "enter": 28,
    "escape": 1,
    "esc": 1,
    "backspace": 14,
    "tab": 15,
    "space": 57,
    "minus": 12,
    "-": 12,
    "equal": 13,
    "=": 13,
    "leftbrace": 26,
    "[": 26,
    "rightbrace": 27,
    "]": 27,
    "semicolon": 39,
    ";": 39,
    "apostrophe": 40,
    "'": 40,
    "grave": 41,
    "`": 41,
    "backslash": 43,
    "\\": 43,
    "comma": 51,
    ",": 51,
    "dot": 52,
    ".": 52,
    "slash": 53,
    "/": 53,
    # ─────────────────────────────────────────────
    # Function Keys
    # ─────────────────────────────────────────────
    "f1": 59,
    "f2": 60,
    "f3": 61,
    "f4": 62,
    "f5": 63,
    "f6": 64,
    "f7": 65,
    "f8": 66,
    "f9": 67,
    "f10": 68,
    "f11": 87,
    "f12": 88,
    # ─────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────
    "up": 103,
    "down": 108,
    "left": 105,
    "right": 106,
    "home": 102,
    "end": 107,
    "pageup": 104,
    "pgup": 104,
    "pagedown": 109,
    "pgdn": 109,
    "insert": 110,
    "ins": 110,
    "delete": 111,
    "del": 111,
    # ─────────────────────────────────────────────
    # Locks
    # ─────────────────────────────────────────────
    "capslock": 58,
    "caps": 58,
    "numlock": 69,
    "scrolllock": 70,
    # ─────────────────────────────────────────────
    # Misc
    # ─────────────────────────────────────────────
    "sysrq": 99,
    "print": 99,
    "printscreen": 99,
    "pause": 119,
    "menu": 127,
    # ─────────────────────────────────────────────
    # Numpad
    # ─────────────────────────────────────────────
    "kp0": 82,
    "kp1": 79,
    "kp2": 80,
    "kp3": 81,
    "kp4": 75,
    "kp5": 76,
    "kp6": 77,
    "kp7": 71,
    "kp8": 72,
    "kp9": 73,
    "kpminus": 74,
    "kpplus": 78,
    "kpasterisk": 55,
    "kpmultiply": 55,
    "kpslash": 98,
    "kpdivide": 98,
    "kpenter": 96,
    "kpdot": 83,
    # ─────────────────────────────────────────────
    # Media Keys
    # ─────────────────────────────────────────────
    "mute": 113,
    "volumedown": 114,
    "volumeup": 115,
    "playpause": 164,
    "stopcd": 166,
    "previoussong": 165,
    "nextsong": 163,
}


def parse_key_combo(combo: str) -> list[tuple[int, int]]:
    """
    Parse a key combo like 'ctrl+c' into ydotool key sequence.

    Args:
        combo: Key combination string (e.g., 'ctrl+c', 'super+1', 'alt+Tab')

    Returns:
        List of (keycode, pressed) tuples for ydotool.

    Example:
        'ctrl+c' -> [(29, 1), (46, 1), (46, 0), (29, 0)]

    Raises:
        ValueError: If any key in the combo is not recognized.
    """
    keys = [k.strip().lower() for k in combo.split("+")]
    codes: list[int] = []

    for key in keys:
        code = KEYCODES.get(key)
        if code is None:
            raise ValueError(
                f"Unknown key: '{key}'. Available keys: {', '.join(sorted(KEYCODES.keys()))}"
            )
        codes.append(code)

    # Build sequence: press all keys, then release in reverse order
    sequence: list[tuple[int, int]] = []

    # Press all keys (in order)
    for code in codes:
        sequence.append((code, 1))  # key down

    # Release all keys (in reverse order)
    for code in reversed(codes):
        sequence.append((code, 0))  # key up

    return sequence


def format_for_ydotool(sequence: list[tuple[int, int]]) -> list[str]:
    """
    Format key sequence as arguments for ydotool key command.

    Args:
        sequence: List of (keycode, pressed) tuples

    Returns:
        List of strings like ['29:1', '46:1', '46:0', '29:0']
    """
    return [f"{code}:{pressed}" for code, pressed in sequence]


def key_combo_to_ydotool_args(combo: str) -> list[str]:
    """
    Convert a key combo string directly to ydotool arguments.

    Args:
        combo: Key combination string (e.g., 'ctrl+c')

    Returns:
        List of ydotool key arguments

    Example:
        'ctrl+c' -> ['29:1', '46:1', '46:0', '29:0']
    """
    sequence = parse_key_combo(combo)
    return format_for_ydotool(sequence)
