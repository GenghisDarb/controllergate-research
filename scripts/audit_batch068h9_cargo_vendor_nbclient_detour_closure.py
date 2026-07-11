from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.public_summary import audit_public_summary_text
from controllergate.runtime.cargo_provider_strategies import classify_cargo_failure

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h9_cargo_vendor_nbclient_detour_closure"
H8 = ROOT / "outputs/post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing"
EXPECTED_H8_SHA = "3f629da042c7cdf722c9284d8329e534f1b14d021906d3f43e9b2fea061cd44f"
EXPECTED_VENDOR_SHA = "55348126a7198d6dfd799fcda57bc449b87eb14160e8b86e0d170a1c2ed38698"


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    required = {
        "batch068h8_artifact_ingest.json", "batch068h8_state_preservation.json",
        "batch068h8_claim_boundary_preservation.json", "batch068h8_cargo_classification_correction.json",
        "cargo_cache_writability_audit_batch068h9.json", "cargo_cache_transport_decision_batch068h9.json",
        "cargo_provider_selection_batch068h9.json", "cargo_vendor_manifest_batch068h9.json",
        "cargo_vendor_offline_metadata_batch068h9.json", "cargo_provider_closure_batch068h9.json",
        "historical_builder_v3_identity_batch068h9.json", "historical_builder_v3_offline_preflight.json",
        "wheel_build_decisions_batch068h9.json", "pyzmq_wheel_verification_batch068h9.json",
        "rpds_wheel_verification_batch068h9.json", "amds_provider_build_transitions_batch068h9.json",
        "offline_capsule_sbom_origins_batch068h9.json", "warning_orthology_arms_batch068h9.json",
        "diagnostic_collection_equivalence_batch068h9.json", "nbclient_issue316_ownership_batch068h9.json",
        "nbclient_detour_closure_batch068h9.json", "batch068h9_final_decision.json",
        "public_claim_boundary_batch068h9.json", "batch068h9_summary.md", "SHA256SUMS.txt",
    }
    errors += [f"required_missing:{name}" for name in sorted(required) if not (OUT / name).is_file()]
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2)); return 1

    lines = (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    covered: set[str] = set()
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            errors.append("SHA256SUMS_malformed"); continue
        digest, rel = parts[0], parts[1].lstrip("*"); covered.add(rel)
        target = OUT / rel
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            errors.append(f"SHA256_mismatch:{rel}")
    actual = {path.name for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"}
    if covered != actual: errors.append("SHA256SUMS_coverage_invalid")
    if len(actual) + 1 > 25: errors.append("compact_evidence_limit_exceeded")

    ingest = load("batch068h8_artifact_ingest.json")
    if not (ingest.get("status") == "PASS" and ingest.get("observed_size_bytes") == 207576 and ingest.get("observed_sha256") == EXPECTED_H8_SHA and ingest.get("file_count") == 118): errors.append("h8_artifact_identity_invalid")
    if ingest.get("outer_manifest", {}).get("checked") != 117 or ingest.get("internal_manifest", {}).get("checked") != 70: errors.append("h8_manifest_counts_invalid")
    if any(ingest.get(key) for key in ("unsafe_paths", "duplicate_paths", "forbidden_payloads")): errors.append("h8_artifact_custody_invalid")

    correction = load("batch068h8_cargo_classification_correction.json")
    raw = (H8 / "official_runner_cargo_failure_raw.log").read_text(encoding="utf-8")
    if correction.get("corrected_classification") != "cargo_cache_not_writable" or classify_cargo_failure(raw, 101) != "cargo_cache_not_writable": errors.append("h8_cargo_permission_classification_invalid")
    if any(classify_cargo_failure(text, 1) == "cargo_http_server_error" for text in ("downloaded 500 bytes", "crate 502", "version 503.0", "error 504")): errors.append("loose_http_substring_classification_present")
    if any(classify_cargo_failure(text, 1) != "cargo_http_server_error" for text in ("HTTP 500", "status code 503", "response 502")): errors.append("structured_http_classification_invalid")

    cache = load("cargo_cache_writability_audit_batch068h9.json")
    if cache.get("status") != "PASS" or not all(cache.get("checks", {}).get(key) for key in ("directory", "write", "rename", "database_file", "subdirectory", "delete")): errors.append("cargo_cache_preflight_invalid")
    provider = load("cargo_provider_selection_batch068h9.json")
    attempts = provider.get("strategy_attempts", [])
    if not (provider.get("status") == "PASS" and provider.get("selected_method") == "direct_lock_vendor" and len(attempts) >= 2 and attempts[0].get("status") == "BLOCK" and attempts[1].get("status") == "PASS"): errors.append("cargo_provider_fallback_authority_invalid")
    if provider.get("package_count") != 38 or provider.get("file_count") != 1320 or provider.get("provider_hash") != EXPECTED_VENDOR_SHA: errors.append("cargo_vendor_identity_invalid")
    vendor = load("cargo_vendor_manifest_batch068h9.json")
    if vendor.get("status") != "PASS" or vendor.get("checksums_verified") != 38 or vendor.get("config_path_in_container") != "/opt/cargo-vendor": errors.append("cargo_vendor_closure_invalid")
    metadata = load("cargo_vendor_offline_metadata_batch068h9.json")
    metadata_command = " ".join(str(item) for item in metadata.get("command", []))
    if not (metadata.get("status") == "PASS" and metadata.get("executed") is True and metadata.get("network") == "none" and "metadata --locked --offline" in metadata_command): errors.append("actual_offline_metadata_invalid")

    builder = load("historical_builder_v3_identity_batch068h9.json")
    preflight = load("historical_builder_v3_offline_preflight.json")
    if builder.get("status") != "PASS" or builder.get("selected_cargo_method") != "direct_lock_vendor" or builder.get("cargo_provider_hash") != EXPECTED_VENDOR_SHA or builder.get("network_during_build") != "none": errors.append("builder_provider_consumption_invalid")
    if preflight.get("status") != "PASS" or preflight.get("cargo_metadata_locked_offline") != "PASS" or preflight.get("network") != "none": errors.append("builder_offline_preflight_invalid")
    wheels = load("wheel_build_decisions_batch068h9.json")
    successes = {row.get("package") for row in wheels.get("packages", []) if row.get("status") == row.get("verification_status") == row.get("runtime_status") == "PASS"}
    if wheels.get("status") != "PASS" or successes != {"coverage", "markupsafe", "pyzmq", "rpds-py"} or wheels.get("network") != "none" or wheels.get("local_h7_h8_wheels_promoted") is not False: errors.append("official_wheel_closure_invalid")
    for name in ("pyzmq_wheel_verification_batch068h9.json", "rpds_wheel_verification_batch068h9.json"):
        wheel = load(name)
        if wheel.get("status") != wheel.get("verification_status") or wheel.get("runtime_status") != "PASS" or not wheel.get("native_extensions"): errors.append(f"native_wheel_verification_invalid:{name}")

    amds = load("amds_provider_build_transitions_batch068h9.json")
    if amds.get("status") != "PASS" or min(amds.get(key, 0) for key in ("posterior_updates", "board_updates", "branches_closed")) < 1 or amds.get("architecture_expanded") is not False or amds.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED": errors.append("amds_transition_boundary_invalid")
    capsule = load("offline_capsule_sbom_origins_batch068h9.json")
    if capsule.get("status") != capsule.get("SBOM") or capsule.get("SBOM") != "PASS" or any(capsule.get(key) != "PASS" for key in ("runner_origin", "target_origin", "harness_origin", "source_tree_immutability", "test_tree_immutability")) or capsule.get("network") != "none": errors.append("offline_capsule_sbom_origin_invalid")
    warning = load("warning_orthology_arms_batch068h9.json")
    diagnostic = load("diagnostic_collection_equivalence_batch068h9.json")
    if warning.get("default", {}).get("classification") != "historical_warning_policy_boundary_reproduced" or warning.get("default_policy_mutated") is not False: errors.append("default_warning_policy_not_preserved")
    if not (warning.get("status") == "PASS" and warning.get("diagnostic_classification") == "decision_time_project_declared_warning_diagnostic" and diagnostic.get("status") == "PASS" and diagnostic.get("node_count", 0) > 0 and diagnostic.get("node_set_equivalence") and diagnostic.get("test_bodies_executed") == 0): errors.append("diagnostic_warning_orthology_invalid")

    ownership = load("nbclient_issue316_ownership_batch068h9.json")
    closure = load("nbclient_detour_closure_batch068h9.json")
    if ownership.get("classification") != "interpreter_mock_behavior_change" or ownership.get("source_repair_admissible") is not False or ownership.get("future_pr_evidence_used") is not False or not ownership.get("signature_equivalence"): errors.append("nbclient_ownership_invalid")
    if not (closure.get("status") == "PASS" and closure.get("retired_from_source_only_repair_queue") and closure.get("patch_generated") is False and closure.get("duplicate_clean_replay") == closure.get("count_gate") == "NOT_RUN" and closure.get("replacement_candidate_selected") is False and closure.get("next_major_action") == "batch070"): errors.append("nbclient_detour_closure_invalid")
    final = load("batch068h9_final_decision.json")
    boundary = load("public_claim_boundary_batch068h9.json")
    if final.get("status") != "PASS" or final.get("issue_derived_repair_count") != 4 or final.get("native_external_repair_count") != 4 or final.get("validated_protocol") != "v2.18" or final.get("next_major_action") != "batch070": errors.append("final_state_invalid")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated" or final.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED": errors.append("claim_boundary_invalid")
    if boundary.get("status") != "PASS" or boundary.get("next_major_action") != "batch070": errors.append("public_claim_boundary_invalid")
    if audit_public_summary_text((OUT / "batch068h9_summary.md").read_text(encoding="utf-8")).get("status") != "PASS": errors.append("public_language_invalid")
    forbidden = [path.name for path in OUT.iterdir() if path.is_file() and path.suffix.lower() in {".zip", ".tar", ".tgz", ".whl", ".crate", ".pyc"}]
    if forbidden: errors.append("forbidden_committed_payload")

    status = "PASS" if not errors else "FAIL"
    print(json.dumps({"status": status, "errors": errors, "h8_verification": ingest.get("status"), "cargo_provider": provider.get("status"), "wheel_status": wheels.get("status"), "ownership": ownership.get("classification"), "next_major_action": final.get("next_major_action")}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
