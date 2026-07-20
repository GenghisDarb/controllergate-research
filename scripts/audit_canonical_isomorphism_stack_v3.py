"""Verify the corrected stack and reject unsafe current-authority language."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.isomorphism.canonical_stack_v3 import (
    CANONICAL_ORDER,
    REJECTED_INTERPRETATIONS,
    stack_contract,
)


OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization/canonical_isomorphism_stack_v3_audit.json"
UNSAFE_CURRENT_LANGUAGE = (
    "MCM loads over exactly fourteen nucleosomes",
    "fourteen nucleosomes equal 196 base pairs",
    "196 is a universal biological constant",
    "the six-set creates topology",
    "Reactome coverage proves causal gain",
)


def main() -> int:
    config = json.loads((ROOT / "configs/controllergate_5_14_6_196_stack_v3.json").read_text())
    targets = [ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "docs/CURRENT_CONTROLLERGATE_HANDOFF.md"]
    targets.extend((ROOT / "controllergate").rglob("*.py"))
    findings = []
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in UNSAFE_CURRENT_LANGUAGE:
            if phrase.casefold() in text.casefold():
                findings.append({"path": path.relative_to(ROOT).as_posix(), "phrase": phrase})
    checks = {
        "exact_order": config.get("order") == list(CANONICAL_ORDER),
        "contract": config == stack_contract(),
        "rejected_interpretations": config.get("rejected_interpretations") == list(REJECTED_INTERPRETATIONS),
        "unsafe_current_language_absent": not findings,
    }
    result = {"status": "PASS" if all(checks.values()) else "BLOCK", "checks": checks, "findings": findings}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
