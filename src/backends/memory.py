"""File-backed memory backend for Crix."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable

from config import get_memory_dir, get_memory_file


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\b(?:api[_-]?key|token|password|secret)\b\s*[:=]\s*\S+", re.I),
    re.compile(r"\b\d{6}\b"),
]


@dataclass
class MemoryHit:
    path: str
    line: int
    text: str
    score: int


def _resolve_memory_file() -> Path:
    return PROJECT_ROOT / get_memory_file()


def _resolve_memory_dir() -> Path:
    return PROJECT_ROOT / get_memory_dir()


def _now() -> datetime:
    return datetime.now()


def _redact_sensitive(text: str) -> str:
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def _collect_terms(query: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9_\-]+", query.lower())
    return [t for t in terms if len(t) > 1]


def _iter_memory_files() -> Iterable[Path]:
    memory_file = _resolve_memory_file()
    memory_dir = _resolve_memory_dir()

    if memory_file.exists():
        yield memory_file

    if memory_dir.exists():
        for file_path in sorted(memory_dir.glob("*.md")):
            if file_path.is_file():
                yield file_path


def ensure_memory_files() -> str:
    """Create memory storage files/directories when missing."""
    memory_file = _resolve_memory_file()
    memory_dir = _resolve_memory_dir()

    memory_dir.mkdir(parents=True, exist_ok=True)
    if not memory_file.exists():
        memory_file.write_text(
            "# Crix Memory\n\n"
            "Durable facts, preferences, and decisions for assistant continuity.\n\n"
            "## Profile\n"
            "- (add stable user preferences here)\n\n"
            "## Routines\n"
            "- (add recurring workflows here)\n",
            encoding="utf-8",
        )
    return f"Memory ready: {memory_file.name} + {memory_dir.name}/"


def append_memory_entry(
    note: str,
    *,
    category: str = "general",
    source: str = "tool",
    confidence: float = 0.8,
) -> str:
    """Append a timestamped memory entry to daily memory log."""
    text = note.strip()
    if not text:
        return "No memory saved: empty note"

    ensure_memory_files()
    safe_note = _redact_sensitive(text)

    now = _now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    day_file = _resolve_memory_dir() / f"{date_str}.md"

    if not day_file.exists():
        day_file.write_text(f"# Memory Log {date_str}\n\n", encoding="utf-8")

    entry = (
        f"- [{time_str}] category={category} source={source} confidence={confidence:.2f}\n"
        f"  {safe_note}\n"
    )
    with day_file.open("a", encoding="utf-8") as f:
        f.write(entry)

    return f"Saved memory to {day_file.relative_to(PROJECT_ROOT)}"


def build_memory_context(max_chars: int = 3500) -> str:
    """Build compact memory context for startup prompt injection."""
    ensure_memory_files()
    memory_file = _resolve_memory_file()
    memory_dir = _resolve_memory_dir()

    sections: list[str] = []
    if memory_file.exists():
        sections.append(memory_file.read_text(encoding="utf-8").strip())

    daily_files = sorted(memory_dir.glob("*.md"))
    for daily in reversed(daily_files[-5:]):
        content = daily.read_text(encoding="utf-8").strip()
        if content:
            sections.append(f"## {daily.name}\n{content}")

    merged = "\n\n".join([s for s in sections if s]).strip()
    if len(merged) <= max_chars:
        return merged

    return "...\n" + merged[-max_chars:]


def memory_search(query: str, limit: int = 5) -> list[MemoryHit]:
    """Simple keyword-based memory search across memory files."""
    terms = _collect_terms(query)
    if not terms:
        return []

    hits: list[MemoryHit] = []
    for file_path in _iter_memory_files():
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        rel = str(file_path.relative_to(PROJECT_ROOT))
        for idx, line in enumerate(lines, start=1):
            lower = line.lower()
            score = sum(1 for term in terms if term in lower)
            if score <= 0:
                continue
            hits.append(
                MemoryHit(
                    path=rel,
                    line=idx,
                    text=line.strip(),
                    score=score,
                )
            )

    hits.sort(key=lambda h: (h.score, h.path, h.line), reverse=True)
    return hits[: max(1, limit)]


def memory_get(path: str, from_line: int = 1, lines: int = 20) -> str:
    """Read a focused snippet from an allowed memory file."""
    target = (PROJECT_ROOT / path).resolve()
    memory_file = _resolve_memory_file().resolve()
    memory_dir = _resolve_memory_dir().resolve()

    allowed = target == memory_file or memory_dir in target.parents
    if not allowed:
        return "Blocked: path is outside memory files"

    if not target.exists() or not target.is_file():
        return "Memory file not found"

    content = target.read_text(encoding="utf-8").splitlines()
    start = max(1, from_line)
    end = start + max(1, lines) - 1
    selected = content[start - 1 : end]
    if not selected:
        return "No content in selected range"

    rendered = "\n".join(f"{i}: {line}" for i, line in enumerate(selected, start=start))
    return rendered


def flush_session_memory(history_dict: dict) -> str:
    """Extract durable memory candidates from session history and append them."""
    items = history_dict.get("items", []) if isinstance(history_dict, dict) else []
    if not items:
        return "No session memory flushed: empty history"

    candidates: list[str] = []
    trigger_terms = {
        "prefer",
        "always",
        "never",
        "remember",
        "routine",
        "daily",
        "weekly",
        "tomorrow",
        "follow up",
        "todo",
        "deadline",
        "important",
    }

    for item in items[-30:]:
        if item.get("type") != "message":
            continue
        if item.get("role") != "user":
            continue

        raw_content = item.get("content", [])
        text_parts = [c for c in raw_content if isinstance(c, str)]
        text = " ".join(text_parts).strip()
        if not text:
            continue

        lower = text.lower()
        if any(term in lower for term in trigger_terms):
            candidates.append(text)

    if not candidates:
        return "No session memory flushed: no durable candidates"

    saved = 0
    for candidate in candidates[:8]:
        append_memory_entry(
            candidate,
            category="session",
            source="shutdown_flush",
            confidence=0.7,
        )
        saved += 1

    return f"Flushed {saved} session memory items"
