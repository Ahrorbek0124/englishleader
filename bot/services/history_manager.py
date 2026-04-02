"""
history_manager.py
Stores per-user translation history as JSON files.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

MAX_HISTORY = 20
HISTORY_DIR = Path(__file__).parent / "history"


class HistoryManager:
    def __init__(self) -> None:
        HISTORY_DIR.mkdir(exist_ok=True)

    def _history_file(self, chat_id: int) -> Path:
        return HISTORY_DIR / f"history_{chat_id}.json"

    def _load(self, chat_id: int) -> List[Dict[str, Any]]:
        f = self._history_file(chat_id)
        if not f.exists():
            return []
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, chat_id: int, entries: List[Dict[str, Any]]) -> None:
        self._history_file(chat_id).write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_entry(self, chat_id: int, source_text: str, result_text: str, mode: str = "text") -> None:
        """Save a translation entry for the user."""
        entries = self._load(chat_id)
        now_utc = datetime.now(timezone.utc)
        entries.append(
            {
                "time_utc": now_utc.isoformat(timespec="minutes"),
                "mode": mode,
                "source": source_text[:300],
                "result": result_text[:300],
            }
        )
        # Keep only the last MAX_HISTORY entries
        entries = entries[-MAX_HISTORY:]
        self._save(chat_id, entries)

    def get_history(self, chat_id: int) -> str:
        """Return formatted history string for display in Telegram."""
        entries = self._load(chat_id)
        if not entries:
            return "📭 Tarjima tarixi bo'sh."

        lines = ["📜 *So'nggi tarjimalar:*\n"]
        for i, e in enumerate(reversed(entries), start=1):
            mode_icon = {"text": "📝", "voice": "🎤", "file": "📁", "photo": "📷"}.get(e.get("mode", "text"), "📝")

            time_label = self._format_time_label(e)
            lines.append(
                f"{i}. {mode_icon} `{time_label}`\n"
                f"   ➤ {e['source'][:80]}\n"
                f"   ✅ {e['result'][:80]}\n"
            )
            if i >= 10:
                remaining = len(entries) - 10
                if remaining > 0:
                    lines.append(f"... va yana {remaining} ta tarjima.")
                break
        return "\n".join(lines)

    @staticmethod
    def _format_time_label(entry: Dict[str, Any]) -> str:
        raw = entry.get("time_utc") or entry.get("time")
        if not raw:
            return "?"

        dt: datetime
        # New format: ISO UTC
        if isinstance(raw, str) and "T" in raw:
            try:
                dt = datetime.fromisoformat(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                return str(raw)
        else:
            # Old format: naive local time string
            try:
                dt = datetime.strptime(str(raw), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except Exception:
                return str(raw)

        if ZoneInfo is None:
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        try:
            us = dt.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M %p")
            uz = dt.astimezone(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d %H:%M")
            return f"US: {us} | UZ: {uz}"
        except Exception:
            return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def clear_history(self, chat_id: int) -> None:
        """Clear all history for the user."""
        f = self._history_file(chat_id)
        if f.exists():
            f.unlink()
