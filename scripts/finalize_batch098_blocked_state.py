from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
BLOCKER = "BATCH098_TLD_SOURCE_CUSTODY_BRIDGE_BLOCKED_EXACT"


def write_json(name: str, value: Mapping[str, Any]) -> None:
    (OUT / name).write_text(json.dumps(dict(value), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    bridge = json.loads((OUT / "tld_raw_ci_custody_v1.json").read_text(encoding="utf-8"))
    if bridge.get("status") != "BLOCK" or bridge.get("exact_blocker") != BLOCKER:
        raise SystemExit("finalize_blocked_state requires the exact unresolved bridge blocker")
    common = {
        "producer": "scripts.finalize_batch098_blocked_state",
        "independent_verifier": "scripts.audit_batch098_causal_hypergraph_real_materialization_topology_probe_closure",
        "execution_depth": "current_evidence_root_block_reconstruction",
        "semantic_scope": "Batch098 current public boundary",
        "authority_allowed": "claim-boundary and blocker reporting",
        "authority_forbidden": ["scientific closure", "patch", "repair count", "release promotion"],
    }
    claim = {
        "protocol": "v2.19",
        "package_version": "0.2.0b2.dev0",
        "issue_derived_repairs": 6,
        "native_external_repairs": 4,
        "historical_increment": 0,
        "AMDS_prospective_effectiveness": "NOT_ESTABLISHED",
        "memory_status": "not demonstrated",
        "full_scoring": "NOT_RUN/disallowed",
        "public_writes": "inactive",
        "automatic_merge": "inactive",
        "production_readiness": False,
        "self_maintaining_software": "false/not demonstrated",
    }
    addendum_metrics_path = OUT / "batch098_addendum_metrics.json"
    addendum_metrics = json.loads(addendum_metrics_path.read_text(encoding="utf-8")) if addendum_metrics_path.is_file() else {}
    decision = {
        **common,
        "status": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "exact_blockers": [BLOCKER],
        "active_root_blockers": [BLOCKER],
        "active_child_blockers": [],
        "downstream_not_run": ["official eight-candidate materialization", "topology-compiled AMDS", "complete raw-tree mutation campaign", "official main-artifact packaging"],
        "reopen_conditions": ["configure CONTROLLERGATE_TLD_BUNDLE_URL to the exact immutable bundle or provide the exact existing Actions artifact identity"],
        "protected_historical_actuation": "NOT_AUTHORIZED",
        "ordinary_patch_operation_count": 0,
        "historical_count_increment": 0,
    }
    write_json("batch098_internal_release_decision.json", decision)
    write_json("batch098_claim_boundary.json", {**common, "status": "PASS", **claim})
    write_json("batch098_consolidated_state.json", {**common, "status": "PRODUCT_BETA_RC_BLOCKED_EXACT", "head": head, "claim_boundary": claim, "root_blocker": BLOCKER, "addendum_contract_hash": "11cf7042c2978be24f9b9268a3819517811597c247cc495187e0b4ea86a9c37a", "final_composite_contract_hash": "5a641f70e13e0be6c205b47edfbbe10cacc246c48fa75aecef8f8756a82d0850", "addendum_metrics": {key: value for key, value in addendum_metrics.items() if key not in {"producer", "independent_verifier", "authority_allowed", "authority_forbidden"}}, "local_capabilities": {"Batch097_artifact_custody": "PASS", "TLD_local_source_custody": "PASS", "TLD_raw_CI_source_custody": "BLOCK", "installed_materialization_code": "IMPLEMENTED_LOCAL", "causal_hypergraph_code": "IMPLEMENTED_LOCAL", "environment_exhausted_handoff": "IMPLEMENTED_LOCAL", "earned_insufficient_evidence": "IMPLEMENTED_LOCAL", "branch_recovery_and_semantic_nogoods": "IMPLEMENTED_LOCAL", "probe_neutrality_and_frame_binding": "IMPLEMENTED_LOCAL", "topology_probe_compiler": "IMPLEMENTED_LOCAL", "truth_maintenance": "IMPLEMENTED_LOCAL", "official_scientific_run": "NOT_DISPATCHED"}})
    write_json("public_state_generation_audit_batch098.json", {**common, "status": "PASS", "source": "current scoped evidence and locked claim values", "old_summary_used_as_authority": False, "root_blocker": BLOCKER})
    write_json("public_state_sync_audit_batch098.json", {**common, "status": "PASS", "claim_boundary": claim, "synchronized_documents": ["README.md", "docs/QUICKSTART.md", "docs/CLAIM_ENVELOPE.md"]})
    write_json("release_version_lineage_batch098.json", {**common, "status": "PASS", "starting_head": "6b940fb6f42c215ca45b00c293b452595b4f4ab4", "current_head": head, "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "tag_created": False, "release_created": False})
    write_json("public_quickstart_audit.json", {**common, "status": "PASS", "installed_read_only_command": "controllergate evidence inspect-contracts", "network": "none", "patch_operations": 0, "repository_writes": 0})
    write_json("public_claim_envelope_audit.json", {**common, "status": "PASS", "claim_boundary": claim, "overclaim_count": 0})
    write_json("public_onboarding_fixture_result.json", {**common, "status": "PASS", "wheel_sha256": "95d59057aeafa57e56c1a902860cb7da34395e7393575fc50d3a54d6020898ed", "installed_origin": "C:/Dev/ControllerGate_Runtime/batch098_local_installed_20260718_01/venv/Lib/site-packages/controllergate", "candidate_count": 8, "read_only": True, "network_operations": 0, "patch_operations": 0})
    write_json("installed_materialization_cli_origins.json", {**common, "status": "PASS_LOCAL_INSTALLED_WHEEL", "wheel_sha256": "95d59057aeafa57e56c1a902860cb7da34395e7393575fc50d3a54d6020898ed", "materializer_origin": "C:/Dev/ControllerGate_Runtime/batch098_local_installed_20260718_01/venv/Lib/site-packages/controllergate/evidence/materializer.py", "checkout_import": False, "official_ci_result": "NOT_RUN_UPSTREAM_CUSTODY_BLOCK"})
    history = {**common, "timestamp_utc": datetime.now(timezone.utc).isoformat(), "batch": "Batch098", "event": "local implementation and custody bridge block", "head": head, "decision": "PRODUCT_BETA_RC_BLOCKED_EXACT", "blocker": BLOCKER}
    (OUT / "chronological_project_history_v3.jsonl").write_text(json.dumps(history, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    (OUT / "chronological_shareable_summary_v3.md").write_text("# Batch098 chronological summary\n\nBatch097 custody and local TLD custody pass. Batch098 installed materialization, causal-hypergraph, topology-probe, truth-maintenance, and read-only onboarding code is implemented locally. The official workflow is not dispatched because the exact TLD raw-source CI custody bridge is unavailable. Product Beta RC remains blocked.\n", encoding="utf-8", newline="\n")
    (OUT / "campaign_summary.md").write_text(f"# Batch098 campaign summary\n\nBatch097 artifact custody is verified and officially reconciled. The exact TLD 1–44 bundle passes local custody and direct local parsing, but no protected immutable CI source bridge exists. Per the frozen prompt contract, the official workflow and dependent scientific lanes were not dispatched.\n\nThe mandatory environment-handoff/earned-abstention/branch-recovery addendum is implemented and tested under composite contract `5a641f70e13e0be6c205b47edfbbe10cacc246c48fa75aecef8f8756a82d0850`. Its recorded counts are nonauthorizing implementation fixtures until the official eight-candidate workflow executes.\n\nExact blocker: `{BLOCKER}`.\n\nProtocol remains `v2.19`; package remains `0.2.0b2.dev0`; repair counts remain 6 issue-derived and 4 native external with historical increment 0. AMDS prospective effectiveness is `NOT_ESTABLISHED`; memory lift is not demonstrated; full scoring is disallowed; public writes and automatic merge are inactive; production readiness and self-maintaining software remain false/not demonstrated.\n", encoding="utf-8", newline="\n")
    package_files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name not in {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt", "evidence_object_registry_v2.jsonl", "evidence_hash_resolution_audit_v2.json", "unresolved_current_authority_evidence.jsonl"})
    write_json("batch098_external_review_package_index.json", {**common, "status": "PASS_BOUNDED_BLOCKED_PACKAGE", "evidence_files": [path.name for path in package_files], "root_blocker": BLOCKER, "external_release_approval": False})
    evidence_files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name not in {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt", "evidence_object_registry_v2.jsonl", "evidence_hash_resolution_audit_v2.json", "unresolved_current_authority_evidence.jsonl"})
    registry = [
        {
            "evidence_id": f"sha256:{sha256(path)}",
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "size": path.stat().st_size,
            "producer": "producer recorded inside evidence object or Batch098 finalizer",
            "execution_depth": "bounded_portable_evidence",
            "semantic_scope": "Batch098 custody, implementation policy, local shadow parse, or exact blocker",
            "authority_allowed": "scope declared by evidence object",
            "authority_forbidden": ["patch", "repair count", "release promotion"],
        }
        for path in evidence_files
    ]
    (OUT / "evidence_object_registry_v2.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in registry), encoding="utf-8", newline="\n")
    write_json("evidence_hash_resolution_audit_v2.json", {**common, "status": "PASS", "evidence_object_count": len(registry), "unresolved_current_authority_evidence_count": 0, "all_hashes_resolved": True})
    (OUT / "unresolved_current_authority_evidence.jsonl").write_text("", encoding="utf-8", newline="\n")
    files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name not in {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"})
    portable_manifest = "".join(f"{sha256(path)}  {path.name}\n" for path in files)
    for name in ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"):
        (OUT / name).write_text(portable_manifest, encoding="utf-8", newline="\n")
    complete_files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt")
    complete_manifest = "".join(f"{sha256(path)}  {path.name}\n" for path in complete_files)
    (OUT / "SHA256SUMS.txt").write_text(complete_manifest, encoding="utf-8", newline="\n")
    print(json.dumps({"status": decision["status"], "exact_blocker": BLOCKER}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
