from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = [
    ROOT / "README.md",
    ROOT / "docs" / "current_status.md",
    ROOT / "docs" / "CURRENT_FRONTIER_STATUS.md",
    ROOT / "docs" / "capability_inventory.md",
    ROOT / "docs" / "CAPABILITY_AND_CLAIM_MATRIX.md",
    ROOT / "docs" / "QUICKSTART.md",
    ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
]


def audit_texts(files: list[Path] | None = None) -> list[str]:
    failures: list[str] = []
    selected = files or PUBLIC_FILES
    texts: dict[Path, str] = {}
    for path in selected:
        if not path.is_file():
            failures.append(f"missing:{path.relative_to(ROOT)}")
            continue
        texts[path] = path.read_text(encoding="utf-8")
    joined = "\n".join(texts.values())
    required = {
        "current_protocol_v2_19": r"v2\.19 authorized_amds_active_maintenance_lane",
        "issue_count_6": r"(?:issue-derived repair(?: episode)?s?|issue-derived repairs)[^\n]{0,80}(?:`?6`?|6 confirmed)",
        "native_count_4": r"(?:native external repair(?: episode)?s?|native external repairs)[^\n]{0,80}(?:`?4`?|4 confirmed)",
        "amds_not_established": r"AMDS[^\n]{0,80}(?:NOT_ESTABLISHED|not established)",
        "memory_not_demonstrated": r"memory lift[^\n]{0,80}not demonstrated",
        "self_maintenance_not_demonstrated": r"self-maintaining software[^\n]{0,100}(?:false|not demonstrated)",
    }
    for label, pattern in required.items():
        if not re.search(pattern, joined, flags=re.IGNORECASE):
            failures.append(f"missing_public_claim:{label}")
    forbidden = {
        "stale_current_v2_14": r"(?:validated|current) protocol (?:is|:)\s*`?v2\.14\b",
        "stale_issue_count_2": r"(?:confirmed )?issue-derived repair(?: episode)?s?\s*(?:is|:|=|remain(?:s)?)?\s*`?2`?\b",
        "stale_combined_counts": r"native(?: external)?[^\n]{0,40}4[^\n]{0,80}issue[^\n]{0,40}2\b",
        "production_ready_claim": r"\b(?:is|now|declared) production[- ]ready\b",
        "generalized_memory_lift": r"\b(?:generalized|broad) memory lift (?:is )?(?:proved|demonstrated|established)\b",
    }
    for path, text in texts.items():
        try:
            display_path = path.relative_to(ROOT)
        except ValueError:
            display_path = path
        for label, pattern in forbidden.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                failures.append(f"{label}:{display_path}")
    return failures


def main() -> int:
    failures = audit_texts()
    print("Public frontier sync audit:", "PASS" if not failures else "FAIL")
    if failures:
        print("\n".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
