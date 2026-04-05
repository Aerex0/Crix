"""
Configuration management for Crix assistant.
"""

import os


def get_chrome_profile() -> str:
    """
    Get the Chrome profile to use for browser automation.
    Can be overridden via CRIX_CHROME_PROFILE env var.

    Returns:
        Chrome profile directory name (e.g., "Default", "Profile 1")
    """
    return os.getenv("CRIX_CHROME_PROFILE", "Default")


def list_available_chrome_profiles() -> list[str]:
    """
    List available Chrome profiles on the system.
    Useful for debugging or profile selection.

    Returns:
        List of profile directory names
    """
    try:
        from browser_use import Browser

        profiles = Browser.list_chrome_profiles()
        return [p["directory"] for p in profiles]
    except Exception:
        return ["Default"]
