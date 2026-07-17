from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL = "v2.19"
VERSION = "0.2.0b2.dev0"


def load(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_jsonl(path: Path) -> int:
    return sum(bool(line.strip()) for line in path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workflow-run", default="local-validation")
    parser.add_argument("--workflow-head", default="local-validation")
    args = parser.parse_args()
    output = args.output; output.mkdir(parents=True, exist_ok=True)
    cohort = load(output / "historical_eight_episode_materialization_gate.json", {"status": "NOT_RUN", "materialized_count": 0, "typed_incident_pass_count": 0, "cleanup_pass_count": 0, "candidate_substitutions": 0, "future_outcome_evidence_count": 0, "patch_operation_count": 0, "historical_count_increment": 0})
    roles = load(output / "role_measurement_quality_gate_v3.json", {"status": "NOT_RUN", "execution_receipt_count": 0, "verification_receipt_count": 0, "pass_count": 0})
    amds = load(output / "amds_historical_quality_gate_v4.json", {"status": "NOT_RUN", "active_blocker": "historical_blinded_amds_not_run", "eligible_episodes": 0, "executed_episodes": 0, "rounds": 0, "probes": 0, "contradictions": 0, "backtracks": 0, "terminal_distribution": {}, "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "memory_status": "not demonstrated"})
    source = load(output / "source_ownership_requirement_coverage_v3.json", {"status": "NOT_RUN", "source_ownership_proof_count": 0, "stage_execution_receipt_count": 0, "stage_verification_receipt_count": 0})
    authorization = load(output / "external_human_authorization_gate_v2.json", {"status": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "blocker_class": "DORMANT_EXTERNAL_CONDITION"})
    critic = load(output / "internal_release_evidence_decision_v4.json", {"status": "NOT_RUN", "standalone_critic_result": "NOT_RUN", "seal_breaking_executed": 0, "seal_breaking_rejected": 0, "actual_evidence_mutations_executed": 0, "actual_evidence_mutations_rejected": 0})
    shadow = load(output / "reactome_stoichiometry_shadow_decision.json", {"status": "NOT_RUN_SHADOW"})
    product_dependency = load(output / "reactome_product_dependency_audit.json", {"status": "NOT_RUN", "active_product_blocker": False})

    active: list[dict[str, Any]] = []
    if cohort.get("status") != "EIGHT_EPISODE_SEMANTIC_MATERIALIZATION_PASS":
        active.append({"order": 1, "blocker": "eight_episode_semantic_materialization_not_complete", "class": "ACTIVE_ROOT_BLOCKER", "reopen_condition": cohort.get("reopen_condition", "rerun all eight exact candidate lanes")})
        for row in cohort.get("blocked_candidates", []):
            active.append({"order": len(active) + 1, "blocker": ",".join(row.get("blockers", [])) or "candidate_materialization_blocked", "candidate_id": row.get("candidate_id"), "class": "ACTIVE_CHILD_BLOCKER", "reopen_condition": "correct the exact provider or incident-materialization boundary without substitution"})
    elif roles.get("status") != "EIGHT_EPISODE_TEN_ROLE_BOUNDARY_PASS":
        active.append({"order": 1, "blocker": "80_role_measurements_not_complete", "class": "ACTIVE_ROOT_BLOCKER", "reopen_condition": "execute and independently verify ten roles for each frozen episode"})
    elif amds.get("status") != "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS_V4":
        active.append({"order": 1, "blocker": amds.get("active_blocker", "historical_blinded_amds_quality_not_established"), "class": "ACTIVE_ROOT_BLOCKER", "reopen_condition": amds.get("reopen_condition", "rerun canonical blinded AMDS")})
    elif source.get("status") not in {"PASS", "NOT_RUN_NO_SOURCE_TERMINAL"}:
        active.append({"order": 1, "blocker": "stage_source_ownership_not_complete", "class": "ACTIVE_ROOT_BLOCKER", "reopen_condition": "complete executed producer and independent verifier evidence for source-owned terminals"})
    else:
        active.append({"order": 1, "blocker": "PROTECTED_HISTORICAL_ACTUATION_NOT_AUTHORIZED_AFTER_SCIENTIFIC_PASS", "class": "ACTIVE_ROOT_BLOCKER", "reopen_condition": "separately authorize and dispatch the protected historical continuation"})
    dormant = [{"condition": "external_human_authorization_pending_after_AMDS_and_source_ownership", "status": authorization.get("status"), "class": "DORMANT_EXTERNAL_CONDITION"}]
    claims = ["AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED", "prospective_memory_lift_not_demonstrated", "full_scoring_not_run"]
    shadows = [{"limitation": "numeric_stoichiometry_partial", "status": shadow.get("status"), "product_dependency": product_dependency.get("active_product_blocker", False)}]
    scientific_pass = not active[0]["blocker"].startswith("eight_episode") and roles.get("status", "").endswith("PASS") and amds.get("status", "").endswith("PASS_V4")
    decision = "PRODUCT_BETA_RC_BLOCKED_EXACT"
    state = {
        "batch": "Batch095", "workflow_run": args.workflow_run, "workflow_head": args.workflow_head,
        "internal_release_decision": decision, "external_review_status": "BLOCKED_PENDING_CORRECTED_SCIENTIFIC_CLOSURE_AND_PROTECTED_CONTINUATION",
        "active_blockers": active, "dormant_external_conditions": dormant, "claim_boundaries": claims, "shadow_capability_limitations": shadows,
        "cohort": cohort, "roles": roles, "amds": amds, "source_ownership": source, "authorization": authorization,
        "standalone_critic": critic, "reactome_stoichiometry_shadow": shadow, "reactome_product_dependency": product_dependency,
        "ordinary_run_patch_count": cohort.get("patch_operation_count", 0), "historical_count_increment": 0,
        "historical_lifecycles": {"Cloudpickle": "NOT_RUN_DORMANT", "Freezegun": "NOT_RUN_DORMANT", "Audioread": "NOT_RUN_DORMANT", "HordeForge": "NOT_RUN_DORMANT"},
        "deployment": {"repaired_distribution": "NOT_RUN_DORMANT", "package_slot_switch": "NOT_RUN_DORMANT", "health_event_count": 0, "negative_canary": "NOT_RUN_DORMANT", "exact_rollback": "NOT_RUN_DORMANT", "cleanup": "NOT_RUN_DORMANT"},
        "protocol": PROTOCOL, "package_version": VERSION, "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0,
        "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "memory_status": "not demonstrated", "full_scoring": "NOT_RUN/disallowed",
        "public_writes": "inactive", "automatic_merge": "inactive", "production_readiness": False, "self_maintaining_software": "false/not demonstrated",
        "scientific_closure_pass": scientific_pass,
    }
    write(output / "public_state_generation_audit_batch095.json", {"status": "PASS", "source": "scoped current Batch095 evidence", "old_summary_as_authority": False, "active_blockers_dependency_ordered": True, "dormant_claim_shadow_separated": True})
    write(output / "public_state_sync_audit_batch095.json", {"status": "PASS", "protocol": PROTOCOL, "package_version": VERSION, "counts": {"issue_derived": 6, "native_external": 4, "historical": 0}, "release_decision": decision})
    write(output / "release_version_lineage_batch095.json", {"status": "PASS", "parent_head": "2918803db312d1999ab791d8bd7031a0399cb4f2", "workflow_head": args.workflow_head, "protocol": PROTOCOL, "package_version": VERSION, "version_bumped": False})
    write(output / "batch095_internal_release_decision.json", {"status": decision, "maximum_allowed": "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING_V5 only in a later protected continuation", "ordinary_run": True, "Product_Beta_PASS_forbidden": True, "active_blockers": active})
    write(output / "batch095_claim_boundary.json", {"status": "PASS", "protocol": PROTOCOL, "package_version": VERSION, "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0, "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "memory_lift": "not demonstrated", "full_scoring": "NOT_RUN/disallowed", "production_readiness": False, "self_maintaining_software": "false/not demonstrated"})
    write(output / "batch095_consolidated_state.json", state)
    summary = [
        "# Batch095 campaign summary", "", f"Internal decision: `{decision}`.", "",
        f"Eight-episode materialization: `{cohort.get('status')}` ({cohort.get('materialized_count', 0)}/8).",
        f"Ten-role boundary: `{roles.get('status')}` ({roles.get('pass_count', 0)}/80).",
        f"Historical blinded AMDS: `{amds.get('status')}`. Prospective effectiveness remains `NOT_ESTABLISHED`.",
        f"Standalone critic: `{critic.get('standalone_critic_result')}`.",
        "", "Active blockers are dependency ordered:",
        *[f"- `{row['blocker']}`" for row in active],
        "", "External authorization remains a dormant protected-continuation condition until scientific prerequisites pass.",
        f"Reactome stoichiometry remains a non-authorizing shadow result: `{shadow.get('status')}`.",
        "", "Protocol remains v2.19; package version remains 0.2.0b2.dev0; counts remain 6 issue-derived and 4 native external.",
        "No patch, count increment, public write, automatic merge, production-readiness claim, or self-maintaining-software claim is made.",
    ]
    (output / "campaign_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8", newline="\n")

    excluded = {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"}
    members = sorted(path for path in output.iterdir() if path.is_file() and path.name not in excluded)
    index = {"status": "PASS", "file_count": len(members), "files": [{"path": path.name, "size": path.stat().st_size, "sha256": sha(path)} for path in members]}
    write(output / "batch095_external_review_package_index.json", index)
    members = sorted(path for path in output.iterdir() if path.is_file() and path.name not in excluded)
    portable_manifest = "".join(f"{sha(path)}  {path.name}\n" for path in members)
    portable_path = output / "PORTABLE_ARTIFACT_SHA256SUMS.txt"
    portable_path.write_text(portable_manifest, encoding="utf-8", newline="\n")
    artifact_members = [*members, portable_path]
    artifact_manifest = "".join(f"{sha(path)}  {path.name}\n" for path in artifact_members)
    artifact_path = output / "ARTIFACT_SHA256SUMS.txt"
    artifact_path.write_text(artifact_manifest, encoding="utf-8", newline="\n")
    complete_members = [*artifact_members, artifact_path]
    complete_manifest = "".join(f"{sha(path)}  {path.name}\n" for path in complete_members)
    (output / "SHA256SUMS.txt").write_text(complete_manifest, encoding="utf-8", newline="\n")
    print(json.dumps({"status": decision, "active_blocker": active[0]["blocker"], "manifest_entries": len(members)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
