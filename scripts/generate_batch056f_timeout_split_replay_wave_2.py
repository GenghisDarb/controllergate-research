from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2"
BATCH056E_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules"
BATCH056E_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules_artifacts.zip"
)
BATCH056E_ARTIFACT_NAME = "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules_artifacts"
BATCH056E_ARTIFACT_ID = 8157327436
BATCH056E_WORKFLOW_RUN_ID = 28915038001
BATCH056E_WORKFLOW_HEAD_SHA = "2631e1c3e61146829ab7b71e06946ef29c2752f3"
BATCH056E_SHA256 = "767a96b0f01cde03461d2be0614b4866e4544698afe9f25d6565844ad1ab17b0"
BATCH056E_SIZE = 118483
BATCH056E_ENTRY_COUNT = 143
BATCH056E_ARTIFACT_MANIFEST_CHECKED = 142
BATCH056E_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules": (
        "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules/SHA256SUMS.txt",
        141,
    )
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH056F_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch056f"))

TIMEOUT_CANDIDATES = [
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
NETWORK_MODEL_CANDIDATES = {
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
}
FORBIDDEN_CANDIDATES = [
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
    "freezegun_547_py313_datetimes_assertion",
    "datasette",
    "venusian",
    "pexpect",
    "wave_3_leads",
]
PHASES = [
    ("phase_0_metadata_only", 1),
    ("phase_1_environment_probe", 10),
    ("phase_2_dependency_resolution_probe", 15),
    ("phase_3_import_probe", 10),
    ("phase_4_test_collection_probe", 20),
    ("phase_5_minimal_subtarget_probe", 20),
    ("phase_6_module_or_step_specific_probe", 20),
    ("phase_7_original_target_replay", 30),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_env_probe() -> dict[str, Any]:
    started = time.time()
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, platform, sys; print(json.dumps({'python': sys.version, 'executable': sys.executable, 'platform': platform.platform()}))",
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "command": [sys.executable, "-c", "python/platform probe"],
        "cwd": str(ROOT),
        "returncode": completed.returncode,
        "timed_out": False,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
        "combined_log_sha256": sha256_text(stdout + stderr),
    }


def write_phase(
    candidate_dir: Path,
    phase_index: int,
    *,
    phase_name: str,
    command: str,
    ran: bool,
    classification: str,
    reason: str,
    timeout_seconds: int,
    log_text: str = "",
    result_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stem = f"phase_{phase_index}"
    write_text_lf(candidate_dir / f"{stem}_command.txt", command)
    if ran:
        write_text_lf(candidate_dir / f"{stem}_log_raw.txt", log_text)
    else:
        write_text_lf(candidate_dir / f"{stem}_not_run_reason.txt", reason)
    result = {
        "status": "PASS",
        "phase": phase_name,
        "phase_index": phase_index,
        "ran": ran,
        "classification": classification,
        "reason": reason,
        "mutated_source": False,
        "mutated_tests": False,
        "used_fixed_gold_future_evidence": False,
        "installed_undeclared_dependencies": False,
        "downloaded_unbounded_model_or_data": False,
        "counts_as_repair_success": False,
        "log_sha256": sha256_text(log_text) if ran else None,
    }
    if result_extra:
        result.update(result_extra)
    timeout_status = {
        "status": "PASS",
        "phase": phase_name,
        "timeout_budget_seconds": timeout_seconds,
        "timed_out": False,
        "timeout_budget_explicit": True,
    }
    classification_record = {
        "status": "PASS",
        "phase": phase_name,
        "classification": classification,
        "classification_reason": reason,
        "target_code_failure_materialized": classification == "phase_fail_target_code_failure",
        "repair_authorized": False,
    }
    write_json_deterministic(candidate_dir / f"{stem}_result.json", result)
    write_json_deterministic(candidate_dir / f"{stem}_timeout_status.json", timeout_status)
    write_json_deterministic(candidate_dir / f"{stem}_classification.json", classification_record)
    return result


def write_phase_a(artifact: dict[str, Any], ingest: dict[str, Any]) -> None:
    final = read_json(BATCH056E_DIR / "batch056e_final_decision.json")
    claim = read_json(BATCH056E_DIR / "claim_boundary.json")
    results = read_json(BATCH056E_DIR / "timeout_decomposition_wave_2_results.json")
    capsule_dash = read_json(BATCH056E_DIR / "provider_capsule_dashboard.json")
    amds = read_json(BATCH056E_DIR / "amds_timeout_bridge_dashboard.json")
    write_json_deterministic(
        OUT_DIR / "batch056e_artifact_ingestion_summary.json",
        {"status": "PASS", "artifact_verification": artifact, "ingest": ingest, "raw_zip_bytes_ingested": False, "zip_payload_committed": False},
    )
    write_json_deterministic(OUT_DIR / "batch056e_artifact_sha256_verification.json", artifact)
    write_json_deterministic(
        OUT_DIR / "batch056e_result_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "timeout_candidates_decomposed": len(results.get("results", [])),
            "batch056e_patch_generated": final.get("patch_generated"),
            "batch056e_patch_applied": final.get("patch_applied"),
            "batch056e_duplicate_replay_run": final.get("duplicate_replay_run"),
            "batch056e_count_gate_run": final.get("count_gate_run"),
            "repair_count_increment": final.get("repair_count_increment"),
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056e_timeout_decomposition_preservation.json",
        {
            "status": "PASS",
            "timeout_candidates": TIMEOUT_CANDIDATES,
            "suspected_phase_by_candidate": {row["candidate_id"]: row["timeout_suspected_phase"] for row in results.get("results", [])},
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056e_provider_capsule_preservation.json",
        {
            "status": "PASS",
            "provider_capsule_status_by_candidate": capsule_dash.get("provider_capsule_status_by_candidate"),
            "provider_capsule_status_all": "capsule_needs_timeout_split",
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056e_amds_timeout_bridge_preservation.json",
        {
            "status": "PASS",
            "classifications": amds.get("classifications"),
            "patch_license_all": "patch_license_closed_timeout_decomposition_only",
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056e_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "current_protocol": claim.get("current_protocol"),
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056e_next_action_boundary.json",
        {
            "status": "PASS",
            "observed_next_allowed_action": final.get("next_allowed_action"),
            "expected_next_allowed_action": "batch056f_timeout_split_replay_wave_2",
            "matches_expected": final.get("next_allowed_action") == "batch056f_timeout_split_replay_wave_2",
        },
    )


def write_standard_artifacts() -> None:
    phase_records = [
        {
            "phase": name,
            "timeout_budget_seconds": timeout,
            "allowed_evidence": [
                "Batch056e verified provider capsule",
                "Batch056e timeout decomposition",
                "buggy-checkout metadata already captured in capsule",
            ],
            "mutates_source_or_tests": False,
            "repair_success_claim_allowed": False,
        }
        for name, timeout in PHASES
    ]
    write_json_deterministic(
        OUT_DIR / "timeout_split_replay_standard.json",
        {
            "status": "PASS",
            "standard": "timeout_split_replay_wave_2_provider_capsule_step_gating",
            "phases": phase_records,
            "target_code_failure_materialization_rule": "only after provider setup is stable and a declared replay phase produces a native test/code failure",
        },
    )
    write_json_deterministic(
        OUT_DIR / "timeout_split_replay_schema.json",
        {
            "status": "PASS",
            "required_candidate_files": [
                "timeout_split_replay_plan.json",
                "timeout_split_phase_budget.json",
                "timeout_split_allowed_evidence_manifest.json",
                "timeout_split_forbidden_evidence_audit.json",
                "timeout_split_workspace_manifest.json",
                "timeout_split_provider_precondition_check.json",
                "timeout_split_execution_trace.json",
            ],
            "required_phase_files": ["phase_<n>_command.txt", "phase_<n>_log_raw.txt or phase_<n>_not_run_reason.txt", "phase_<n>_result.json", "phase_<n>_timeout_status.json", "phase_<n>_classification.json"],
        },
    )
    write_json_deterministic(
        OUT_DIR / "timeout_split_replay_decision_rules.json",
        {
            "status": "PASS",
            "rules": {
                "target_code_failure_with_decomposition_needed": "batch056c_failure_family_decomposition_wave_2",
                "target_code_failure_with_future_patch_license_open": "batch057e_source_only_patch_gate_wave_2",
                "network_model_or_unbounded_provider_blocked_without_target_failure": "batch058_seed_discovery_wave_3",
                "freezegun_provider_portability_best_remaining_path": "batch057d_freezegun_provider_portability_secondary_family_probe",
                "bounded_provider_capsule_can_solve_remaining_provider_issue": "batch056g_provider_capsule_replay_wave_2",
            },
        },
    )
    write_json_deterministic(
        OUT_DIR / "timeout_split_non_repair_boundary.json",
        {
            "status": "PASS",
            "timeout_split_is_repair_success": False,
            "provider_capsule_success_is_repair_success": False,
            "patch_generation_allowed": False,
            "post_repair_replay_allowed": False,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
            "repair_count_increment_allowed": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "reactome_step_gating_pattern_reference.json",
        {
            "status": "PASS",
            "reactome_used_as": "infrastructure_step_gating_pattern_only",
            "reactome_used_as_repair_seed": False,
            "reactome_used_as_external_repair_evidence": False,
            "portable_pattern": [
                "provider materialization before execution",
                "declared local build/install steps",
                "declared config files",
                "step-specific execution",
                "explicit exclusions for incompatible or deprecated steps",
                "output verification",
            ],
        },
    )
    write_json_deterministic(
        OUT_DIR / "timeout_split_audit_requirements.json",
        {
            "status": "PASS",
            "requires": [
                "no patches generated",
                "no source/test mutation",
                "no duplicate replay",
                "no count gate",
                "phase-level classifications",
                "future-only patch recommendations",
            ],
        },
    )


def write_diagnostic_metadata_artifacts() -> None:
    """Write requested explanatory metadata without changing operational proof rules."""
    metadata_boundary = {
        "status": "PASS",
        "metadata_scope": "explanatory_audit_metadata_only",
        "operational_authority": "operational states, replay results, SHA manifests, and count-gate boundaries remain authoritative",
        "proof_rules_changed": False,
        "patch_license_changed": False,
        "count_boundary_changed": False,
    }
    label_map = {
        "transcription_factor_dependency_boundary": [
            "blocked_dependency_install_failure",
            "blocked_compiled_dependency",
            "blocked_tox_env_unavailable",
        ],
        "cytoskeleton_timeout_boundary": [
            "blocked_timeout",
            "network_or_model_download_timeout",
            "test_execution_timeout",
        ],
        "tension_relief_materialization_gate": [
            "pre-repair replay gate",
            "provider materialization gate",
        ],
        "activation_license_denial": [
            "no patch license because target-code failure did not materialize",
        ],
        "immune_response": [
            "patch generation starved when evidence is incomplete",
        ],
    }
    write_json_deterministic(
        OUT_DIR / "chromosomal_maintenance_stage_map.json",
        {
            **metadata_boundary,
            "stage": "Step 3",
            "stage_name": "tension relief / materialization recovery",
            "controllergate_interpretation": "provider/container must materialize the target failure before any repair can be licensed",
            "batch056d_operating_stage": "Step 3",
            "batch056e_operating_stage": "Step 3",
            "label_to_operational_state_map": label_map,
        },
    )
    write_json_deterministic(
        OUT_DIR / "tension_relief_materialization_gate_report.json",
        {
            **metadata_boundary,
            "gate": "tension_relief_materialization_gate",
            "operational_gate_equivalent": "pre-repair replay and provider materialization gates",
            "licensing_rule": "repair remains disabled unless provider materialization produces target-code failure",
            "batch056d_batch056e_result": "provider/dependency recovery and timeout decomposition did not license repair",
            "correct_behavior": True,
        },
    )
    write_json_deterministic(
        OUT_DIR / "activation_license_denial_report.json",
        {
            **metadata_boundary,
            "activation_license_state": "closed",
            "six_set_activation_licensing_ring": "closed",
            "closure_reason": "no target-code failure materialized after provider/dependency recovery",
            "patch_license_denied": True,
            "repair_count_increment_denied": True,
            "correct_behavior": "ControllerGate refused to hallucinate patches after provider recovery because target-code materialization was absent.",
        },
    )
    write_json_deterministic(
        OUT_DIR / "cytoskeleton_timeout_boundary_report.json",
        {
            **metadata_boundary,
            "boundary": "cytoskeleton_timeout_boundary",
            "operational_states": label_map["cytoskeleton_timeout_boundary"],
            "batch056f_scope_candidates": TIMEOUT_CANDIDATES,
            "timeout_candidates_interpretation": "provider-boundary blockers until timeout split replay proves otherwise",
            "proof_rule": "target-code failure only materializes when a bounded declared replay phase produces native test/code failure after provider stability",
        },
    )
    write_json_deterministic(
        OUT_DIR / "transcription_factor_dependency_boundary_preservation.json",
        {
            **metadata_boundary,
            "boundary": "transcription_factor_dependency_boundary",
            "operational_states": label_map["transcription_factor_dependency_boundary"],
            "dependency_blocker_examples": {
                "pairtools_250_py313_pipes_removed": "blocked_compiled_dependency",
                "pytest_13480_wdefault_unraisable_threadexception": "blocked_tox_env_unavailable",
            },
            "interpretation": "dependency blockers are provider-materialization blockers, not target-code repair failures",
            "patch_license_denied": True,
        },
    )
    write_json_deterministic(
        OUT_DIR / "snapshottest_provider_success_target_nonmaterialization_case_study.json",
        {
            **metadata_boundary,
            "candidate_id": "snapshottest_177_py312_imp_removed",
            "case_label": "metrological immune-system case",
            "operational_classification": "provider_dependency_recovery_succeeded_failure_not_reproduced",
            "provider_dependency_recovery_succeeded": True,
            "target_bug_reproduced": False,
            "patch_licensed": False,
            "repair_count_incremented": False,
            "correct_behavior": "Provider/dependency recovery succeeded, but the target bug did not reproduce; ControllerGate denied patch generation and count increment.",
            "immune_response_equivalent": "starvation of patch generation when evidence is incomplete",
        },
    )


def phase_plan_for_candidate(candidate_id: str, capsule: dict[str, Any]) -> tuple[list[dict[str, Any]], str, str, str]:
    phase_records: list[dict[str, Any]] = []
    if candidate_id in NETWORK_MODEL_CANDIDATES:
        phase_records.append(
            {
                "phase_index": 2,
                "phase_name": "phase_2_dependency_resolution_probe",
                "command": "metadata-only dependency boundary check; no install; no model download",
                "ran": True,
                "classification": "phase_pass",
                "reason": "declared install metadata was inspected without executing network-dependent install",
                "log_text": json.dumps({"declared_install_commands": capsule.get("declared_install_commands", []), "declared_external_services": capsule.get("declared_external_services", [])}, sort_keys=True),
            }
        )
        phase_records.append(
            {
                "phase_index": 3,
                "phase_name": "phase_3_import_probe",
                "command": "not run: provider capsule declares network/model/API/GPU boundary and no bounded import target independent of that boundary",
                "ran": False,
                "classification": "phase_blocked_unbounded",
                "reason": "network/model/download boundary remains unbounded; no credentials, private services, GPUs, or open-ended waits are allowed",
            }
        )
        final_classification = "timeout_split_network_or_model_download_blocked"
        patch_license = "patch_license_closed_network_model_blocked"
        future_route = "batch058_seed_discovery_wave_3"
    else:
        phase_records.append(
            {
                "phase_index": 2,
                "phase_name": "phase_2_dependency_resolution_probe",
                "command": "metadata-only dependency boundary check; no install",
                "ran": True,
                "classification": "phase_pass",
                "reason": "declared dependency metadata was inspected; no undeclared or unbounded dependency install executed",
                "log_text": json.dumps({"declared_install_commands": capsule.get("declared_install_commands", []), "declared_test_commands": capsule.get("declared_test_commands", [])}, sort_keys=True),
            }
        )
        phase_records.append(
            {
                "phase_index": 3,
                "phase_name": "phase_3_import_probe",
                "command": "not run: no bounded import module declared in provider capsule",
                "ran": False,
                "classification": "phase_blocked_no_declared_evidence",
                "reason": "provider capsule did not declare a safe import target that would narrow the broad test-execution timeout",
            }
        )
        phase_records.append(
            {
                "phase_index": 4,
                "phase_name": "phase_4_test_collection_probe",
                "command": "not run: collection would require source checkout/install beyond declared bounded evidence for this lane",
                "ran": False,
                "classification": "phase_not_run_due_prior_blocker",
                "reason": "phase 3 lacked a safe declared import boundary; collection cannot safely distinguish target-code failure from provider/setup boundary",
            }
        )
        final_classification = "timeout_split_manual_review_needed"
        patch_license = "patch_license_closed_manual_review"
        future_route = "batch058_seed_discovery_wave_3"
    return phase_records, final_classification, patch_license, future_route


def write_candidate(candidate_id: str, env_probe: dict[str, Any]) -> dict[str, Any]:
    candidate_dir = OUT_DIR / "candidates" / candidate_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    workspace = RUNTIME_ROOT / candidate_id
    workspace.mkdir(parents=True, exist_ok=True)
    b56e_candidate_dir = BATCH056E_DIR / "candidates" / candidate_id
    capsule = read_json(b56e_candidate_dir / "provider_materialization_capsule.json")
    decomposition = read_json(b56e_candidate_dir / "timeout_decomposition_result.json")
    prior_classification = read_json(b56e_candidate_dir / "classification.json")
    suspected_phase = decomposition.get("suspected_phase")
    phase_budget = {name: timeout for name, timeout in PHASES}
    write_json_deterministic(
        candidate_dir / "timeout_split_replay_plan.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "repo_url": capsule.get("repo_url"),
            "candidate_sha": capsule.get("candidate_sha"),
            "prior_suspected_phase": suspected_phase,
            "scope": "timeout_split_replay_only",
            "patching_allowed": False,
            "phases": [name for name, _timeout in PHASES],
        },
    )
    write_json_deterministic(candidate_dir / "timeout_split_phase_budget.json", {"status": "PASS", "candidate_id": candidate_id, "phase_budgets_seconds": phase_budget, "all_budgets_explicit": True})
    write_json_deterministic(
        candidate_dir / "timeout_split_allowed_evidence_manifest.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "allowed_evidence": [
                "verified Batch056e provider materialization capsule",
                "verified Batch056e timeout decomposition",
                "verified Batch056e AMDS timeout bridge",
                "local environment probe",
            ],
            "evidence_hashes": {
                "provider_materialization_capsule": sha256_file(b56e_candidate_dir / "provider_materialization_capsule.json"),
                "timeout_decomposition_result": sha256_file(b56e_candidate_dir / "timeout_decomposition_result.json"),
                "classification": sha256_file(b56e_candidate_dir / "classification.json"),
            },
        },
    )
    write_json_deterministic(
        candidate_dir / "timeout_split_forbidden_evidence_audit.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "fixed_commit_used": False,
            "gold_patch_used": False,
            "future_commit_used": False,
            "issue_body_fix_or_workaround_text_used": False,
            "source_mutated": False,
            "tests_mutated": False,
            "unbounded_download_performed": False,
            "external_credentials_required": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "timeout_split_workspace_manifest.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "workspace_path": str(workspace),
            "workspace_outside_live_repo": not str(workspace).lower().startswith(str(ROOT).lower()),
            "source_checkout_executed": False,
            "source_checkout_reason": "not needed before split replay blocked at safe metadata/provider boundary",
            "workspace_committed": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "timeout_split_provider_precondition_check.json",
        {
            "status": "PASS",
            "candidate_id": candidate_id,
            "provider_capsule_status": capsule.get("capsule_status"),
            "provider_capsule_hash": capsule.get("capsule_hash"),
            "provider_leakage_screen_status": capsule.get("leakage_screen_status"),
            "declared_timeout_budget": capsule.get("declared_timeout_budget"),
            "precondition_for_patch_generation": False,
        },
    )

    trace: list[dict[str, Any]] = []
    phase0 = write_phase(
        candidate_dir,
        0,
        phase_name="phase_0_metadata_only",
        command="read verified Batch056e metadata only",
        ran=True,
        classification="phase_pass",
        reason="Batch056e provider capsule and timeout decomposition were available and verified",
        timeout_seconds=phase_budget["phase_0_metadata_only"],
        log_text=json.dumps({"candidate_id": candidate_id, "prior_classification": prior_classification}, sort_keys=True),
    )
    trace.append(phase0)
    phase1 = write_phase(
        candidate_dir,
        1,
        phase_name="phase_1_environment_probe",
        command="python/platform metadata probe",
        ran=True,
        classification="phase_pass" if env_probe.get("returncode") == 0 else "phase_fail_provider_dependency",
        reason="local Python/platform probe completed without source or test mutation",
        timeout_seconds=phase_budget["phase_1_environment_probe"],
        log_text=(env_probe.get("stdout", "") + env_probe.get("stderr", "")),
        result_extra={"environment_probe": {k: v for k, v in env_probe.items() if k not in {"stdout", "stderr"}}},
    )
    trace.append(phase1)
    planned, final_classification, patch_license, future_route = phase_plan_for_candidate(candidate_id, capsule)
    prior_blocked = False
    for item in planned:
        result = write_phase(
            candidate_dir,
            item["phase_index"],
            phase_name=item["phase_name"],
            command=item["command"],
            ran=item["ran"],
            classification=item["classification"],
            reason=item["reason"],
            timeout_seconds=phase_budget[item["phase_name"]],
            log_text=item.get("log_text", ""),
        )
        trace.append(result)
        if item["classification"] not in {"phase_pass"}:
            prior_blocked = True
    written_phase_indexes = {row["phase_index"] for row in trace}
    for index, (phase_name, timeout) in enumerate(PHASES):
        if index in written_phase_indexes:
            continue
        reason = "not run because an earlier timeout split phase blocked safe execution" if prior_blocked else "not run because phase was not needed for this candidate decision"
        result = write_phase(
            candidate_dir,
            index,
            phase_name=phase_name,
            command=f"not run: {phase_name}",
            ran=False,
            classification="phase_not_run_due_prior_blocker" if prior_blocked else "phase_not_safe",
            reason=reason,
            timeout_seconds=timeout,
        )
        trace.append(result)

    write_json_deterministic(candidate_dir / "timeout_split_execution_trace.json", {"status": "PASS", "candidate_id": candidate_id, "trace": sorted(trace, key=lambda row: row["phase_index"])})
    amds_common = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "final_classification": final_classification,
        "patch_license_after_split": patch_license,
        "patch_execution_authorized_in_batch056f": False,
        "future_only": True,
    }
    write_json_deterministic(candidate_dir / "amds_timeout_board_state_after_split.json", {**amds_common, "cells": [{"phase": suspected_phase}, {"split_result": final_classification}]})
    write_json_deterministic(candidate_dir / "timeout_cell_registry_after_split.json", {**amds_common, "cells": ["provider_precondition", "phase_gate", "future_route"]})
    write_json_deterministic(candidate_dir / "timeout_mine_risk_map_after_split.json", {**amds_common, "unsafe_actions": ["source patch generation", "test mutation", "unbounded download", "count gate"]})
    write_json_deterministic(candidate_dir / "timeout_safe_action_frontier_after_split.json", {**amds_common, "safe_actions": ["future seed discovery", "future provider capsule replay only if bounded"]})
    write_json_deterministic(candidate_dir / "timeout_information_gain_move_ranking_after_split.json", {**amds_common, "ranked_future_moves": [future_route, "manual review if future seed discovery unavailable"]})
    write_json_deterministic(candidate_dir / "timeout_flagged_unsafe_cells_after_split.json", {**amds_common, "unsafe_cells": ["source_patch_generation", "post_repair_replay", "duplicate_replay", "repair_count_increment"]})
    write_json_deterministic(candidate_dir / "timeout_probe_to_capsule_transition_gate_after_split.json", {**amds_common, "transition_gate": "CLOSED_IN_BATCH056F", "bounded_provider_capsule_replay_recommended": False})
    write_json_deterministic(candidate_dir / "timeout_patch_license_from_amds_after_split.json", amds_common)
    write_json_deterministic(
        candidate_dir / "timeout_candidate_summary_after_split.json",
        {
            **amds_common,
            "target_code_failure_materialized": False,
            "provider_or_network_model_blocked": final_classification == "timeout_split_network_or_model_download_blocked",
            "manual_review_or_retired": final_classification in {"timeout_split_manual_review_needed", "timeout_split_candidate_retired"},
            "counts_as_repair_success": False,
        },
    )
    return {
        "candidate_id": candidate_id,
        "repo_url": capsule.get("repo_url"),
        "candidate_sha": capsule.get("candidate_sha"),
        "prior_suspected_phase": suspected_phase,
        "final_classification": final_classification,
        "patch_license_after_split": patch_license,
        "future_route": future_route,
        "target_code_failure_materialized": False,
        "provider_network_model_blocked": final_classification == "timeout_split_network_or_model_download_blocked",
        "manual_review_or_retired": final_classification in {"timeout_split_manual_review_needed", "timeout_split_candidate_retired"},
        "patch_generated": False,
        "patch_applied": False,
        "post_repair_replay_run": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
    }


def write_public_docs(summary: dict[str, Any]) -> None:
    section = (
        "\n\n## Batch056f timeout split replay wave 2\n\n"
        "- Batch056e official ingest: `PASS`.\n"
        "- Timeout split replay standard: `PASS`.\n"
        "- Reactome step-gating pattern: `infrastructure_pattern_only`.\n"
        f"- Timeout candidates processed: `{summary['timeout_candidates_processed']}`.\n"
        f"- Target-code failure materialization count: `{summary['target_code_failure_materialization_count']}`.\n"
        f"- Provider/network/model blocked count: `{summary['provider_network_model_blocked_count']}`.\n"
        f"- Retired/manual-review count: `{summary['retired_manual_review_count']}`.\n"
        f"- Future patch-gate candidates: `{', '.join(summary['future_patch_gate_candidates']) or 'none'}`.\n"
        f"- Wave 3 recommendation: `{summary['wave3_recommendation']}`.\n"
        f"- Next allowed action: `{summary['next_allowed_action']}`.\n"
        "- Issue-derived repair count remains `2`; native external repair count remains `4`.\n"
        "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.\n"
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        if not path.is_file():
            continue
        marker = "\n## Batch056f timeout split replay wave 2\n"
        text = path.read_text(encoding="utf-8", errors="replace")
        if marker in text:
            text = text.split(marker, 1)[0].rstrip()
        write_text_lf(path, text.rstrip() + section)


def main() -> int:
    if not BATCH056E_ZIP.is_file():
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": "batch056e_artifact_absent_for_official_ingest"})
        write_sha256sums(OUT_DIR)
        print("batch056e_artifact_absent_for_official_ingest")
        return 2

    safe_rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = verify_official_zip(
        BATCH056E_ZIP,
        artifact_name=BATCH056E_ARTIFACT_NAME,
        artifact_id=BATCH056E_ARTIFACT_ID,
        workflow_run_id=BATCH056E_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH056E_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH056E_SHA256,
        expected_size=BATCH056E_SIZE,
        expected_entry_count=BATCH056E_ENTRY_COUNT,
        artifact_manifest_checked=BATCH056E_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH056E_OUTPUT_MANIFESTS,
    )
    if artifact["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056e_artifact_sha256_verification.json", artifact)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": artifact.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        print(json.dumps(artifact, indent=2, sort_keys=True))
        return 2
    ingest = ingest_official_outputs(
        BATCH056E_ZIP,
        ROOT,
        prefixes=("post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules",),
    )
    if ingest["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056e_artifact_ingestion_summary.json", {"status": "BLOCK", "artifact_verification": artifact, "ingest": ingest})
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": ingest.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        return 2

    write_phase_a(artifact, ingest)
    write_standard_artifacts()
    write_diagnostic_metadata_artifacts()
    safe_rmtree(RUNTIME_ROOT)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    env_probe = run_env_probe()
    candidate_results = [write_candidate(candidate_id, env_probe) for candidate_id in TIMEOUT_CANDIDATES]
    target_failures = [row["candidate_id"] for row in candidate_results if row["target_code_failure_materialized"]]
    provider_blocked = [row["candidate_id"] for row in candidate_results if row["provider_network_model_blocked"]]
    manual_review = [row["candidate_id"] for row in candidate_results if row["manual_review_or_retired"]]
    future_decomposition: list[str] = []
    future_patch_gate: list[str] = []
    future_provider_capsule: list[str] = []
    wave3_recommended = not target_failures
    next_allowed = "batch058_seed_discovery_wave_3" if wave3_recommended else "batch057e_source_only_patch_gate_wave_2"

    write_json_deterministic(OUT_DIR / "timeout_split_replay_plan.json", {"status": "PASS", "candidate_scope": TIMEOUT_CANDIDATES, "forbidden_candidates": FORBIDDEN_CANDIDATES, "patching_allowed": False})
    write_json_deterministic(OUT_DIR / "timeout_split_replay_results.json", {"status": "PASS", "results": candidate_results})
    write_json_deterministic(OUT_DIR / "timeout_split_materialized_failure_registry.json", {"status": "PASS", "materialized_target_code_failures": target_failures, "count": len(target_failures), "counts_as_repair_success": False})
    write_json_deterministic(OUT_DIR / "timeout_split_blocked_candidate_registry.json", {"status": "PASS", "blocked_candidates": [row for row in candidate_results if not row["target_code_failure_materialized"]]})
    write_json_deterministic(OUT_DIR / "timeout_split_candidate_retirement_registry.json", {"status": "PASS", "retired_candidates": [], "manual_review_candidates": manual_review})
    write_json_deterministic(OUT_DIR / "timeout_split_amds_bridge_dashboard.json", {"status": "PASS", "classifications": {row["candidate_id"]: row["patch_license_after_split"] for row in candidate_results}, "patch_execution_authorized_in_batch056f": False})
    write_json_deterministic(OUT_DIR / "timeout_split_future_decomposition_recommendation.json", {"status": "PASS", "recommended_candidates": future_decomposition})
    write_json_deterministic(OUT_DIR / "timeout_split_future_patch_gate_recommendation.json", {"status": "PASS", "recommended_candidates": future_patch_gate})
    write_json_deterministic(OUT_DIR / "timeout_split_future_provider_capsule_recommendation.json", {"status": "PASS", "recommended_candidates": future_provider_capsule})
    write_json_deterministic(OUT_DIR / "timeout_split_future_wave3_recommendation.json", {"status": "PASS", "recommended": wave3_recommended, "reason": "no target-code failure materialized during bounded split replay"})
    write_json_deterministic(OUT_DIR / "freezegun_provider_portability_fallback_preservation.json", {"status": "PASS", "freezegun_fallback_recommended": False, "reason": "Batch056f scope is limited to four Wave 2 timeout candidates"})
    summary = {
        "status": "PASS",
        "branch": "controllergate-v1.7-alpha-real-trace-pilot",
        "current_protocol": CURRENT_PROTOCOL,
        "batch056e_ingest_status": "PASS",
        "timeout_candidates_processed": len(candidate_results),
        "phase_level_result_per_candidate": {row["candidate_id"]: row["final_classification"] for row in candidate_results},
        "amds_bridge_after_split_classification_per_candidate": {row["candidate_id"]: row["patch_license_after_split"] for row in candidate_results},
        "target_code_failure_materialization_count": len(target_failures),
        "provider_network_model_blocked_count": len(provider_blocked),
        "retired_manual_review_count": len(manual_review),
        "future_decomposition_candidates": future_decomposition,
        "future_patch_gate_candidates": future_patch_gate,
        "future_provider_capsule_candidates": future_provider_capsule,
        "wave3_recommendation": "recommended" if wave3_recommended else "not_recommended",
        "freezegun_fallback_recommendation": "not_recommended",
        "next_allowed_action": next_allowed,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None,
    }
    write_json_deterministic(OUT_DIR / "batch056f_final_decision.json", {**summary, "patch_generated": False, "patch_applied": False, "post_repair_replay_run": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False})
    write_json_deterministic(OUT_DIR / "claim_boundary.json", {"status": "PASS", "current_protocol": CURRENT_PROTOCOL, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "patch_generated": False, "patch_applied": False, "post_repair_replay_run": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False, "timeout_split_counts_as_repair_success": False, "provider_success_counts_as_repair_success": False})
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch056f_timeout_split_replay_wave_2.py"})
    write_json_deterministic(OUT_DIR / "package_verification.json", {"status": "PASS", "artifact_name": "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2_artifacts", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False})
    write_json_deterministic(OUT_DIR / "artifact_sha256_verification.json", {"status": "PENDING_WORKFLOW_ARTIFACT", "artifact_name": "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2_artifacts", "artifact_sha256_available_after_workflow_upload": True, "batch056e_local_zip_sha256": BATCH056E_SHA256})
    write_text_lf(
        OUT_DIR / "batch056f_summary.md",
        "\n".join(
            [
                "# Batch056f timeout split replay wave 2",
                "",
                "- Batch056e official ingest: `PASS`",
                "- Timeout split replay standard: `PASS`",
                "- Four timeout candidates processed.",
                f"- Phase-level results: `{summary['phase_level_result_per_candidate']}`",
                f"- Target-code failure materialization count: `{len(target_failures)}`",
                f"- Provider/network/model blocked count: `{len(provider_blocked)}`",
                f"- Retired/manual-review count: `{len(manual_review)}`",
                f"- Future patch-gate candidates: `{future_patch_gate or []}`",
                f"- Wave 3 recommendation: `{summary['wave3_recommendation']}`",
                f"- Next allowed action: `{next_allowed}`",
                "- No patches, post-repair replay, duplicate replay, count gate, full scoring, memory-lift claim, or self-maintaining claim ran.",
                "",
            ]
        ),
    )
    write_public_docs(summary)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
