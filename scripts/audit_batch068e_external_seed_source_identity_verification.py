from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.manifests import verify_manifest
from controllergate.core.public_summary import audit_public_summary_text

OUT_NAME = "post_v2_37_hardening_batch068e_external_seed_source_identity_verification"
OUT_DIR = ROOT / "outputs" / OUT_NAME

EXTERNAL_LEADS = [
    "numpy_21994_ufunc_overflow",
    "pytest_11058_unraisable_exception",
    "black_2992_blackd_path_separator",
    "jinja_1628_lexer_py311",
    "scipy_16783_lbfgsb_tolerance",
]

REQUIRED_FILES = [
    "batch068d_artifact_ingestion_summary.json",
    "batch068d_artifact_sha256_verification.json",
    "batch068d_result_preservation.json",
    "batch068d_external_seed_blocker_preservation.json",
    "batch068d_claim_boundary_preservation.json",
    "source_identity_verification_policy_batch068e.json",
    "external_seed_source_identity_schema_batch068e.json",
    "candidate_sha_verification_policy_batch068e.json",
    "issue_provenance_policy_batch068e.json",
    "automated_seed_intake_engine_status_batch068e.json",
    "external_seed_identity_verification_results_batch068e.json",
    "external_seed_candidate_sha_resolution_requests_batch068e.json",
    "external_seed_approved_identity_registry_batch068e.json",
    "external_seed_rejected_identity_registry_batch068e.json",
    "candidate_sha_resolution_request_schema_batch068e.json",
    "candidate_sha_resolution_request_queue_batch068e.json",
    "candidate_sha_resolution_policy_batch068e.json",
    "automated_seed_discovery_engine_plan_batch068e.json",
    "universal_seed_intake_state_machine_batch068e.json",
    "seed_identity_cache_batch068e.json",
    "seed_intake_autonomy_tiers_batch068e.json",
    "external_seed_command_orthology_readiness_batch068e.json",
    "existing_backlog_source_identity_gap_scan_batch068e.json",
    "existing_backlog_sha_resolution_request_queue_batch068e.json",
    "existing_backlog_auto_identity_promotion_batch068e.json",
    "external_lead_provider_quality_ledger_batch068e.json",
    "self_maintenance_bottleneck_reduction_plan_batch068e.json",
    "reactome_style_source_identity_registry_batch068e.json",
    "reactome_style_environment_orthology_registry_batch068e.json",
    "reactome_style_prior_batch_continuity_batch068e.json",
    "chromosomal_maintenance_order_lock_batch068e.json",
    "sister_cohesion_baseline_registry_guard_batch068e.json",
    "chromosomal_failed_branch_closure_registry_batch068e.json",
    "homologous_transfer_guard_batch068e.json",
    "safe_abstention_apoptosis_watchdog_batch068e.json",
    "batch068e_handoff_plan.json",
    "batch068e_final_decision.json",
    "batch068e_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_IMPLEMENTATION_FILES = [
    "controllergate/core/source_identity.py",
    "controllergate/core/external_seed_verifier.py",
    "controllergate/core/candidate_sha_verifier.py",
    "controllergate/core/issue_provenance.py",
    "controllergate/core/seed_identity_cache.py",
    "controllergate/core/candidate_sha_resolution.py",
    "configs/source_identity_verification_policy.json",
    "configs/external_seed_source_identity_schema.json",
    "configs/candidate_sha_verification_policy.json",
    "configs/issue_provenance_policy.json",
    "scripts/generate_batch068e_external_seed_source_identity_verification.py",
    "scripts/audit_batch068e_external_seed_source_identity_verification.py",
    ".github/workflows/post_v2_37_hardening_batch068e_external_seed_source_identity_verification.yml",
]


