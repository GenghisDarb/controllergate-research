from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_canonical_component_uniqueness import audit as canonical_audit
from scripts.audit_current_state_view_sync import audit as state_view_audit
from scripts.audit_external_operation_boundaries import audit as operation_audit
from scripts.audit_no_batch_core_logic import audit as batch_core_audit
from scripts.audit_no_legacy_production_imports import audit as legacy_audit
from scripts.audit_no_hardcoded_production_counts import audit as count_source_audit


REQUIRED = (
    "batch084_artifact_verification.json", "batch084_amds_execution_quality_reconciliation.json",
    "batch084_openbb_result_transport_reconciliation.json", "batch084_poetry_launcher_isolation_reconciliation.json",
    "batch084_historical_canary_reconciliation.json", "batch084_product_beta_reconciliation.json",
    "batch084_maturity_reconciliation.json", "batch085_architecture_convergence.json",
    "batch085_durable_state_validation.json", "batch085_typed_reaction_kernel.json",
    "batch085_historical_provider_recovery.json", "batch085_proof_count_state.json",
    "batch085_memory_isolation.json", "batch085_amds_quality.json",
    "batch085_historical_product_beta.json", "batch085_canary_health_rollback.json",
    "batch085_controlled_self_maintenance.json", "batch085_persistent_watch_loop.json",
    "batch085_write_policy.json", "batch085_openbb_stdout_transport.json",
    "batch085_poetry_isolation.json", "batch085_current_state_sync.json",
    "batch085_package_validation.json", "batch085_product_beta_rc_decision.json",
    "batch085_claim_boundary.json", "batch085_independent_critic.json", "campaign_summary.md", "SHA256SUMS.txt",
)


def read(out: Path, name: str) -> dict[str, object]:
    return json.loads((out / name).read_text(encoding="utf-8"))


def audit(out: Path) -> dict[str, object]:
    errors = [f"missing:{name}" for name in REQUIRED if not (out / name).is_file()]
    if errors: return {"status": "FAIL", "errors": errors}
    artifact = read(out, "batch084_artifact_verification.json")
    if artifact.get("artifact_sha256") != "838d306b63530f6cbb72ca7d9c937feb4d648c8ce79a616683b77550b0dbe413" or artifact.get("status") != "PASS": errors.append("batch084_artifact_identity")
    raw = ROOT / "outputs/post_v2_37_hardening_batch084_real_amds_canary_product_beta"
    sums = {}
    for line in (raw / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip(): digest, rel = line.split(maxsplit=1); sums[rel.lstrip(" *")] = digest
    for rel, digest in sums.items():
        path = raw / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest: errors.append(f"batch084_raw_drift:{rel}")
    amds = read(out, "batch084_amds_execution_quality_reconciliation.json")
    if amds.get("safe_abstention_accuracy") != 0.0 or amds.get("wrong_authorization_rate") != 0.5 or amds.get("AMDS_REPAIR_GATING_READINESS") != "NOT_READY": errors.append("batch084_amds_reconciliation")
    openbb = read(out, "batch084_openbb_result_transport_reconciliation.json")
    if openbb.get("result_transport") != "BLOCK_PERMISSION_DENIED" or openbb.get("causal_ownership") != "INSUFFICIENT_EVIDENCE": errors.append("batch084_openbb_reconciliation")
    poetry = read(out, "batch084_poetry_launcher_isolation_reconciliation.json")
    if poetry.get("SOURCE_OWNERSHIP") != "NOT_ESTABLISHED": errors.append("batch084_poetry_reconciliation")
    for name, result in (("canonical", canonical_audit()), ("batch_core", batch_core_audit()), ("legacy", legacy_audit()), ("operations", operation_audit()), ("count_source", count_source_audit()), ("state_views", state_view_audit())):
        if result.get("status") != "PASS": errors.append(f"{name}_audit:{result.get('errors')}")
    durable = read(out, "batch085_durable_state_validation.json")
    if durable.get("status") != "PASS" or durable.get("schema_version") != 2 or durable.get("competing_worker_lease_rejected") is not True: errors.append("durable_state")
    counts = read(out, "batch085_proof_count_state.json")
    if counts.get("issue_derived") != 6 or counts.get("native_external") != 4 or counts.get("new_count_increment") != 0: errors.append("proof_counts")
    if read(out, "batch085_memory_isolation.json").get("truth_access_denied") is not True: errors.append("memory_isolation")
    quality = read(out, "batch085_amds_quality.json")
    if quality.get("quality_gate") != "FAIL" or quality.get("wrong_authorization_rate") != 0.5 or quality.get("status") != "AMDS_REMAINS_DIAGNOSTIC_ONLY": errors.append("amds_quality_overclaim")
    historical = read(out, "batch085_historical_product_beta.json")
    if historical.get("status") != "HISTORICAL_PRODUCT_BETA_BLOCKED_EXACT" or historical.get("repair_count_increment") != 0: errors.append("historical_product_beta")
    self_maintenance = read(out, "batch085_controlled_self_maintenance.json")
    if self_maintenance.get("status") != "CONTROLLED_SELF_MAINTENANCE_BETA_PASS" or self_maintenance.get("test_mutated") is not False or self_maintenance.get("count_increment") != 0: errors.append("self_maintenance")
    watch = read(out, "batch085_persistent_watch_loop.json")
    if watch.get("status") != "PASS" or watch.get("duplicates_suppressed", 0) < 1 or watch.get("public_writes") != 0: errors.append("watch_loop")
    writes = read(out, "batch085_write_policy.json")
    if writes.get("highest_demonstrated_level") != "WRITE_LEVEL_2_ISOLATED_LOCAL_WORKTREE" or writes.get("public_remote_mutation") is not False: errors.append("write_policy")
    package = read(out, "batch085_package_validation.json")
    if package.get("status") not in {"PASS", "BLOCKED_EXACT_PLATFORM_VALIDATION_PENDING"} or package.get("product_beta_version_not_applied") is not True: errors.append("package_validation")
    decision = read(out, "batch085_product_beta_rc_decision.json")
    if decision.get("status") != "PRODUCT_BETA_RC_BLOCKED_EXACT": errors.append("product_beta_rc_overclaim")
    claims = read(out, "batch085_claim_boundary.json")
    expected = {"current_protocol": "v2.19", "issue_derived_repair_count": 6, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "public_write_connectors": "inactive", "production_readiness": False, "self_maintaining_software": "false/not demonstrated"}
    if any(claims.get(key) != value for key, value in expected.items()): errors.append("claim_boundary")
    manifest = {}
    for line in (out / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip(): digest, rel = line.split(maxsplit=1); manifest[rel.lstrip(" *")] = digest
    for path in out.iterdir():
        if path.is_file() and path.name != "SHA256SUMS.txt":
            if manifest.get(path.name) != hashlib.sha256(path.read_bytes()).hexdigest(): errors.append(f"manifest:{path.name}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "required_file_count": len(REQUIRED), "scientific_result": decision.get("status"), "package_status": package.get("status")}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--out", default=str(ROOT / "outputs/post_v2_37_hardening_batch085_canonical_kernel_product_beta_rc")); args = parser.parse_args()
    result = audit(Path(args.out)); print(json.dumps(result, sort_keys=True)); return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
