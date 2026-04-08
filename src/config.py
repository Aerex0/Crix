"""Configuration management for Crix assistant."""

import os


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_chrome_profile() -> str:
    """Get the Chrome profile used for browser automation."""
    return os.getenv("CRIX_CHROME_PROFILE", "Default")


def list_available_chrome_profiles() -> list[str]:
    """List available Chrome profiles on the system."""
    try:
        from browser_use import Browser

        profiles = Browser.list_chrome_profiles()
        return [p["directory"] for p in profiles]
    except Exception:
        return ["Default"]


def get_memory_enabled() -> bool:
    """Whether persistent memory is enabled."""
    return _env_bool("CRIX_MEMORY_ENABLED", True)


def get_memory_file() -> str:
    """Primary long-term memory file path relative to project root."""
    return os.getenv("CRIX_MEMORY_FILE", "MEMORY.md")


def get_memory_dir() -> str:
    """Daily/session memory directory path relative to project root."""
    return os.getenv("CRIX_MEMORY_DIR", "memory")


def get_memory_max_context_chars() -> int:
    """Max memory text chars injected into startup instructions."""
    return _env_int("CRIX_MEMORY_MAX_CONTEXT_CHARS", 3500)


def get_memory_default_search_limit() -> int:
    """Default max results returned by memory_search."""
    return _env_int("CRIX_MEMORY_SEARCH_LIMIT", 5)


def get_memory_flush_enabled() -> bool:
    """Whether shutdown/session memory flush is enabled."""
    return _env_bool("CRIX_MEMORY_FLUSH_ENABLED", True)
