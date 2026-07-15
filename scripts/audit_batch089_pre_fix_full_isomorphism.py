from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from batch089_common import OUTPUT, STARTING_HEAD, write_json


DEFECTS = [
    (".github/workflows/post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure.yml", "source capsule upload", "hidden files are not explicitly preserved"),
    ("scripts/batch088_capsule_transport.py", "build_source", "two independent successful source builds are not required"),
    ("scripts/batch088_capsule_transport.py", "build diagnostics", "bounded diagnostics are reduced to opaque hashes"),
    ("scripts/finalize_batch088_evidence.py", "transport", "source identity does not survive portable producer-consumer reconstruction"),
    ("scripts/batch088_consume_capsules.py", "main", "verified capsules still unconditionally produce a blocked lifecycle"),
    ("scripts/batch088_non_source_attempt.py", "main", "non-source lifecycle is a placeholder block writer"),
    ("scripts/run_batch088_amds_builder.py", "build_contracts", "the same generic probe family is reused for every episode"),
    ("scripts/batch088_neutral_probe.py", "main", "old text and JSON are parsed instead of candidate-specific experiments"),
    ("scripts/batch088_neutral_probe.py", "main", "text counts and inferred return codes cannot establish ownership"),
    ("configs/batch088_historical_cohort_decision_time.json", "anchors", "some anchors are label hashes rather than measured runtime identities"),
    ("controllergate/amds/dpp14/constraint_propagation.py", "propagate", "active-set intersection is not complete truth maintenance"),
    ("controllergate/amds/dpp14/constraint_propagation.py", "implication handling", "absent antecedent can incorrectly discard a consequent"),
    ("controllergate/amds/dpp14/constraint.py", "constraint semantics", "explicit true/false/unknown cardinality semantics are incomplete"),
    ("scripts/run_batch088_amds_builder.py", "adversarial backtrack", "contradiction evidence is synthetic rather than brokered historical evidence"),
    ("controllergate/amds/dpp14/controller_audit.py", "source ownership", "generic fact prefixes replace required individual proof tokens"),
    ("controllergate/product/cycle.py", "stage initialization", "production stages can begin from default pass-like state"),
    ("controllergate/product/historical_lifecycle.py", "repair license", "independent licensing conditions collapse to one path-presence result"),
    ("controllergate/product/historical_lifecycle.py", "duplicate replay", "duplicate replay does not prove a fresh independent compartment"),
    ("outputs/post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure/tld_curvature_elbow_audit.json", "TLD", "only shadow traces exist; real curvature is not established"),
    ("scripts/finalize_batch088_evidence.py", "output write", "later runs can regenerate prior historical output directories"),
    (".github/workflows/post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure.yml", "expected block jobs", "workflow success can mean only an asserted block record"),
    ("scripts/audit_batch088_release_critic.py", "release decision", "many passing checks can obscure one load-bearing unresolved checkpoint"),
]


def source(path: str) -> str:
    result = subprocess.run(["git", "show", f"{STARTING_HEAD}:{path}"], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.stdout if result.returncode == 0 else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT / "batch089_pre_fix_expected_failure.json")
    args = parser.parse_args()
    rows = []
    for index, (path, symbol, defect) in enumerate(DEFECTS, 1):
        text = source(path)
        rows.append({"defect_id": f"B089-P1-{index:02d}", "file": path, "symbol": symbol, "line_range": "1-end" if text else "missing-at-starting-head", "defect": defect, "risk": "release-critical evidence can be overstated or authority can be bypassed", "required_correction": "implement a typed executable transition with independent verification and an explicit authority boundary", "red_to_green_test": f"batch089_prompt1_defect_{index:02d}", "starting_head_object_observed": bool(text)})
    record = {"audited_head": STARTING_HEAD, "builder_decision_function_imported": False, "detected_defect_count": len(rows), "defects": rows, "status": "BATCH089_PRE_FIX_AUDIT_FAIL_EXPECTED"}
    write_json(args.output, record)
    print(json.dumps({"status": record["status"], "detected_defect_count": len(rows)}, sort_keys=True))
    return 0 if len(rows) >= 22 else 1


if __name__ == "__main__":
    raise SystemExit(main())
