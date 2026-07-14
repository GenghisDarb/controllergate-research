from __future__ import annotations

import re


SECRET = re.compile(r"(?i)(token|password|secret|authorization)[=: ]+[^\s,]+")


def redact(value: str) -> tuple[str, bool]:
    clean, count = SECRET.subn(lambda m: m.group(1) + "=[REDACTED]", value)
    return clean, count > 0


def audit_events(events: list[dict[str, object]]) -> dict[str, object]:
    writes = [row for row in events if row.get("write_authority") is True]
    return {"status": "PASS" if not writes else "BLOCK", "write_authority_disabled": not writes,
            "event_count": len(events)}
