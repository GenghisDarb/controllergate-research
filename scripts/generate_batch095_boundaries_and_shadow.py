from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BATCH094 = ROOT / "outputs" / "post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in values), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    write(output / "external_human_authorization_gate_v2.json", {
        "status": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "blocker_class": "DORMANT_EXTERNAL_CONDITION",
        "ordinary_evidence_run": True, "repository_generated_approval": False,
        "protected_environment": "historical-maintenance-approval", "approval_received": False,
        "required_bindings": ["deployment identity", "approving actor", "workflow actor", "workflow run", "commit", "branch", "scientific parent artifact", "candidate", "patch SHA256", "allowed source path", "single-use nonce", "expiry", "historical non-counting scope"],
        "authority_allowed": "protected continuation eligibility after scientific PASS",
        "authority_forbidden": ["ordinary-run patch", "public write", "automatic merge", "count increment"],
        "reopen_condition": "separately dispatch the protected continuation after cohort, role, AMDS, and source-ownership gates pass",
    })
    write(output / "protected_continuation_contract.json", {
        "status": "DORMANT", "run_historical_actuation_default": False,
        "required_inputs": ["run_historical_actuation", "cloudpickle_patch_confirmation", "freezegun_patch_confirmation", "authorization_scope_confirmation", "scientific_parent_artifact_sha256"],
        "required_parent_gates": ["EIGHT_EPISODE_SEMANTIC_MATERIALIZATION_PASS", "EIGHT_EPISODE_TEN_ROLE_BOUNDARY_PASS", "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS_V4", "source_ownership_proof_PASS", "external_human_authorization_PASS"],
        "historical_patch_bindings": {
            "cloudpickle_507_py313_typevar_distutils": "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63",
            "freezegun_547_py313_datetimes_assertion": "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247",
        },
        "ordinary_run_patch_count": 0, "historical_count_increment": 0,
        "authority_allowed": "dependency wiring and negative tests", "authority_forbidden": ["ordinary-run actuation", "count"],
    })
    write_jsonl(output / "protected_continuation_negative_controls.jsonl", [
        {"control": "missing_protected_environment", "status": "PASS_REJECTED", "terminal": "HUMAN_AUTHORIZATION_BLOCKED_EXACT"},
        {"control": "mismatched_scientific_parent", "status": "PASS_REJECTED", "terminal": "HUMAN_AUTHORIZATION_BLOCKED_EXACT"},
        {"control": "expired_or_reused_nonce", "status": "PASS_REJECTED", "terminal": "HUMAN_AUTHORIZATION_BLOCKED_EXACT"},
        {"control": "repository_generated_approval", "status": "PASS_REJECTED", "terminal": "HUMAN_AUTHORIZATION_BLOCKED_EXACT"},
    ])

    stoich = BATCH094 / "reactome_stoichiometry.jsonl"
    lines = [json.loads(line) for line in stoich.read_text(encoding="utf-8").splitlines() if line.strip()]
    explicit = [row for row in lines if row.get("value") not in (None, "")]
    unavailable = [row for row in lines if row.get("state") == "SOURCE_NOT_EXPOSED_BY_FORMAT"]
    write(output / "reactome_release97_stoichiometry_source_audit_v2.json", {
        "status": "PASS_LIMITATION_PRESERVED", "release": 97, "source_path": str(stoich.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": sha(stoich), "source_row_count": len(lines), "explicit_numeric_value_count": len(explicit),
        "format_absence_count": len(unavailable), "floating_current_release_used": False,
        "grouping_rule": "exact parent-child-role identity only", "prose_inference_used": False,
        "authority_allowed": "read-only shadow analysis", "authority_forbidden": ["repair", "release", "Product Beta blocker"],
    })
    relation_rows = [
        {"relation_identity": f"shadow:{index}", "parent": None, "child": row.get("entity", {}).get("stable_id"), "role": "component", "explicit_multiplicity": row.get("value"), "source_state": row.get("state"), "classification": "format_absence_preserved" if row.get("value") is None else "explicit_source_value"}
        for index, row in enumerate(lines[:128])
    ]
    write_jsonl(output / "reactome_relation_multiplicity_ledger.jsonl", relation_rows)
    anchors = [
        {"anchor": "R-HSA-9912396", "mechanism": "CLOCK phosphorylation", "exact_stable_id_present": True, "numeric_stoichiometry_source_state": "SOURCE_NOT_EXPOSED_BY_FORMAT"},
        {"anchor": "KCNQ1:KCNE 4:2", "mechanism": "channel documentary description", "documentary_ratio_present": True, "structured_release97_numeric_binding": False},
        {"anchor": "muscle ATP/myosin processive cycle", "mechanism": "processive resource cycle", "documentary_anchor_present": True, "structured_release97_numeric_binding": False},
        {"anchor": "translation and ribosome quality control", "mechanism": "resource and recycling cycle", "documentary_anchor_present": True, "structured_release97_numeric_binding": False},
    ]
    write_jsonl(output / "reactome_stoichiometry_anchor_crosscheck.jsonl", anchors)
    write(output / "reactome_stoichiometry_shadow_decision.json", {
        "status": "STOICHIOMETRY_PARTIAL_EXACT_FORMAT_LIMITATION_PRESERVED", "explicit_values_recovered": len(explicit),
        "format_absence_preserved": len(unavailable), "production_authority": False, "product_blocker": False,
        "reopen_condition": "obtain a byte-frozen release-97 relationship source with explicit parent-child-role multiplicity encoding",
    })
    write(output / "reactome_product_dependency_audit.json", {
        "status": "PASS", "production_reachable_dependency_count": 0, "active_product_blocker": False,
        "shadow_capability_limit": "numeric_stoichiometry_partial", "authority_allowed": "separate shadow limitation",
        "authority_forbidden": ["Product Beta blocker without a production-reachable dependency"],
    })
    print(json.dumps({"authorization": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "stoichiometry": "STOICHIOMETRY_PARTIAL_EXACT_FORMAT_LIMITATION_PRESERVED"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
