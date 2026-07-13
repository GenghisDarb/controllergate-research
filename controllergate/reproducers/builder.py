from __future__ import annotations

from pathlib import Path
from typing import Any

from controllergate.core.evidence import sha256_file


def build_reproducer(*, issue_lines: list[str], destination: Path, candidate_source: Path, forbidden_fragments: list[str]) -> dict[str, Any]:
    text = "\n".join(issue_lines).rstrip() + "\n"
    if any(fragment.lower() in text.lower() for fragment in forbidden_fragments):
        return {"status": "BLOCK", "exact_blocker": "reproducer_contamination_detected"}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="\n")
    outside = candidate_source.resolve() not in destination.resolve().parents
    return {"status": "PASS" if outside else "BLOCK", "path": str(destination), "sha256": sha256_file(destination), "outside_candidate_source": outside, "issue_line_count": len(issue_lines)}
