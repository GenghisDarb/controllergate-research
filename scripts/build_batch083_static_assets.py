from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEAD = "3b8f66c8ab7f51ea268293c71bf9815a3f17071c"


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hashed(value: dict[str, object], key: str) -> dict[str, object]:
    value[key] = hashlib.sha256(canonical(value).encode()).hexdigest(); return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    historical = [json.loads(line) for line in (ROOT / "configs/historical_requirement_registry_v1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    loose = []
    mapping = {"IMPLEMENTED_ENFORCED": "IMPLEMENTED_HISTORICAL_REPLAY", "ALREADY_IMPLEMENTED_ENFORCED": "IMPLEMENTED_HISTORICAL_REPLAY",
               "DEFERRED_NAMED_BATCH": "DEFERRED_NAMED_BATCH"}
    for row in historical:
        value = {"requirement_id": row["requirement_id"], "category": "historical_engineering_law", "name": row["name"],
                 "historical_origin": row["historical_origin"], "current_evidence": row.get("required_evidence", []),
                 "actual_evidence_depth": "historical proof boundary retained; Batch083 raw-evidence promotion is separately adjudicated",
                 "status": mapping[row["status"]], "owner_module": row["owner_module"], "enforcer": row["enforcement_module"],
                 "acceptance_tests": row["acceptance_tests"], "required_artifacts": row.get("required_evidence", []),
                 "current_blocker": row.get("exact_blocker"), "risk_if_ignored": row["risk_if_missing"],
                 "next_legal_action": row["next_action"], "reopen_condition": row["reopen_condition"],
                 "claim_boundary": row["claim_boundary_effect"], "product_dependency": row["requirement_id"] in {"CG-LAW-001","CG-LAW-002","CG-LAW-003","CG-LAW-004","CG-LAW-011","CG-LAW-016","CG-LAW-017","CG-LAW-021","CG-LAW-023","CG-LAW-032","CG-LAW-033","CG-LAW-040"},
                 "last_verified_head": HEAD}
        loose.append(hashed(value, "record_hash"))
    additions = [
        ("CG-GAP-001","reaction_execution","reaction-complete execution","controllergate.reactions.event","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-002","deployment","historical canary execution","controllergate.deployment.canary_slot","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-003","deployment","health monitoring","controllergate.deployment.health_monitor","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-004","deployment","automatic rollback drill","controllergate.deployment.rollback_controller","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-005","connectivity","read-only connector framework","controllergate.connectors.read_only","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-006","connectivity","write-capable connector","controllergate.connectors.read_only","BLOCKED_EXACT"),
        ("CG-GAP-007","product","canonical product engine","controllergate.engine","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-008","product","controlled Product Alpha cycle","controllergate.product.cycle","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-009","diagnosis","historical AMDS blind challenge","controllergate.amds.historical_challenge","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-010","memory","routing-memory counterfactual","controllergate.amds.historical_challenge","IMPLEMENTED_FIXTURE_ONLY"),
        ("CG-GAP-011","provider","OpenBB provider transitive closure","controllergate.runtime.provider_resolver_v4","BLOCKED_EXACT"),
        ("CG-GAP-012","provider","Poetry process-level isolation","controllergate.runtime.windows_process_egress_guard","BLOCKED_EXACT"),
        ("CG-GAP-013","operation","autonomous self-maintaining operation","controllergate.engine","BLOCKED_EXACT"),
    ]
    acceptance = {
        "CG-GAP-001": ["tests/core/test_batch083_reaction_core.py"],
        "CG-GAP-002": ["tests/core/test_batch083_deployment_connectors.py"],
        "CG-GAP-003": ["tests/core/test_batch083_deployment_connectors.py"],
        "CG-GAP-004": ["tests/core/test_batch083_deployment_connectors.py"],
        "CG-GAP-005": ["tests/core/test_batch083_deployment_connectors.py"],
        "CG-GAP-006": ["tests/core/test_batch083_deployment_connectors.py"],
        "CG-GAP-007": ["tests/core/test_batch083_product_governance_amds.py"],
        "CG-GAP-008": ["tests/core/test_batch083_product_governance_amds.py"],
        "CG-GAP-009": ["tests/core/test_batch083_product_governance_amds.py"],
        "CG-GAP-010": ["tests/core/test_batch083_product_governance_amds.py"],
        "CG-GAP-011": ["tests/runtime/test_batch083_provider_openapi_network.py"],
        "CG-GAP-012": ["tests/runtime/test_batch083_provider_openapi_network.py"],
        "CG-GAP-013": ["tests/core/test_batch083_product_governance_amds.py"],
    }
    artifacts = {
        "CG-GAP-001": ["batch083_reaction_ledger.jsonl"],
        "CG-GAP-002": ["batch083_historical_canary_health_rollback.json"],
        "CG-GAP-003": ["batch083_historical_canary_health_rollback.json"],
        "CG-GAP-004": ["batch083_historical_canary_health_rollback.json"],
        "CG-GAP-005": ["batch083_public_readonly_connector_pilot.json"],
        "CG-GAP-006": ["batch083_public_readonly_connector_pilot.json"],
        "CG-GAP-007": ["batch083_product_alpha_cycle.json"],
        "CG-GAP-008": ["batch083_product_alpha_cycle.json"],
        "CG-GAP-009": ["batch083_historical_amds_blind_challenge.json"],
        "CG-GAP-010": ["batch083_routing_memory_counterfactual.json"],
        "CG-GAP-011": ["batch083_openbb_provider_v4_result.json"],
        "CG-GAP-012": ["batch083_poetry_duplicate_reproduction.json"],
        "CG-GAP-013": ["batch083_product_alpha_cycle.json"],
    }
    gaps = []
    for rid, category, name, owner, status in additions:
        blocked = status == "BLOCKED_EXACT"
        value = {"requirement_id": rid, "category": category, "name": name, "historical_origin": "Batch082 depth reconciliation and Batch083 Product Alpha contract",
                 "current_evidence": [owner], "actual_evidence_depth": status, "status": status, "owner_module": owner,
                 "enforcer": "scripts.audit_batch083_reaction_product_cross_area_wave1g", "acceptance_tests": acceptance[rid],
                 "required_artifacts": artifacts[rid],
                 "current_blocker": ("capability remains deliberately inactive or lacks execution closure" if blocked else None),
                 "risk_if_ignored": "A maturity or product claim could exceed direct execution evidence.",
                 "next_legal_action": "supply exact missing identity and execute the named verifier" if blocked else "retain regression execution",
                 "reopen_condition": "new independently verified execution evidence" if blocked else "negative regression or verifier failure",
                 "claim_boundary": "No production readiness, write authority, full scoring, or self-maintaining claim.",
                 "product_dependency": True, "last_verified_head": HEAD}
        gaps.append(hashed(value, "record_hash"))
    for path, records in [(ROOT / "configs/controllergate_loose_end_registry_v2.jsonl", loose + gaps),
                          (ROOT / "configs/controllergate_product_gap_registry_v1.jsonl", gaps)]:
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8", newline="\n")
    v2 = json.loads((ROOT / "configs/controllergate_engineering_constitution_v2.json").read_text(encoding="utf-8"))
    laws = []
    for law in v2["laws"]:
        item = {**law, "enforcement_callable": "controllergate.governance.law_runtime_adjudicator:adjudicate",
                "proof_artifact": f"batch083_constitution_v3_law_proofs/{law['requirement_id']}.json",
                "required_proof_bindings": ["execution_record_ids","raw_log_hashes","output_hashes","verifier_record","ci_job_identity"],
                "boolean_evidence_forbidden": True}
        item["definition_hash"] = hashlib.sha256(canonical({k:v for k,v in item.items() if k != "definition_hash"}).encode()).hexdigest(); laws.append(item)
    write_json(ROOT / "configs/controllergate_engineering_constitution_v3.json", {"constitution_version": 3, "law_count": len(laws),
               "raw_evidence_required": True, "allowed_evidence_states": ["STATIC_ENFORCEMENT_VERIFIED","CONTROLLED_FIXTURE_EXERCISED_PASS","HISTORICAL_REAL_REPLAY_PASS","PROSPECTIVE_EXERCISED_PASS","RUNTIME_EXERCISED_BLOCK","PRESERVED_HISTORICAL_PASS","NOT_EXERCISED","DEFERRED_NAMED_BATCH"], "laws": laws})
    dimensions = ["artifact custody","runtime-root governance","intake","provider reconstruction","target/reproducer authority","reaction-complete pathway","AMDS diagnosis","routing-memory retrieval","routing-memory diagnostic utility","repair generation","validation and duplicate replay","canary deployment","health monitoring","automatic rollback","connector framework","read-only live connector","write-capable live connector","canonical product engine","controlled Product Alpha","autonomous self-maintaining operation","public usability"]
    write_json(ROOT / "configs/controllergate_capability_maturity_model_v1.json", {"version": 1, "levels": ["LEVEL_0_ABSENT","LEVEL_1_SCHEMA_ONLY","LEVEL_2_CONTROLLED_FIXTURE_VALIDATED","LEVEL_3_HISTORICAL_REAL_REPLAY","LEVEL_4_PROSPECTIVE_CONTROLLED_PILOT","LEVEL_5_BOUNDED_LIVE_OPERATION"], "dimensions": dimensions,
               "promotion_requires": ["evidence_ids","execution_record_ids","log_hashes","independent_verifier","limitations","next_promotion_requirement"], "stagnant_dimensions_must_be_reported": True})
    lines = ["# ControllerGate loose-end status", "", f"The permanent registry contains {len(loose)+len(gaps)} requirements; {len(gaps)} are explicit product gaps.", "", "Every requirement has an owner, executable enforcer, acceptance test, reopen condition, claim boundary, and evidence depth. Blocked capabilities remain visible. Canary deployment, health monitoring, rollback, live connectivity, and autonomous operation cannot disappear from maturity reporting.", "", "Write-capable connectors and autonomous self-maintaining operation remain blocked. Full scoring remains disallowed and the current protocol remains v2.19."]
    (ROOT / "docs/CONTROLLERGATE_LOOSE_END_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__": main()
