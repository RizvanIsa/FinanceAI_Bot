from __future__ import annotations

import datetime
import os
from collections import deque
from typing import List, Optional

from app.event_log import EVENT_LOG_PATH

FEEDBACK_LOG_PATH = "logs/feedback.log"
FEEDBACK_RECENT_LINES = 40


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _tail_lines(path: str, max_lines: int) -> List[str]:
    if not os.path.exists(path):
        return []

    recent: deque[str] = deque(maxlen=max_lines)
    with open(path, encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            recent.append(line.rstrip("\n"))

    return list(recent)


def append_feedback_entry(
    user_id: int,
    username: Optional[str],
    description: str,
    include_recent_events: bool = True,
    recent_lines: int = FEEDBACK_RECENT_LINES,
) -> List[str]:
    _ensure_parent(FEEDBACK_LOG_PATH)

    entry: List[str] = []
    entry.append("=" * 60)
    entry.append(f"Timestamp: {datetime.datetime.utcnow().isoformat()}Z")
    user_label = f"{user_id}"
    if username:
        user_label += f" ({username})"
    entry.append(f"User: {user_label}")
    entry.append("Description:")
    entry.extend(line for line in description.strip().splitlines() if line)
    entry.append("")

    recent_events: List[str] = []
    if include_recent_events:
        entry.append("Recent events:")
        recent_events = _tail_lines(EVENT_LOG_PATH, recent_lines)
        if recent_events:
            entry.extend(recent_events)
        else:
            entry.append("<no event log entries yet>")
        entry.append("")

    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as feedback_log:
        feedback_log.write("\n".join(entry))
        feedback_log.write("\n")

    return recent_events
