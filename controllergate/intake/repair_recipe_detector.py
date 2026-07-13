from __future__ import annotations

import re


PATTERNS = {
    "exact_file_and_edit": re.compile(r"(?is)(?:[\w./-]+\.py).{0,200}(?:replace|change|remove|insert|edit).{0,200}(?:with|to|into)"),
    "line_replacement": re.compile(r"(?i)(?:line\s+\d+|at\s+[\w./-]+\.py:\d+).{0,120}(?:replace|change|remove)"),
    "before_after": re.compile(r"(?is)\bbefore\s*:.*\bafter\s*:"),
    "unified_diff": re.compile(r"(?m)^(?:diff --git |@@ -\d|--- a/|\+\+\+ b/)"),
    "linked_fix_pr": re.compile(r"(?i)(?:fix(?:ed)?\s+(?:by|in)|solution\s+PR).{0,40}(?:/pull/\d+|PR\s*#\d+)"),
    "linked_fix_commit": re.compile(r"(?i)(?:fix(?:ed)?\s+(?:by|in)|solution\s+commit).{0,40}\b[0-9a-f]{7,40}\b"),
    "replacement_code": re.compile(r"(?is)(?:replace|change).{0,120}```(?:python)?\s+.+?```"),
}


def detect_repair_recipe(text: str) -> list[str]:
    return sorted(name for name, pattern in PATTERNS.items() if pattern.search(text))
