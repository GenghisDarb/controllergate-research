from __future__ import annotations

import hashlib
import re
from typing import Any


HARD_PATTERNS = {
    "unified_diff": re.compile(r"(?m)^(?:diff --git |@@ -\d|--- a/|\+\+\+ b/)", re.I),
    "linked_fix_pr": re.compile(r"(?i)(?:fix(?:ed|es)?\s+(?:by|in)|resolved\s+by)\s+(?:https://github\.com/\S+/pull/\d+|#\d+)"),
    "linked_fixed_commit": re.compile(r"(?i)(?:fixed|resolved)\s+(?:by|in)\s+(?:commit\s+)?[0-9a-f]{7,40}"),
    "replacement_function": re.compile(r"(?is)(?:replace\s+(?:the\s+)?(?:function|method)|complete\s+replacement).{0,200}```python"),
    "line_by_line_edit": re.compile(r"(?i)(?:change|replace|edit)\s+line\s+\d+|on\s+line\s+\d+\s+(?:change|replace)"),
    "gold_or_future_patch": re.compile(r"(?i)gold\s+patch|future\s+test\s+(?:change|patch)|known\s+good\s+patch"),
    "explicit_test_edit_instructions": re.compile(r"(?i)(?:please\s+)?add\s+(?:\d+\s+more\s+|a\s+)?(?:regression\s+)?test(?:\s+case)?s?\b|modify\s+(?:the\s+)?tests?\b"),
    "complete_repair_instructions": re.compile(r"(?i)(?:please\s+)?(?:change|edit|replace|remove|preserve|implement)\s+(?:the\s+)?(?:function|method|module|code|architecture|metadata)\b"),
    "controllergate_output": re.compile(r"(?i)ControllerGate.{0,80}(?:patch|repair output|source-only repair)"),
}

SOFT_PATTERNS = {
    "python_reproducer": re.compile(r"```python", re.I),
    "stack_trace": re.compile(r"(?i)traceback \(most recent call last\)|\bFile \"[^\"]+\.py\", line \d+"),
    "failed_workaround": re.compile(r"(?i)workaround|tried .{0,80}(?:but|failed|does not work)"),
    "descriptive_solution_word": re.compile(r"(?i)\b(?:solution|patch)\b"),
    "pr_mention": re.compile(r"(?i)(?:pull request|\bPR\s*#|/pull/\d+)"),
}


def classify_contamination(body: str, comments: str = "") -> dict[str, Any]:
    text = body + "\n" + comments
    hard = sorted(name for name, pattern in HARD_PATTERNS.items() if pattern.search(text))
    soft = sorted(name for name, pattern in SOFT_PATTERNS.items() if pattern.search(text))
    classification = "HARD_REJECT" if hard else "SOFT_RISK" if soft else "CLEAN"
    excluded = [match.group(0) for pattern in HARD_PATTERNS.values() for match in pattern.finditer(text)]
    return {"classification": classification, "hard_contamination_hits": hard, "soft_risk_hits": soft, "excluded_text_hashes": sorted({hashlib.sha256(item.encode()).hexdigest() for item in excluded}), "broad_words_alone_hard_reject": False, "python_code_fence_alone_hard_reject": False}


def sanitize_issue_record(*, title: str, body: str, comments: str, classification: dict[str, Any]) -> dict[str, Any]:
    safe_lines: list[str] = []
    forbidden = re.compile(r"(?i)(?:fix(?:ed)?\s+(?:by|in)|replace\s+(?:the\s+)?(?:function|method)|diff --git|@@ -\d|resolved\s+by|(?:please\s+)?(?:add|change|edit|replace|remove|preserve|implement)\b)")
    relevant = re.compile(r"(?i)(?:traceback|error|exception|assert|failed|failure|regression|python\s+3\.|pytest|tests?[/\\]|test_[A-Za-z0-9_]+|expected|actual|observed|runtime|version|usage:)")
    # Code fences are not copied wholesale, but failure-bearing lines inside a
    # reproducer remain eligible.  This preserves traceback targets without
    # allowing an entire issue body or proposed implementation into execution.
    for origin, text in (("body", body), ("comment", comments)):
        in_code = False
        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if relevant.search(line) and not forbidden.search(line):
                prefix = f"[{origin}:code] " if in_code else f"[{origin}] "
                safe_lines.append(prefix + line)
    sanitized = "\n".join(safe_lines)
    independent_clean = not bool(forbidden.search(sanitized))
    return {"title": title, "failure_description": sanitized[:12000], "body_sha256": hashlib.sha256(body.encode()).hexdigest(), "comments_sha256": hashlib.sha256(comments.encode()).hexdigest(), "issue_snapshot_hash": hashlib.sha256((title + "\n" + body).encode()).hexdigest(), "comments_snapshot_hash": hashlib.sha256(comments.encode()).hexdigest(), "classification": classification["classification"], "hard_contamination_hits": classification["hard_contamination_hits"], "soft_risk_hits": classification["soft_risk_hits"], "excluded_text_hashes": classification["excluded_text_hashes"], "sanitized_fields": ["title", "failure_description"], "raw_issue_body_isolated": True, "repair_instructions_excluded": independent_clean, "independent_contamination_verifier": "PASS" if independent_clean else "BLOCK"}
