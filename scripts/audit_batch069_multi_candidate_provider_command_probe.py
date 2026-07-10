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
from controllergate.core.public_summary import FORBIDDEN_PUBLIC_TERMS, audit_public_summary_text

OUT_NAME = "post_v2_37_hardening_batch069_multi_candidate_provider_command_probe"
OUT_DIR = ROOT / "outputs" / OUT_NAME
TOP5 = [
    "audioread_144_py313_aifc_removed",
    "codex_wave3_aio_libs_aiosmtpd_issues_403",
    "codex_wave3_alpha_unito_streamflow_issues_1100",
    "codex_wave3_aws_neuron_nki_library_issues_5",
    "codex_wave3_biface_i18n_issues_86",
]

REQUIRED_TOP_FILES = [
    "batch068_artifact_ingestion_summary.json",
    "batch068_artifact_sha256_verification.json",
    "batch068_result_preservation.json",
    "batch068_top5_preservation.json",
    "batch068_claim_boundary_preservation.json",
    "pytest_parked_state_preservation_batch069.json",
    "batch069_probe_contract.json",
    "batch069_active_candidate_probe_set.json",
    "batch069_candidate_probe_order.json",
    "batch069_probe_budget_policy.json",
    "batch069_probe_result_inventory.json",
    "batch069_materialized_candidate_inventory.json",
    "batch069_parked_candidate_inventory.json",
    "batch069_rejected_candidate_inventory.json",
    "batch069_top_candidate_after_probe.json",
    "batch069_top_5_after_probe.json",
    "batch069_reward_signal_summary.json",
    "batch069_memory_lift_boundary_preservation.json",
    "seed_readiness_status_schema_batch069.json",
    "seed_readiness_rehabilitation_registry_batch069.json",
    "unapproved_seed_status_inventory_batch069.json",
    "unapproved_seed_rehabilitation_plan_batch069.json",
    "environment_gated_seed_recipe_registry_batch069.json",
    "manual_artifact_request_queue_batch069.json",
    "external_source_approval_queue_batch069.json",
    "seed_readiness_product_backlog_batch069.json",
    "approved_vs_prepared_seed_policy_batch069.json",
    "batch070_handoff_plan_batch069.json",
    "batch069_final_decision.json",
    "batch069_summary.md",
    "SHA256SUMS.txt",
]

READINESS_STATUSES = {
    "approved_for_current_probe",
    "approved_for_future_probe",
    "readiness_backlog",
    "environment_gated_with_recipe",
    "manual_artifact_required",
    "external_source_approval_required",
    "parked_with_reopen_condition",
    "terminal_with_exact_reason",
    "already_counted_excluded",
    "probe_only_routing_memory",
    "orthology_routing_only",
}

REQUIRED_CANDIDATE_FILES = [
    "candidate_identity.json",
    "source_custody_check.json",
    "candidate_sha_verification.json",
    "workspace_purity_plan.json",
    "provider_capsule_probe.json",
    "version_origin_probe.json",
    "runner_target_risk_probe.json",
    "command_boundary_manifest.json",
    "command_boundary_probe.json",
    "harness_origin_firewall.json",
    "pre_repair_replay_gate.json",
    "pre_repair_replay_result.json",
    "reward_signal.json",
    "terminal_state.json",
    "next_action_recommendation.json",
]


def read_json(path: Path | str) -> Any:
    return json.loads((OUT_DIR / path if isinstance(path, str) else path).read_text(encoding="utf-8"))


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def run_check(args: list[str], errors: list[str], label: str) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    expect(errors, proc.returncode == 0, f"{label} failed: {proc.stdout[-1200:]} {proc.stderr[-1200:]}")


def audit_public_summary(errors: list[str]) -> None:
    text = (OUT_DIR / "batch069_summary.md").read_text(encoding="utf-8")
    expect(errors, audit_public_summary_text(text).get("status") == "PASS", "Batch069 public summary failed neutral language audit")
    hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in text.lower()]
    expect(errors, not hits, f"Batch069 summary contains forbidden public terms: {hits}")