def read_json(name: str | Path) -> Any:
    path = OUT_DIR / name if isinstance(name, str) else name
    return json.loads(path.read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_identity_records(errors: list[str]) -> None:
    results = read_json("external_seed_identity_verification_results_batch068e.json")
    requests = read_json("candidate_sha_resolution_request_queue_batch068e.json")
    approved = read_json("external_seed_approved_identity_registry_batch068e.json")
    rejected = read_json("external_seed_rejected_identity_registry_batch068e.json")
    expect(errors, results.get("status") == "PASS", "identity results not PASS")
    expect(errors, results.get("candidate_count") == 5, "expected five external leads")
    expect(errors, requests.get("request_count") == 5, "expected five SHA resolution requests")
    expect(errors, approved.get("approved_identity_count") == 5, "expected five repo/issue verified identities")
    expect(errors, rejected.get("rejected_count") == 0, "unexpected rejected identity")
    seen = {row.get("candidate_id") for row in results.get("records", [])}
    expect(errors, seen == set(EXTERNAL_LEADS), f"external lead set mismatch {seen}")
    for row in results.get("records", []):
        cid = row["candidate_id"]
        expect(errors, row.get("repo_identity_status") == "repo_verified", f"{cid} repo not verified")
        expect(errors, row.get("issue_identity_status") == "issue_verified", f"{cid} issue not verified")
        expect(errors, row.get("candidate_sha_status") == "candidate_sha_missing_resolution_required", f"{cid} SHA status changed")
        expect(errors, row.get("verified_candidate_sha") is None, f"{cid} invented verified SHA")
        expect(errors, row.get("candidate_sha_resolves_to_commit") is False, f"{cid} commit resolved without SHA")
        expect(errors, row.get("approval_status") == "approved_issue_identity_verified_sha_missing", f"{cid} wrong approval status")
        expect(errors, row.get("autonomy_tier") == 1, f"{cid} wrong autonomy tier")
        expect(errors, row.get("source_checkout_committed") is False, f"{cid} source checkout committed")
        expect(errors, row.get("fixed_or_future_source_read") is False, f"{cid} fixed/future source read")
        expect(errors, row.get("gold_patch_read") is False, f"{cid} gold patch read")
        expect(errors, row.get("issue_fix_text_used") is False, f"{cid} issue fix text used")
        for rel in [
            f"external_seed_identity/{cid}/repo_identity.json",
            f"external_seed_identity/{cid}/issue_identity.json",
            f"external_seed_identity/{cid}/sha_verification.json",
            f"external_seed_identity/{cid}/decision_time_safe_source_manifest.json",
            f"external_seed_identity/{cid}/source_identity_terminal_state.json",
            f"decision_time_safe_source_manifest_{cid}_batch068e.json",
        ]:
            expect(errors, (OUT_DIR / rel).is_file(), f"{cid} missing {rel}")
        manifest = read_json(f"decision_time_safe_source_manifest_{cid}_batch068e.json")
        expect(errors, manifest.get("approved_for_metadata_scan") is False, f"{cid} metadata scan approved without SHA")
        expect(errors, manifest.get("approved_for_command_orthology_scan") is False, f"{cid} command orthology approved without SHA")
        expect(errors, manifest.get("approved_for_provider_command_probe") is False, f"{cid} provider command probe approved")


def audit_engine_and_backlog(errors: list[str]) -> None:
    engine = read_json("automated_seed_intake_engine_status_batch068e.json")
    tiers = read_json("seed_intake_autonomy_tiers_batch068e.json")
    orthology = read_json("external_seed_command_orthology_readiness_batch068e.json")
    backlog = read_json("existing_backlog_source_identity_gap_scan_batch068e.json")
    backlog_requests = read_json("existing_backlog_sha_resolution_request_queue_batch068e.json")
    provider = read_json("external_lead_provider_quality_ledger_batch068e.json")
    bottleneck = read_json("self_maintenance_bottleneck_reduction_plan_batch068e.json")
    expect(errors, engine.get("status") == "PASS", "engine status not PASS")
    expect(errors, engine.get("raw_leads_processed") == 5, "engine processed wrong count")
    expect(errors, engine.get("repo_issue_verified_count") == 5, "repo/issue verified count mismatch")
    expect(errors, engine.get("candidate_sha_verified_count") == 0, "candidate SHA verified unexpectedly")
    expect(errors, engine.get("tests_executed") == 0, "tests executed in Batch068e")
    expect(errors, engine.get("patch_generated") is False, "patch generated in Batch068e")
    expect(errors, tiers.get("tier1_repo_issue_verified_count") == 5, "tier 1 count mismatch")
    expect(errors, tiers.get("tier2_sha_verified_count") == 0, "tier 2 count mismatch")
    expect(errors, tiers.get("tier3_command_orthology_ready_count") == 0, "tier 3 count mismatch")
    expect(errors, orthology.get("tier2_seed_count") == 0, "command orthology ran without Tier 2")
    expect(errors, orthology.get("tests_executed") == 0, "orthology executed tests")
    expect(errors, backlog.get("candidate_count") == 94, "backlog scan count mismatch")
    expect(errors, backlog.get("physical_verification_budget") == 20, "backlog budget not recorded")
    expect(errors, backlog_requests.get("request_count") >= 1, "backlog SHA request queue missing")
    expect(errors, provider.get("status") == "PASS", "provider quality not PASS")
    expect(errors, bottleneck.get("status") == "PASS", "bottleneck plan not PASS")
    expect(errors, len(bottleneck.get("records", [])) >= 14, "bottleneck plan incomplete")


def audit_interlocks_and_final(errors: list[str]) -> None:
    for rel in [
        "reactome_style_source_identity_registry_batch068e.json",
        "reactome_style_environment_orthology_registry_batch068e.json",
        "reactome_style_prior_batch_continuity_batch068e.json",
        "chromosomal_maintenance_order_lock_batch068e.json",
        "sister_cohesion_baseline_registry_guard_batch068e.json",
        "chromosomal_failed_branch_closure_registry_batch068e.json",
        "homologous_transfer_guard_batch068e.json",
        "safe_abstention_apoptosis_watchdog_batch068e.json",
    ]:
        value = read_json(rel)
        expect(errors, value.get("status") == "PASS", f"{rel} not PASS")
        expect(errors, value.get("internal_metadata_only") is True or rel.startswith("sister_"), f"{rel} not internal metadata")
    expect(errors, read_json("chromosomal_maintenance_order_lock_batch068e.json").get("maintenance_order_violation_count") == 0, "maintenance order violation")
    expect(errors, read_json("homologous_transfer_guard_batch068e.json").get("homology_used_as_patch_authority_count") == 0, "routing used as patch authority")

    final = read_json("batch068e_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("batch068e_audit_status") == "PASS", "audit status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native count changed")
    expect(errors, final.get("external_seed_count") == 5, "external seed final count mismatch")
    expect(errors, final.get("repo_issue_verified_count") == 5, "repo/issue final count mismatch")
    expect(errors, final.get("candidate_sha_verified_count") == 0, "SHA final count must be zero")
    expect(errors, final.get("tier1_repo_issue_verified_count") == 5, "Tier 1 final count mismatch")
    expect(errors, final.get("tier2_sha_verified_count") == 0, "Tier 2 final count mismatch")
    expect(errors, final.get("tier3_command_orthology_ready_count") == 0, "Tier 3 final count mismatch")
    expect(errors, final.get("candidate_sha_resolution_request_count") == 5, "external SHA request count mismatch")
    expect(errors, final.get("existing_backlog_scanned_count") == 94, "existing backlog final count mismatch")
    expect(errors, final.get("next_allowed_action") == "batch068f_candidate_sha_resolution_intake", "unexpected next action")
    expect(errors, final.get("exact_blocker") == "candidate_sha_resolution_required_before_metadata_scan_or_command_probe", "unexpected final blocker")
    for key in ["patch_generated", "patch_applied", "source_mutated", "tests_mutated", "fixtures_mutated", "config_mutated", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]:
        expect(errors, final.get(key) is False, f"{key} must remain false")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining changed")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch068e_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "neutral public language audit failed")
    forbidden = [
        "reactome",
        "chromosomal",
        "biological",
        "torus",
        "tld",
        "tot-brot",
        "tot-bulb",
        "apoptosis",
        "nuclear pore",
        "sister chromatid",
    ]
    hits = [term for term in forbidden if term in text.lower()]
    expect(errors, not hits, f"public summary contains internal terms: {hits}")
    expect(errors, "not repair proof" in text, "public summary must state not repair proof")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch068e output directory")
    for rel in REQUIRED_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing output {rel}")
    for rel in REQUIRED_IMPLEMENTATION_FILES:
        expect(errors, (ROOT / rel).is_file(), f"missing implementation {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    artifact = read_json("batch068d_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch068d_artifact_absent_for_local_ingest"}, "unexpected Batch068d artifact status")
    if artifact.get("status") == "PASS":
        expect(errors, artifact.get("outer", {}).get("size_bytes") == 55763, "Batch068d artifact size mismatch")
        expect(errors, artifact.get("outer", {}).get("sha256") == "27f8357d3320e8e37ef50016d63976dabe81166a6dd0a74939b1347880dac319", "Batch068d artifact SHA mismatch")
        for name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch068d manifest failed {name}")
    audit_identity_records(errors)
    audit_engine_and_backlog(errors)
    audit_interlocks_and_final(errors)
    audit_public_summary(errors)
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch068e external seed source identity verification audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
