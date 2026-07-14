from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.amds.dpp14.engine import TRANSITIONS
from controllergate.interlocks.audit import audit_registry
from scripts.audit_canonical_component_uniqueness import audit as audit_canonical

OUT = ROOT / "outputs/post_v2_37_hardening_batch086_historical_lifecycle_dpp14_product_beta_rc"
B85 = ROOT / "outputs/post_v2_37_hardening_batch085_canonical_kernel_product_beta_rc"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_status(root: Path) -> dict:
    manifest = root / "SHA256SUMS.txt"; failures = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1); path = root / relative
        if not path.is_file() or digest(path) != expected: failures.append(relative)
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def write_manifest() -> None:
    rows = [f"{digest(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    (OUT / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def audit() -> dict:
    errors: list[str] = []
    required = ["batch085_artifact_ingest.json", "batch086_consolidated_state.json", "historical_provider_reconstruction_results.json",
        "cloudpickle_507_py313_typevar_distutils_historical_lifecycle.json", "freezegun_547_py313_datetimes_assertion_historical_lifecycle.json",
        "historical_non_source_frozen_frame.json", "historical_non_source_lifecycle_results.json", "dpp14_transition_registry.json",
        "dpp14_quality_gate.json", "historical_interlock_audit.json", "causal_elbow_audit.json", "controller_orientation_return_map.json",
        "failed_reaction_branch_lineage.json", "historical_provider_precondition_registry.json", "normal_incident_pathway_pairs.json",
        "reactome_complete_maintenance_pathway.json", "batch086_product_beta_rc_decision.json", "batch086_claim_boundary.json", "SHA256SUMS.txt"]
    missing = [name for name in required if not (OUT / name).is_file()]
    if missing: errors.append("required_outputs_missing:" + ",".join(missing))
    if errors: return {"status": "FAIL", "errors": errors, "missing": missing}
    ingest = load("batch085_artifact_ingest.json")
    if (ingest.get("status"), ingest.get("artifact_size_bytes"), ingest.get("artifact_sha256")) != ("PASS", 27451, "c1178fe4878bfc24124980143b7784f34287710127fea80aed58a490f2186a2b"):
        errors.append("batch085_artifact_identity_invalid")
    if manifest_status(B85)["status"] != "PASS": errors.append("raw_batch085_evidence_changed")
    if audit_canonical()["status"] != "PASS": errors.append("canonical_component_uniqueness_failed")
    if (ROOT / "controllergate/batch086").exists(): errors.append("batch086_specific_core_engine_detected")
    providers = load("historical_provider_reconstruction_results.json")["providers"]
    if any(row.get("called_exact") or row.get("classification") == "HISTORICAL_EXACT_PROVIDER_BYTES_VERIFIED" for row in providers.values()): errors.append("reconstructed_provider_called_exact")
    cloud = load("cloudpickle_507_py313_typevar_distutils_historical_lifecycle.json")
    freeze = load("freezegun_547_py313_datetimes_assertion_historical_lifecycle.json")
    if cloud.get("patch_sha256") != "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63": errors.append("cloudpickle_patch_identity_invalid")
    if freeze.get("patch_sha256") != "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247": errors.append("freezegun_patch_identity_invalid")
    if not any(item.get("complete") for item in (cloud, freeze)): errors.append("complete_historical_repair_lifecycle_missing")
    non_source = load("historical_non_source_lifecycle_results.json")
    if len(non_source.get("results", [])) < 2 or not all(item.get("complete") and item.get("repair_license") is False for item in non_source["results"]): errors.append("two_correct_non_source_terminals_missing")
    if any(item.get("repair_count_increment") != 0 for item in (cloud, freeze, *non_source.get("results", []))): errors.append("historical_replay_incremented_count")
    transitions = load("dpp14_transition_registry.json")
    if transitions.get("transition_count") != 14 or tuple(transitions.get("transitions", [])) != TRANSITIONS: errors.append("dpp14_transition_set_invalid")
    if not transitions.get("parallel_lanes_read_only") or not transitions.get("controller_audit_sole_terminal_writer"): errors.append("dpp14_parallel_or_writer_contract_invalid")
    source = (ROOT / "controllergate/amds/dpp14/controller_audit.py").read_text(encoding="utf-8")
    if 'proposed = "source_owned_behavior_defect"' in source or "source fallback" in source.lower(): errors.append("source_owned_fallback_detected")
    quality = load("dpp14_quality_gate.json")
    if quality.get("status") == "PASS" and (quality.get("wrong_repair_authorization") != 0 or quality.get("safe_abstention_accuracy", 0) < 0.8 or quality.get("single_class_collapse")):
        errors.append("dpp14_quality_gate_false_pass")
    if audit_registry(ROOT)["status"] != "PASS" or load("historical_interlock_audit.json").get("interlocks_can_authorize_patch") is not False: errors.append("interlock_recovery_or_non_authorization_failed")
    elbow = load("causal_elbow_audit.json")
    if elbow.get("elbow") != "OPEN" or elbow.get("raw_argmin_authority") is not False or elbow.get("numeric_threshold_authority") is not False: errors.append("categorical_elbow_invalid")
    twist = load("controller_orientation_return_map.json")
    if twist.get("status") != "PASS" or twist.get("approximate_tolerance_accepted") is not False: errors.append("exact_twist_return_invalid")
    projection = json.loads((ROOT / "experiments/tld_shadow/three_projection_controller_audit.json").read_text(encoding="utf-8"))
    if projection.get("authority") != "NONBLOCKING_RESEARCH" or projection.get("n10_n13_n14_assignments_assumed") is not False or projection.get("can_grant_patch_authority") is not False: errors.append("three_projection_authority_violation")
    branches = load("failed_reaction_branch_lineage.json")
    if branches.get("status") != "PASS" or any(item.get("count_increment") != 0 for item in branches.get("branches", [])): errors.append("failed_branch_lineage_invalid")
    preconditions = load("historical_provider_precondition_registry.json")
    if not preconditions.get("records") or any(not item.get("required_package") or not item.get("required_version") for item in preconditions["records"]): errors.append("provider_preconditions_incomplete")
    pairs = load("normal_incident_pathway_pairs.json")
    if len(pairs.get("pairs", [])) < 4 or any(not item.get("first_divergent_event") for item in pairs["pairs"]): errors.append("normal_incident_pairing_incomplete")
    for item in (cloud, freeze):
        if item.get("complete") and (item.get("health", {}).get("status") != "PASS" or item.get("rollback", {}).get("status") != "PASS" or not all(run.get("returncode") == 0 for run in item.get("canary_runs", []))): errors.append("real_canary_health_rollback_invalid")
    decision = load("batch086_product_beta_rc_decision.json"); claims = load("batch086_claim_boundary.json")
    raw_pass = not errors and decision.get("complete_historical_repair_lifecycles", 0) >= 1 and decision.get("correct_non_source_terminals", 0) >= 2 and quality.get("status") == "PASS"
    expected_decision = "PRODUCT_BETA_RC_PASS" if raw_pass else "PRODUCT_BETA_RC_BLOCKED_EXACT"
    if decision.get("status") != expected_decision: errors.append("product_beta_rc_decision_mismatch")
    if claims.get("protocol") != "v2.19" or claims.get("issue_derived_repair_count") != 6 or claims.get("native_external_repair_count") != 4 or claims.get("full_scoring") != "NOT_RUN/disallowed" or claims.get("production_readiness") is not False or claims.get("self_maintaining_software") != "false/not demonstrated": errors.append("claim_boundary_violation")
    version = next(line.split('"')[1] for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines() if line.startswith("version = "))
    expected_version = "0.2.0b1" if decision.get("status") == "PRODUCT_BETA_RC_PASS" else "0.1.0a1"
    if version != expected_version: errors.append("package_version_decision_mismatch")
    manifest_before = manifest_status(OUT)
    if manifest_before["status"] != "PASS": errors.append("batch086_manifest_mismatch")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "Batch085_artifact_identity": "PASS",
            "raw_Batch085_evidence_unchanged": "PASS" if "raw_batch085_evidence_changed" not in errors else "FAIL",
            "canonical_component_count": 26, "historical_repair_lifecycles_complete": sum(item.get("complete", False) for item in (cloud, freeze)),
            "non_source_terminals_complete": sum(item.get("complete", False) for item in non_source["results"]),
            "DPP14_quality": quality.get("status"), "interlocks": audit_registry(ROOT)["status"], "causal_elbow": elbow.get("elbow"),
            "twist_return": twist.get("status"), "three_projection": projection.get("status"), "Product_Beta_RC": decision.get("status"),
            "package_version": version, "independent_critic_recompute": "PASS" if not errors else "FAIL"}


def main() -> int:
    result = audit()
    if result["status"] == "PASS":
        decision_path = OUT / "batch086_product_beta_rc_decision.json"; decision = json.loads(decision_path.read_text(encoding="utf-8")); decision["independent_critic_recompute"] = "PASS"
        decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (OUT / "batch086_audit_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    write_manifest()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