def audit_candidates(errors: list[str]) -> None:
    probe_set = read_json("batch069_active_candidate_probe_set.json")
    records = probe_set.get("records", [])
    ids = [item.get("candidate_id") for item in records]
    expect(errors, ids == TOP5, f"active candidate probe set must preserve top 5 order: {ids}")
    inventory = read_json("batch069_probe_result_inventory.json").get("records", [])
    expect(errors, len(inventory) == 5, f"expected 5 probed candidates, found {len(inventory)}")
    inventory_by_id = {item.get("candidate_id"): item for item in inventory}
    for cid in TOP5:
        cdir = OUT_DIR / "candidates" / cid
        expect(errors, cdir.is_dir(), f"missing candidate directory {cid}")
        for rel in REQUIRED_CANDIDATE_FILES:
            expect(errors, (cdir / rel).is_file(), f"missing {cid}/{rel}")
        if cid == "audioread_144_py313_aifc_removed":
            expect(errors, (cdir / "audioread_provider_backend_reopen_check.json").is_file(), "missing audioread provider backend reopen check")
        record = inventory_by_id.get(cid)
        expect(errors, isinstance(record, dict), f"missing aggregate record for {cid}")
        if not isinstance(record, dict):
            continue
        for field in [
            "provider_capsule_status",
            "command_boundary_status",
            "harness_origin_status",
            "pre_repair_replay_status",
            "terminal_state",
            "next_allowed_candidate_action",
            "audit_status",
        ]:
            expect(errors, field in record, f"{cid} missing aggregate field {field}")
        expect(errors, record.get("already_counted_status") == "not_already_counted", f"{cid} unexpectedly already counted")
        expect(errors, record.get("parked_candidate_status") == "not_parked", f"{cid} unexpectedly parked")
        expect(errors, record.get("gold_fixed_future_exclusion_status") == "PASS", f"{cid} forbidden evidence exclusion failed")
        expect(errors, record.get("audit_status") == "PASS", f"{cid} audit status not PASS")
        sha = read_json(cdir / "candidate_sha_verification.json")
        expect(errors, sha.get("status") == "PASS", f"{cid} candidate SHA verification failed")
        source = read_json(cdir / "source_custody_check.json")
        expect(errors, source.get("status") == "PASS", f"{cid} source custody failed")
        expect(errors, source.get("candidate_checkout_committed") is False, f"{cid} candidate checkout committed")
        workspace = read_json(cdir / "workspace_purity_plan.json")
        expect(errors, workspace.get("outside_live_repo") is True, f"{cid} workspace not outside live repo")
        expect(errors, workspace.get("source_mutation_allowed") is False, f"{cid} source mutation allowed")
        expect(errors, workspace.get("test_mutation_allowed") is False, f"{cid} test mutation allowed")
        command = read_json(cdir / "command_boundary_probe.json")
        expect(errors, command.get("issue_comment_fix_text_used") in {False, None}, f"{cid} used issue-comment fix text")
        harness = read_json(cdir / "harness_origin_firewall.json")
        expect(errors, harness.get("fixed_patch_gold_future_evidence_used") is False, f"{cid} used fixed/gold/future evidence")
        reward = read_json(cdir / "reward_signal.json")
        expect(errors, reward.get("graded_signal") == 0.0, f"{cid} reward signal must be zero")
        expect(errors, reward.get("repair_skill_memory_update_allowed") is False, f"{cid} repair memory update allowed")


