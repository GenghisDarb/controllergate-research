from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record
from controllergate.runtime.network_event_ledger import verify_network_event_ledger
from controllergate.runtime.network_policy import validate_network_policy
from controllergate.core.public_summary import audit_public_summary_text

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h8_authorized_cargo_warning_candidate_routing"
EXPECTED_H7_SHA = "1221e67eedeb828f3bcd539ee5e1e7fd496f54ec361dfbf28811b1c9bf24b6fe"


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def manifest_errors() -> list[str]:
    errors: list[str] = []
    path = OUT / "SHA256SUMS.txt"
    if not path.is_file():
        return ["SHA256SUMS_missing"]
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            errors.append("SHA256SUMS_malformed")
            continue
        target = OUT / parts[1].lstrip("*")
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != parts[0]:
            errors.append(f"SHA256_mismatch:{parts[1]}")
    return errors


def main() -> int:
    errors = manifest_errors()
    required = {
        "batch068h7_artifact_ingest.json", "batch068h7_official_state_preservation.json",
        "batch068h7_official_local_divergence_registry.json", "batch068h7_network_authorization_mismatch.json",
        "network_authorization_policy_v1.json", "provider_acquisition_authorization_batch068h8.json",
        "offline_execution_authorization_batch068h8.json", "network_event_ledger_batch068h8.jsonl",
        "official_runner_cargo_failure_raw_log_index.json", "official_runner_cargo_failure_classification.json",
        "cargo_fetch_result_batch068h8.json", "cargo_provider_authority_batch068h8.json",
        "builder_authority_nonconflation_audit.json", "amds_active_board_v4_batch068h8.json",
        "amds_board_v4_state_consistency_audit.json", "amds_posterior_update_trace_batch068h8.jsonl",
        "amds_official_execution_summary_batch068h8.json", "wheel_decisions_batch068h8.json",
        "offline_capsule_sbom_decision_batch068h8.json", "warning_orthology_arm_registry_batch068h8.json",
        "project_declared_nowarn_collection_equivalence.json", "nbclient_issue316_ownership_decision.json",
        "nbclient_candidate_retirement_decision.json", "replacement_candidate_selection_batch068h8.json",
        "batch068h8_final_decision.json", "public_claim_boundary_audit_batch068h8.json", "SHA256SUMS.txt",
    }
    errors += [f"required_missing:{name}" for name in sorted(required) if not (OUT / name).is_file()]
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2)); return 1

    ingest = load("batch068h7_artifact_ingest.json")
    if not (ingest.get("status") == "PASS" and ingest.get("observed_size_bytes") == 47398 and ingest.get("observed_sha256") == EXPECTED_H7_SHA and ingest.get("file_count") == 48): errors.append("h7_artifact_identity_invalid")
    if ingest.get("outer_manifest", {}).get("checked") != 47 or ingest.get("internal_manifest", {}).get("checked") != 36: errors.append("h7_manifest_counts_invalid")
    if any(ingest.get(key) for key in ("unsafe_paths", "duplicate_paths", "forbidden_payloads")): errors.append("h7_artifact_custody_invalid")
    divergence = load("batch068h7_official_local_divergence_registry.json")
    authority = load("batch068h7_official_authority_decision.json")
    if divergence.get("authority") != "OFFICIAL_WORKFLOW_ARM" or authority.get("authoritative_arm") != "OFFICIAL_WORKFLOW_ARM" or authority.get("local_diagnostic_authority") is not False: errors.append("official_local_evidence_conflated")
    mismatch = load("batch068h7_network_authorization_mismatch.json")
    if not mismatch.get("mismatch") or mismatch.get("historical_authorization_network_phases") != []: errors.append("h7_network_authorization_mismatch_not_preserved")

    provider_auth = load("provider_acquisition_authorization_batch068h8.json")
    offline_auth = load("offline_execution_authorization_batch068h8.json")
    provider_policies = provider_auth.get("scope", {}).get("network_policies", [])
    offline_policies = offline_auth.get("scope", {}).get("network_policies", [])
    for label, value in (("provider", provider_auth), ("offline", offline_auth)):
        supplied = value.get("authorization_hash"); unsigned = {key: item for key, item in value.items() if key != "authorization_hash"}
        if supplied != hash_record(unsigned): errors.append(f"{label}_authorization_hash_invalid")
    if provider_auth.get("nonce") == offline_auth.get("nonce"): errors.append("network_authorizations_not_separate")
    if provider_auth.get("scope", {}).get("network_phases") != ["provider_acquisition"]: errors.append("provider_network_phase_not_bound")
    if offline_auth.get("scope", {}).get("network_phases") != []: errors.append("offline_network_capability_present")
    for item in [*provider_policies, *offline_policies]:
        if validate_network_policy(item, phase_id=item.get("phase_id", ""))["status"] != "PASS": errors.append(f"network_policy_invalid:{item.get('phase_id')}")
    if any(item.get("network_mode") != "none" for item in offline_policies): errors.append("offline_phase_network_not_none")
    network_ledger = verify_network_event_ledger(OUT / "network_event_ledger_batch068h8.jsonl")
    if network_ledger["status"] != "PASS" or network_ledger["checked"] < 1: errors.append("network_event_ledger_invalid_or_empty")

    cargo = load("cargo_fetch_result_batch068h8.json")
    if cargo.get("status") != "PASS" or cargo.get("method") not in {"cargo_fetch", "direct_vendor"}: errors.append("cargo_provider_not_closed")
    if cargo.get("classification") != "cargo_fetch_pass": errors.append("cargo_pass_misclassified")
    if cargo.get("provider_file_count", 0) <= 0 or cargo.get("crate_verification_count", 0) <= 0: errors.append("cargo_provider_evidence_empty")
    raw_index = load("official_runner_cargo_failure_raw_log_index.json")
    if not raw_index.get("complete_stdout_stderr") or not raw_index.get("sha256"): errors.append("cargo_complete_telemetry_missing")
    retry = load("cargo_fetch_retry_policy_v1.json")
    if "download_checksum_mismatch" not in retry.get("nonretryable", []): errors.append("cargo_checksum_retry_not_forbidden")
    nonconflation = load("builder_authority_nonconflation_audit.json")
    if nonconflation.get("status") != "PASS" or not nonconflation.get("toolchain_authority_independent_of_provider"): errors.append("toolchain_provider_authority_conflated")

    board = load("amds_active_board_v4_batch068h8.json")
    if board.get("schema_version") != "amds.board.v4" or board.get("board_hash") != hash_record({k: v for k, v in board.items() if k != "board_hash"}): errors.append("amds_board_v4_hash_invalid")
    closed = {key for key, value in board.get("branches", {}).items() if value.get("branch_state") == "CLOSED"}
    for key in closed:
        states = [cell.get("state") for cell in board.get("cells", []) if cell.get("branch_membership") == key]
        if not states or all(state == "UNKNOWN" for state in states): errors.append(f"closed_branch_cells_unknown:{key}")
    posterior_rows = [json.loads(line) for line in (OUT / "amds_posterior_update_trace_batch068h8.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if not posterior_rows or not all("prior" in row and "likelihoods" in row and "entropy_before" in row and "entropy_after" in row for row in posterior_rows): errors.append("amds_posterior_not_observation_driven")
    amds = load("amds_official_execution_summary_batch068h8.json")
    if amds.get("status") != "PASS" or min(amds.get(key, 0) for key in ("registries_generated", "probes_executed", "observations", "posterior_updates", "board_updates", "reranks")) < 1: errors.append("official_amds_execution_vacuous")
    if amds.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED": errors.append("amds_prospective_overclaim")

    wheels = load("wheel_decisions_batch068h8.json")
    packages = {row.get("package"): row for row in wheels.get("packages", [])}
    if set(packages) != {"coverage", "markupsafe", "pyzmq", "rpds-py"} or not all(row.get("status") == "PASS" and row.get("normalized_content_reproducibility") for row in packages.values()): errors.append("required_wheel_reproducibility_invalid")
    capsule = load("offline_capsule_sbom_decision_batch068h8.json")
    if capsule.get("status") != "PASS" or capsule.get("SBOM", {}).get("status") != "PASS" or any(capsule.get(key) != "PASS" for key in ("runner_origin", "target_origin", "harness_origin")): errors.append("offline_capsule_or_sbom_invalid")
    warning = load("warning_orthology_arm_registry_batch068h8.json")
    equivalent = load("project_declared_nowarn_collection_equivalence.json")
    if warning.get("default_policy", {}).get("classification") != "historical_warning_policy_boundary_reproduced": errors.append("default_warning_policy_not_preserved")
    if warning.get("diagnostic_label") != "decision_time_project_declared_warning_diagnostic" or equivalent.get("status") != "PASS" or equivalent.get("node_count", 0) <= 0: errors.append("diagnostic_warning_arm_invalid")
    ownership = load("nbclient_issue316_ownership_decision.json")
    retirement = load("nbclient_candidate_retirement_decision.json")
    if ownership.get("classification") != "interpreter_mock_behavior_change" or ownership.get("source_repair_admissible") is not False: errors.append("nbclient_ownership_invalid")
    if retirement.get("candidate_terminal_state") != "retired_from_source_only_repair_queue": errors.append("nbclient_retirement_invalid")
    replacement = load("replacement_candidate_selection_batch068h8.json")
    if replacement.get("selection_count") not in {0, 1} or replacement.get("selection_count") == 1 and replacement.get("selected") != "anyio_1028_old_pytest_assertion": errors.append("replacement_one_hop_invalid")
    if replacement.get("patch_generated") is not False: errors.append("replacement_patch_without_authority")

    final = load("batch068h8_final_decision.json")
    boundary = load("public_claim_boundary_audit_batch068h8.json")
    if final.get("patch_generated") is not False or final.get("count_gate") != "NOT_RUN": errors.append("patch_or_count_boundary_invalid")
    if final.get("issue_derived_repair_count") != 4 or final.get("native_external_repair_count") != 4: errors.append("repair_count_changed_without_gate")
    if final.get("validated_protocol_after") != "v2.18" or final.get("v2_19_promotion") not in {"BLOCK", "ELIGIBLE_NOT_PERFORMED"}: errors.append("protocol_boundary_invalid")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated": errors.append("public_claim_boundary_invalid")
    if boundary.get("status") != "PASS" or boundary.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED": errors.append("claim_boundary_audit_invalid")
    for path in (ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md", OUT / "batch068h8_summary.md"):
        if audit_public_summary_text(path.read_text(encoding="utf-8")).get("status") != "PASS": errors.append(f"public_language_invalid:{path.relative_to(ROOT).as_posix()}")
    forbidden = [p.name for p in OUT.iterdir() if p.is_file() and p.suffix.lower() in {".zip", ".tar", ".tgz", ".whl", ".crate", ".pyc"}]
    if forbidden: errors.append("forbidden_committed_payload")
    if not (OUT / "official_runner_cargo_failure_raw.log").exists() and len([p for p in OUT.iterdir() if p.is_file()]) > 42: errors.append("compact_evidence_limit_exceeded")

    status = "PASS" if not errors else "FAIL"
    print(json.dumps({"status": status, "errors": errors, "h7_artifact": "PASS", "cargo_provider": cargo.get("status"), "amds": amds.get("status"), "wheel_status": wheels.get("status"), "ownership": ownership.get("classification"), "replacement": replacement.get("selected"), "exact_blocker": final.get("exact_blocker")}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
