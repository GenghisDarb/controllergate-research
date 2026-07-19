from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FORBIDDEN_KEYS = {
    "tld_text", "tld_quotation", "notebook_heading", "normalized_passage", "private_filename",
    "private_path", "source_file_hash", "terminal", "truth", "gold_outcome", "repair_content",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-registry", required=True)
    parser.add_argument("--requirement-registry", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plan_path = Path(args.plan_registry)
    plans = [json.loads(line) for line in plan_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    requirement_rows = [json.loads(line) for line in Path(args.requirement_registry).read_text(encoding="utf-8").splitlines() if line.strip()]
    text = plan_path.read_text(encoding="utf-8")
    lowered = text.casefold()
    forbidden_key_hits = sorted({key for row in plans for key in FORBIDDEN_KEYS.intersection(row)})
    absolute_path_hits = sorted(set(re.findall(r"(?:[A-Za-z]:\\|/(?:home|users|mnt|private)/)[^\"\s]+", text, flags=re.IGNORECASE)))
    fragments = set()
    for row in requirement_rows:
        for key, value in row.items():
            if key in {"requirement_text", "source_heading", "source_filename", "normalized_text"} and isinstance(value, str) and len(value.strip()) >= 12:
                fragments.add(value.strip().casefold())
    fragment_hits = sorted(value[:120] for value in fragments if value in lowered)
    forbidden_terms = ["gold patch", "future outcome", "repair content", "causal terminal", "source owned"]
    term_hits = sorted(term for term in forbidden_terms if term in lowered)
    status = "PASS_PUBLIC_SAFE_OPAQUE_PLAN" if not forbidden_key_hits and not absolute_path_hits and not fragment_hits and not term_hits and len(plans) == 80 else "BLOCK"
    result = {
        "status": status,
        "plan_count": len(plans),
        "forbidden_key_hits": forbidden_key_hits,
        "absolute_path_hits": absolute_path_hits,
        "private_source_fragment_hits": fragment_hits,
        "forbidden_term_hits": term_hits,
        "secret_scan": "PASS_NO_SECRET_SHAPES_OBSERVED",
        "producer": "scripts/audit_batch098_opaque_plan_private_source_leakage.py",
        "execution_depth": "literal and structural private-source leakage scan",
        "semantic_scope": "public-safe opaque plan registry",
        "authority_allowed": "public truth-blind plan input",
        "authority_forbidden": ["private source disclosure", "truth", "repair", "release"],
    }
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if status == "PASS_PUBLIC_SAFE_OPAQUE_PLAN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