def audit_seed_readiness(errors: list[str]) -> None:
    registry = read_json("seed_readiness_rehabilitation_registry_batch069.json")
    records = registry.get("records", [])
    expect(errors, registry.get("status") == "PASS", "seed readiness registry status not PASS")
    expect(errors, isinstance(records, list), "seed readiness records must be a list")
    if not isinstance(records, list):
        return
    batch068_inventory = json.loads((ROOT / "outputs" / "post_v2_37_hardening_batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_063d_063e_controls" / "candidate_seed_inventory_batch068.json").read_text(encoding="utf-8")).get("records", [])
    batch068_ids = {item.get("candidate_id") for item in batch068_inventory if isinstance(item, dict)}
    readiness_ids = {item.get("candidate_id") for item in records if isinstance(item, dict)}
    expect(errors, readiness_ids == batch068_ids, f"readiness registry does not account for every Batch068 seed: missing={sorted(batch068_ids-readiness_ids)[:10]} extra={sorted(readiness_ids-batch068_ids)[:10]}")
    current_probe_ids = set(TOP5)
    env_ids = set()
    manual_ids = set()
    external_ids = set()
    for item in records:
        status = item.get("batch069_readiness_status")
        cid = item.get("candidate_id")
        expect(errors, status in READINESS_STATUSES, f"{cid} invalid readiness status {status}")
        expect(errors, status != "unapproved_without_reason", f"{cid} unapproved without reason")
        if status != "approved_for_current_probe":
            expect(errors, bool(item.get("exact_blocker")), f"{cid} missing exact blocker")
            expect(errors, bool(item.get("reopen_condition")) or status == "terminal_with_exact_reason", f"{cid} missing reopen condition or terminal reason")
        else:
            expect(errors, cid in current_probe_ids, f"{cid} current-probe status but not in active probe set")
        if status == "environment_gated_with_recipe":
            env_ids.add(cid)
        if status == "manual_artifact_required":
            manual_ids.add(cid)
        if status == "external_source_approval_required":
            external_ids.add(cid)
        if status in {"approved_for_future_probe", "readiness_backlog", "environment_gated_with_recipe", "manual_artifact_required", "external_source_approval_required"}:
            expect(errors, "repair proof" in str(item.get("public_explanation", "")), f"{cid} missing prepared-not-proof explanation")
    unapproved = read_json("unapproved_seed_status_inventory_batch069.json")
    expect(errors, unapproved.get("unapproved_without_reason_count") == 0, "unapproved seed without rehabilitation path")
    env = read_json("environment_gated_seed_recipe_registry_batch069.json")
    recipe_ids = {item.get("candidate_id") for item in env.get("records", [])}
    expect(errors, env_ids == recipe_ids, f"environment-gated seed recipe mismatch: missing={env_ids-recipe_ids} extra={recipe_ids-env_ids}")
    for item in env.get("records", []):
        for field in [
            "environment_blocker_type",
            "provider_capsule_recipe",
            "approval_condition",
            "reopen_condition",
            "can_be_rechecked_in_CI",
        ]:
            expect(errors, field in item, f"{item.get('candidate_id')} environment recipe missing {field}")
    manual = read_json("manual_artifact_request_queue_batch069.json")
    manual_queue_ids = {item.get("candidate_id") for item in manual.get("records", [])}
    expect(errors, manual_ids == manual_queue_ids, f"manual artifact queue mismatch: missing={manual_ids-manual_queue_ids} extra={manual_queue_ids-manual_ids}")
    external = read_json("external_source_approval_queue_batch069.json")
    external_queue_ids = {item.get("candidate_id") for item in external.get("records", [])}
    expect(errors, external_ids == external_queue_ids, f"external source approval queue mismatch: missing={external_ids-external_queue_ids} extra={external_queue_ids-external_ids}")
    backlog = read_json("seed_readiness_product_backlog_batch069.json")
    expect(errors, backlog.get("status") == "PASS", "seed readiness product backlog missing/pass failed")
    expect(errors, (ROOT / "configs" / "controllergate_seed_readiness_backlog.json").is_file(), "missing seed readiness backlog config")
    policy = read_json("approved_vs_prepared_seed_policy_batch069.json")
    expect(errors, policy.get("unapproved_seeds_enter_repair_count_lanes") is False, "unapproved seeds can enter repair-count lanes")
    expect(errors, policy.get("prepared_but_not_approved_allowed") is True, "prepared-but-not-approved distinction missing")


def main() -> int:
    errors: list[str] = []
    expect(errors, OUT_DIR.is_dir(), "missing Batch069 output directory")
    for rel in REQUIRED_TOP_FILES:
        expect(errors, (OUT_DIR / rel).is_file(), f"missing Batch069 output {rel}")
    for rel in [
        "scripts/generate_batch069_multi_candidate_provider_command_probe.py",
        "scripts/audit_batch069_multi_candidate_provider_command_probe.py",
        ".github/workflows/post_v2_37_hardening_batch069_multi_candidate_provider_command_probe.yml",
        "configs/controllergate_seed_readiness_backlog.json",
    ]:
        expect(errors, (ROOT / rel).is_file(), f"missing Batch069 file {rel}")
    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1

    manifest = verify_manifest(OUT_DIR)
    expect(errors, manifest.get("status") == "PASS", f"SHA256SUMS failed: {manifest}")
    artifact = read_json("batch068_artifact_sha256_verification.json")
    expect(errors, artifact.get("status") in {"PASS", "batch068_artifact_absent_for_local_ingest"}, f"unexpected Batch068 artifact status {artifact.get('status')}")
    if artifact.get("status") == "PASS":
        outer = artifact.get("outer", {})
        entries = artifact.get("entries", {})
        expect(errors, outer.get("size_bytes") == 105081, "Batch068 artifact size mismatch")
        expect(errors, outer.get("sha256") == "f169aae0c3e145f5a4a0c410c8a2de8bee25e2d151a738b6fd2d9fe27c39565a", "Batch068 artifact SHA mismatch")
        expect(errors, entries.get("unsafe_path_count") == 0, "Batch068 unsafe artifact paths")
        expect(errors, entries.get("duplicate_path_count") == 0, "Batch068 duplicate artifact paths")
        expect(errors, artifact.get("nested_archive_cache_venv_pyc_payload_count") == 0, "Batch068 nested/cache payloads")
        for manifest_name, result in artifact.get("manifests", {}).items():
            expect(errors, result.get("status") == "PASS", f"Batch068 artifact manifest failed: {manifest_name}")

    pytest_record = read_json("pytest_parked_state_preservation_batch069.json")
    expect(errors, pytest_record.get("candidate_id") == "pytest_13895_pytest9_skiptest_behavior", "wrong parked Pytest candidate")
    expect(errors, pytest_record.get("generic_followup_forbidden") is True, "Pytest generic follow-up not forbidden")
    expect(errors, pytest_record.get("repair_skill_memory_allowed") is False, "Pytest repair memory allowed")
    audit_candidates(errors)
    audit_seed_readiness(errors)
    reward = read_json("batch069_reward_signal_summary.json")
    expect(errors, reward.get("repair_skill_memory_update_allowed_count") == 0, "repair memory update count must remain zero")
    final = read_json("batch069_final_decision.json")
    expect(errors, final.get("status") == "PASS", "final status not PASS")
    expect(errors, final.get("batch069_audit_status") == "PASS", "final audit status not PASS")
    expect(errors, final.get("current_protocol") == "v2.14", "current protocol changed")
    expect(errors, final.get("issue_derived_repair_count") == 4, "issue-derived count changed")
    expect(errors, final.get("native_external_repair_count") == 4, "native external count changed")
    for key in [
        "patch_generated",
        "patch_applied",
        "source_mutated",
        "tests_mutated",
        "fixtures_mutated",
        "config_mutated",
        "duplicate_replay_run",
        "count_gate_run",
        "repair_count_increment",
    ]:
        expect(errors, final.get(key) is False, f"{key} must remain false")
    expect(errors, final.get("active_candidate_count") == 5, "active candidate count changed")
    expect(errors, final.get("probed_candidate_count") == 5, "probed candidate count changed")
    expect(errors, final.get("total_seed_count_from_batch068", 0) >= 90, "Batch068 seed count not preserved in readiness layer")
    expect(errors, final.get("current_probe_seed_count") == 5, "current probe seed count changed")
    expect(errors, final.get("prepared_seed_count") == final.get("total_seed_count_from_batch068"), "not every seed prepared")
    expect(errors, final.get("unapproved_seed_count") == final.get("total_seed_count_from_batch068") - 5, "unapproved seed count mismatch")
    expect(errors, final.get("unapproved_with_exact_blocker_count") == final.get("unapproved_seed_count"), "unapproved exact blocker coverage mismatch")
    expect(errors, final.get("unapproved_without_reason_count") == 0, "unapproved seed without rehabilitation path")
    expect(errors, final.get("seed_readiness_rehabilitation_status") == "PASS", "seed readiness rehabilitation did not pass")
    expect(errors, final.get("product_readiness_backlog_status") == "PASS", "product readiness backlog did not pass")
    expect(errors, final.get("full_scoring") == "NOT_RUN/disallowed", "full scoring changed")
    expect(errors, final.get("memory_lift") == "not_demonstrated", "memory lift changed")
    expect(errors, final.get("self_maintaining_software") == "false/not_demonstrated", "self-maintaining status changed")
    expect(errors, final.get("next_allowed_action") in {
        "batch070_source_topology_and_patch_license_gate",
        "batch070_multi_candidate_source_topology_and_patch_license_gate",
        "batch069b_recoverable_provider_command_followup",
        "batch068b_source_expansion_registry_buildout_or_manual_artifact_intake",
        "batch068b_manual_artifact_and_external_source_custody_intake",
    }, "invalid next allowed action")
    audit_public_summary(errors)

    run_check([sys.executable, "scripts/audit_batch068_multi_seed_harvest_for_5th_issue_repair.py"], errors, "Batch068 audit")
    run_check([sys.executable, "scripts/audit_batch063e_pytest_runner_target_split_evidence_intake.py"], errors, "Batch063e audit")
    run_check([sys.executable, "scripts/audit_batch063d_pytest_safe_tag_acquisition_hardening.py"], errors, "Batch063d audit")
    run_check([sys.executable, "scripts/audit_batch063c_pytest_command_boundary_followup.py"], errors, "Batch063c audit")
    run_check([sys.executable, "scripts/audit_batch067_universal_wrapper_hardening_implementation.py"], errors, "Batch067 audit")
    run_check([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], errors, "current protocol audit")
    run_check([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], errors, "current protocol dry-run")

    if errors:
        print("FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Batch069 multi-candidate provider command probe audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
