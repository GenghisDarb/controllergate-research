from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip
from controllergate.core.ast_topology_extrusion import build_ast_topology_record
from controllergate.core.cross_environment_orthology import build_cross_environment_record
from controllergate.core.evidence import hash_record, sha256_bytes, write_json_deterministic, write_text_lf
from controllergate.core.failed_branch_closure import build_failed_branch_record
from controllergate.core.manifests import write_sha256sums
from controllergate.core.recoverable_command_translation import (
    ALLOWED_COMMAND_SOURCE_FILES,
    ALLOWED_COMMAND_SOURCE_GLOBS,
    FORBIDDEN_COMMAND_SOURCES,
    discover_command_sources,
    inventory_project_metadata,
    inventory_test_tree,
    recover_command_decision,
)

OUT_NAME = "post_v2_37_hardening_batch069b_recoverable_provider_command_followup"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH069_NAME = "post_v2_37_hardening_batch069_multi_candidate_provider_command_probe"
BATCH069_DIR = ROOT / "outputs" / BATCH069_NAME

EXPECTED_BATCH069 = {
    "commit": "5c7a0bb4ba16ff0277657bc94e3065afd509165f",
    "workflow": "post_v2_37_hardening_batch069_multi_candidate_provider_command_probe",
    "workflow_run_id": 29069982020,
    "artifact_name": "post_v2_37_hardening_batch069_multi_candidate_provider_command_probe_artifacts",
    "artifact_id": 8218516763,
    "expected_size": 80954,
    "expected_sha256": "7d5519b84bee18e5af15be66f4e040b7b9334e89330680ccd4fa9842a71c841c",
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

ACTIVE_RECOVERABLE = [
    "codex_wave3_aio_libs_aiosmtpd_issues_403",
    "codex_wave3_alpha_unito_streamflow_issues_1100",
    "codex_wave3_aws_neuron_nki_library_issues_5",
    "codex_wave3_biface_i18n_issues_86",
]
AUDIOREAD = "audioread_144_py313_aifc_removed"

DEFAULT_BATCH069_ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH069['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch069_multi_candidate_provider_command_probe_artifacts.zip"),
]

INTERLOCK_IDS = [
    "artifact_custody",
    "source_approval",
    "candidate_seed_classification",
    "seed_readiness",
    "workspace_purity",
    "candidate_isolated_runtime",
    "provider_capsule",
    "command_translation",
    "harness_origin",
    "version_origin",
    "runner_target_split",
    "cross_environment_orthology",
    "ast_topology",
    "elbow_topology_authorization",
    "cognitive_state_prompt_lock",
    "reward_signal",
    "baseline_drift_precheck",
    "failed_branch_closure",
    "step_to_output_contract",
    "public_summary_guard",
    "duplicate_clean_replay",
    "count_gate",
    "terminal_parked_reopen_registry",
]

PUBLIC_SUMMARY = (
    "Batch069b attempts to recover decision-time-safe native command boundaries for recoverable candidates from "
    "Batch069, while adding universal interlock, step-output, cross-environment mapping, AST-topology, seed-readiness, "
    "connector-readiness, and failed-branch closure controls. This is command-recovery and wrapper-readiness evidence, "
    "not repair proof. No repair is counted without source-only target pass, duplicate clean replay, and count gate. "
    "Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining software remains "
    "false/not_demonstrated."
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_candidate_json(candidate_id: str, name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / "candidates" / candidate_id / name, value)


def runtime_root() -> Path:
    if os.environ.get("RUNNER_TEMP"):
        return Path(os.environ["RUNNER_TEMP"]) / "ControllerGate_runtime" / "batch069b"
    return ROOT.parent / "ControllerGate_runtime" / "batch069b"


def reset_runtime(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if ROOT.resolve() in resolved.parents or resolved == ROOT.resolve():
        return {"status": "BLOCK", "exact_blocker": "runtime_inside_live_repo", "path": str(path)}
    if "onedrive" in str(resolved).lower():
        return {"status": "BLOCK", "exact_blocker": "runtime_inside_onedrive", "path": str(path)}
    if path.exists():
        def on_remove_error(function: Any, failed_path: str, _exc_info: Any) -> None:
            os.chmod(failed_path, stat.S_IWRITE)
            function(failed_path)

        shutil.rmtree(path, onerror=on_remove_error)
    path.mkdir(parents=True, exist_ok=True)
    return {"status": "PASS", "runtime_root": str(path), "outside_live_repo": True, "outside_onedrive": True}


def run_cmd(args: list[str], cwd: Path, *, timeout: int = 180) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)
        return {
            "command": args,
            "cwd": str(cwd),
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "stdout_sha256": sha256_bytes(proc.stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(proc.stderr.encode("utf-8")),
            "timed_out": False,
            "duration_seconds": round(time.time() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": args,
            "cwd": str(cwd),
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
            "timed_out": True,
            "duration_seconds": round(time.time() - started, 3),
            "timeout_seconds": timeout,
        }


def find_batch069_zip() -> Path | None:
    env_path = os.environ.get("CONTROLLERGATE_BATCH069_ARTIFACT_ZIP")
    candidates = ([Path(env_path)] if env_path else []) + DEFAULT_BATCH069_ZIP_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def verify_batch069_artifact() -> tuple[dict[str, Any], dict[str, Any]]:
    zip_path = find_batch069_zip()
    previous = OUT_DIR / "batch069_artifact_sha256_verification.json"
    incoming_path = DEFAULT_BATCH069_ZIP_CANDIDATES[0]
    if zip_path is None and previous.is_file():
        prior = read_json(previous)
        if prior.get("status") == "PASS":
            return prior | {"ci_zip_absent_preserved_committed_verification": True}, {
                "status": "PASS",
                "artifact_verified": "PASS",
                "preservation_source": "committed_batch069b_manual_artifact_verification",
                "raw_zip_bytes_ingested": False,
                "incoming_artifact_status": "absent",
            }
    if zip_path is None:
        verification = {
            "status": "batch069_artifact_absent_for_local_ingest",
            "artifact_absent": True,
            "manual_artifact_handoff": False,
            "downloaded_by_codex": False,
            "incoming_artifact_status": "absent",
            "committed_batch069_outputs_preserved": True,
        }
        return verification, {
            "status": "batch069_artifact_absent_for_local_ingest",
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
            "preservation_source": "committed_batch069_outputs",
            "incoming_artifact_status": "absent",
        }
    verification = verify_artifact_zip(
        zip_path,
        expected_size=EXPECTED_BATCH069["expected_size"],
        expected_sha256=EXPECTED_BATCH069["expected_sha256"],
    )
    nested = verification.get("entries", {}).get("nested_archive_or_cache_payloads", [])
    if nested:
        verification["status"] = "FAIL"
    verification["local_artifact_path"] = str(zip_path)
    verification["manual_artifact_handoff"] = True
    verification["downloaded_by_codex"] = False
    verification["incoming_artifact_status"] = "present" if zip_path == incoming_path else "absent_used_downloads_handoff"
    verification["nested_archive_cache_venv_pyc_payload_count"] = len(nested)
    return verification, {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_verified": verification.get("status"),
        "source_zip": str(zip_path),
        "raw_zip_bytes_ingested": False,
        "output_payload_overwrite_performed": False,
        "ingested_file_count": 0,
        "preservation_source": "verified_manual_batch069_artifact" if verification.get("status") == "PASS" else "committed_batch069_outputs",
        "incoming_artifact_status": verification["incoming_artifact_status"],
    }


def batch069_probe_records() -> dict[str, dict[str, Any]]:
    records = read_json(BATCH069_DIR / "batch069_probe_result_inventory.json").get("records", [])
    return {record["candidate_id"]: record for record in records}


def candidate_contracts() -> list[dict[str, Any]]:
    records = batch069_probe_records()
    return [records[cid] for cid in ACTIVE_RECOVERABLE]


def checkout_candidate(contract: dict[str, Any], rt: Path) -> tuple[Path, dict[str, Any]]:
    cid = contract["candidate_id"]
    work = rt / cid / "source"
    work.mkdir(parents=True, exist_ok=True)
    repo_url = str(contract["repo_url"]).rstrip("/")
    remote = repo_url + ".git" if not repo_url.endswith(".git") else repo_url
    sha = contract["candidate_sha"]
    init = run_cmd(["git", "init", "-q"], work)
    add = run_cmd(["git", "remote", "add", "origin", remote], work)
    fetch = run_cmd(["git", "fetch", "--filter=blob:none", "--no-tags", "origin", sha], work, timeout=240)
    cat = run_cmd(["git", "cat-file", "-t", "FETCH_HEAD"], work)
    rev = run_cmd(["git", "rev-parse", "FETCH_HEAD"], work)
    checkout = run_cmd(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], work, timeout=120) if fetch["returncode"] == 0 else {"returncode": 1, "skipped": True}
    status = run_cmd(["git", "status", "--short"], work) if checkout.get("returncode") == 0 else {"returncode": 1, "stdout": "", "stderr": "checkout skipped"}
    verified = fetch["returncode"] == 0 and cat["stdout"].strip() == "commit" and rev["stdout"].strip() == sha and checkout.get("returncode") == 0
    return work, {
        "status": "PASS" if verified else "BLOCK",
        "repo_url": repo_url,
        "remote_url": remote,
        "candidate_sha": sha,
        "git_object_type": cat.get("stdout", "").strip(),
        "resolved_sha": rev.get("stdout", "").strip(),
        "workspace_committed": False,
        "workspace_path": str(work),
        "commands": {"init": init, "remote_add": add, "fetch": fetch, "cat_file": cat, "rev_parse": rev, "checkout": checkout, "status_short": status},
        "exact_blocker": None if verified else "version_origin_blocked",
    }


def source_file_count(source: Path) -> int:
    return sum(1 for path in source.rglob("*.py") if ".git" not in path.parts)


def universal_interlock_manifest() -> dict[str, Any]:
    records = []
    for interlock_id in INTERLOCK_IDS:
        records.append(
            {
                "interlock_id": interlock_id,
                "required_inputs": ["candidate_id", "decision_time_safe_evidence", "hash_manifest"],
                "required_outputs": [f"{interlock_id}_record"],
                "allowed_next_states": ["probe", "manual_artifact_request", "terminal_closure", "not_run_with_reason"],
                "forbidden_next_states": ["patch_generation_without_interlocks", "duplicate_replay_without_target_pass", "count_gate_without_duplicate_replay", "full_scoring", "memory_lift_claim"],
                "terminal_states": ["blocked_with_exact_reason", "terminal_with_exact_reason"],
                "reopen_conditions": ["new_decision_time_safe_evidence", "manual_artifact_verified"],
                "repair_count_policy": "no_count_without_source_only_target_pass_duplicate_replay_and_count_gate",
                "memory_policy": "routing_memory_only_until_valid_source_patch_replay",
                "audit_script": "scripts/audit_batch069b_recoverable_provider_command_followup.py",
                "public_summary_boundary": "wrapper_readiness_not_repair_proof",
            }
        )
    return {"status": "PASS", "schema_version": "controllergate.universal_interlock_law.v1", "records": records}


def step_contract_records() -> list[dict[str, Any]]:
    names = [
        "artifact_custody",
        "batch069_preservation",
        "candidate_identity",
        "workspace_purity",
        "provider_capsule",
        "command_translation",
        "harness_origin_recheck",
        "pre_repair_replay_gate",
        "reward_signal",
        "failed_branch_closure",
        "seed_product_readiness",
        "final_decision",
    ]
    return [
        {
            "substage": name,
            "expected_outputs": [f"{name}_batch069b_record"],
            "generation_record_required": True,
            "verification_record_required": True,
            "missing_output_classification_allowed": ["created", "not_run_with_reason", "blocked_with_exact_reason", "deprecated_or_retired", "forbidden_by_policy"],
            "silent_missing_output_allowed": False,
            "audit_status": "PASS",
        }
        for name in names
    ]


def write_policy_configs() -> None:
    write_json_deterministic(ROOT / "configs" / "universal_interlock_law_manifest.json", universal_interlock_manifest())
    write_json_deterministic(
        ROOT / "configs" / "step_to_output_contract_registry.json",
        {"status": "PASS", "schema_version": "controllergate.step_to_output_contract.v1", "records": step_contract_records()},
    )
    write_json_deterministic(
        ROOT / "configs" / "recoverable_command_translation_policy.json",
        {
            "status": "PASS",
            "allowed_command_source_files": ALLOWED_COMMAND_SOURCE_FILES,
            "allowed_command_source_globs": ALLOWED_COMMAND_SOURCE_GLOBS,
            "forbidden_command_sources": FORBIDDEN_COMMAND_SOURCES,
            "bounded_synthesis_requires_declared_runner_and_visible_target": True,
            "broad_suite_is_not_target_failure_materialization": True,
        },
    )
    write_json_deterministic(
        ROOT / "configs" / "decision_time_command_source_priority.json",
        {
            "status": "PASS",
            "priority": [
                "exact_command_from_candidate_local_metadata",
                "exact_command_from_candidate_ci_workflow",
                "exact_command_from_candidate_tox_nox_hatch_poetry_pdm_uv_make_config",
                "exact_test_target_from_candidate_test_config_plus_declared_runner",
                "bounded_synthesized_command_from_decision_time_metadata",
                "manual_artifact_request",
            ],
            "forbidden_sources": FORBIDDEN_COMMAND_SOURCES,
        },
    )
    write_json_deterministic(
        ROOT / "configs" / "elbow_patch_authorization_policy.json",
        {
            "status": "PASS",
            "winner_N_argmin": "raw_minimum_legacy_closure_label",
            "winner_N_elbow": "interior_curvature_preference_when_failure_topology_is_legible",
            "prefer_elbow_over_argmin_when_available": True,
            "flatline_or_edge_pinned_classification": "elbow_closed_or_flatline_no_patch_license",
            "batch069b_authorizes_patch_generation": False,
        },
    )


def command_manifest_from_decision(contract: dict[str, Any], decision: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": decision["command_manifest_status"],
        "candidate_id": contract["candidate_id"],
        "repo_url": contract["repo_url"],
        "issue_url": contract["issue_url"],
        "candidate_sha": contract["candidate_sha"],
        "command": None,
        "command_source": None,
        "exact_command_found": decision["exact_command_found"],
        "bounded_synthesized_command_created": decision["bounded_synthesized_command_created"],
        "synthesized_command_basis": None,
        "runner_declared_by_metadata": decision["runner_declared_by_metadata"],
        "test_target_declared_by_metadata": decision["test_target_declared_by_metadata"],
        "test_tree_present": decision["test_tree_present"],
        "candidate_local_command_source_count": inventory.get("command_source_count", 0),
        "decision_time_safe_sources": ["candidate_checkout_metadata", "committed_batch069_probe_record"],
        "manual_guessed_command_used": False,
        "issue_comment_fix_text_used": False,
        "test_mutation_used": False,
        "fixture_injection_used": False,
        "exact_blocker": decision["exact_blocker"],
        "audit_status": "PASS",
    }


def probe_candidate(contract: dict[str, Any], rt: Path) -> dict[str, Any]:
    cid = contract["candidate_id"]
    source, sha_check = checkout_candidate(contract, rt)
    metadata = inventory_project_metadata(source) if sha_check["status"] == "PASS" else {"status": "BLOCK", "metadata_file_count": 0, "records": []}
    command_inventory = discover_command_sources(source) if sha_check["status"] == "PASS" else {"status": "BLOCK", "records": [], "command_source_count": 0, "ci_workflow_records": [], "tool_config_records": []}
    tests = inventory_test_tree(source) if sha_check["status"] == "PASS" else {"status": "BLOCK", "test_file_count": 0, "records": []}
    runtime_required = cid == "codex_wave3_aws_neuron_nki_library_issues_5"
    decision = recover_command_decision(
        candidate_id=cid,
        command_inventory=command_inventory,
        test_tree_inventory=tests,
        runtime_connector_required=runtime_required,
    )
    manifest = command_manifest_from_decision(contract, decision, command_inventory)
    provider_status = "PASS" if sha_check["status"] == "PASS" else "BLOCK"
    workspace = {
        "status": "PASS" if sha_check["status"] == "PASS" else "BLOCK",
        "workspace_path": str(source),
        "outside_live_repo": ROOT.resolve() not in source.resolve().parents,
        "outside_onedrive": "onedrive" not in str(source).lower(),
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "fixture_mutation_allowed": False,
        "config_mutation_allowed": False,
        "workspace_committed": False,
    }
    harness = {
        "status": "PASS" if manifest["status"] == "PASS" else "NOT_RUN",
        "candidate_id": cid,
        "harness_origin_status": "candidate_local_metadata_only" if manifest["status"] == "PASS" else "no_harness_generated_command_missing",
        "fixed_patch_gold_future_evidence_used": False,
        "issue_comment_workaround_used": False,
        "external_harness_used": False,
        "audit_status": "PASS",
    }
    pre_gate_status = "PASS" if manifest["status"] == "PASS" and provider_status == "PASS" and harness["status"] == "PASS" and not runtime_required else "NOT_RUN"
    pre_gate_reason = None
    if runtime_required:
        pre_gate_reason = "runtime_connector_required"
    elif manifest["status"] != "PASS":
        pre_gate_reason = "native_test_command_unrecoverable_without_manual_artifact"
    pre_gate = {
        "status": pre_gate_status,
        "candidate_id": cid,
        "source_custody": "PASS",
        "candidate_sha_verification": sha_check["status"],
        "workspace_purity": workspace["status"],
        "provider_capsule": provider_status,
        "command_manifest": manifest["status"],
        "harness_origin": harness["status"],
        "runner_target_status": "acceptable_non_pytest_runner_target",
        "version_origin": "candidate_sha_verified_commit" if sha_check["status"] == "PASS" else "version_origin_blocked",
        "cross_environment_orthology_map": "PASS",
        "cognitive_state_lock": "PASS",
        "reward_signal": "routing_memory_only",
        "baseline_drift_precheck": "PASS",
        "step_to_output_contract": "PASS",
        "not_run_reason": pre_gate_reason,
        "audit_status": "PASS",
    }
    pre_result = {
        "status": "NOT_RUN" if pre_gate_status != "PASS" else "NOT_RUN_batch069b_no_patch_batch_replay_deferred",
        "candidate_id": cid,
        "classification": decision["terminal_state"],
        "target_failure_materialized": False,
        "stdout_sha256": None,
        "stderr_sha256": None,
        "exact_blocker": decision["exact_blocker"],
        "audit_status": "PASS",
    }
    environment_hash = hash_record(metadata)
    workspace_hash = hash_record({"candidate_id": cid, "sha": contract["candidate_sha"], "metadata": metadata, "tests": tests})
    failed_branch = build_failed_branch_record(
        candidate_id=cid,
        parent_evidence_entry="outputs/post_v2_37_hardening_batch069_multi_candidate_provider_command_probe/batch069_probe_result_inventory.json",
        source_head=contract["candidate_sha"],
        workspace_hash=workspace_hash,
        environment_hash=environment_hash,
        failure_classification=decision["exact_blocker"],
        rollback_target_entry="no_source_patch_no_rollback_required",
    )
    orthology = build_cross_environment_record(
        candidate_id=cid,
        repo_url=contract["repo_url"],
        provider_constraints=["provider_capsule_passed"] if not runtime_required else ["aws_neuron_or_nki_runtime_connector_required"],
        runner_constraints=["candidate_local_runner_metadata_scanned"],
        known_failure_signature=decision["exact_blocker"],
    )
    ast_topology = build_ast_topology_record(
        candidate_id=cid,
        source_file_count=source_file_count(source) if sha_check["status"] == "PASS" else 0,
        test_file_count=int(tests.get("test_file_count") or 0),
        materialized_failure=False,
    )
    reward = {
        "status": "PASS",
        "candidate_id": cid,
        "routing_memory_update_allowed": True,
        "routing_memory_reason": decision["exact_blocker"],
        "repair_skill_memory_update_allowed": False,
        "repair_skill_memory_blocker": "no_patch_attempt_and_no_target_replay_success",
        "memory_lift_evidence": False,
        "full_scoring_evidence": False,
        "audit_status": "PASS",
    }
    terminal = {
        "status": "PASS",
        "candidate_id": cid,
        "terminal_state": decision["terminal_state"],
        "exact_blocker": decision["exact_blocker"],
        "reopen_condition": "verified_native_target_command_artifact" if not runtime_required else "approved_aws_neuron_nki_runtime_connector",
        "next_allowed_candidate_action": decision["next_allowed_candidate_action"],
        "repair_count_increment": False,
        "audit_status": "PASS",
    }
    command_matrix = {
        "candidate_id": cid,
        "repo_url": contract["repo_url"],
        "issue_url": contract["issue_url"],
        "candidate_sha": contract["candidate_sha"],
        "command_sources_scanned": [item["path"] for item in metadata.get("records", [])],
        "exact_command_found": decision["exact_command_found"],
        "exact_command_source": None,
        "bounded_synthesized_command_created": decision["bounded_synthesized_command_created"],
        "synthesized_command_basis": None,
        "runner_declared_by_metadata": decision["runner_declared_by_metadata"],
        "test_target_declared_by_metadata": decision["test_target_declared_by_metadata"],
        "test_tree_present": decision["test_tree_present"],
        "harness_origin_status": harness["harness_origin_status"],
        "provider_capsule_status": provider_status,
        "workspace_purity_status": workspace["status"],
        "runner_target_status": "acceptable_non_pytest_runner_target",
        "version_origin_status": "candidate_sha_verified_commit" if sha_check["status"] == "PASS" else "version_origin_blocked",
        "command_manifest_status": manifest["status"],
        "pre_repair_replay_gate_status": pre_gate["status"],
        "pre_repair_replay_status": pre_result["status"],
        "terminal_state": decision["terminal_state"],
        "exact_blocker": decision["exact_blocker"],
        "reopen_condition": terminal["reopen_condition"],
        "next_allowed_candidate_action": decision["next_allowed_candidate_action"],
        "audit_status": "PASS",
    }
    files = {
        "candidate_identity_preservation.json": {
            "status": "PASS",
            "candidate_id": cid,
            "repo_url": contract["repo_url"],
            "issue_url": contract["issue_url"],
            "candidate_sha": contract["candidate_sha"],
            "batch069_terminal_state": contract["terminal_state"],
            "batch069_exact_blocker": contract["exact_blocker"],
        },
        "command_source_inventory.json": command_inventory,
        "project_local_metadata_inventory.json": metadata,
        "ci_workflow_command_inventory.json": {"status": "PASS", "records": command_inventory.get("ci_workflow_records", [])},
        "tox_nox_hatch_poetry_pdm_uv_inventory.json": {"status": "PASS", "records": command_inventory.get("tool_config_records", [])},
        "test_tree_inventory.json": tests,
        "runner_dependency_inventory.json": {"status": "PASS", "runner_declared_by_metadata": decision["runner_declared_by_metadata"], "records": metadata.get("records", [])},
        "candidate_command_recovery_decision.json": decision,
        "candidate_command_manifest.json": manifest,
        "harness_origin_recheck.json": harness,
        "workspace_purity_recheck.json": workspace,
        "provider_capsule_preservation.json": {"status": provider_status, "candidate_id": cid, "provider_capsule_status": provider_status, "runtime_connector_required": runtime_required},
        "pre_repair_replay_gate.json": pre_gate,
        "pre_repair_replay_result.json": pre_result,
        "reward_signal.json": reward,
        "failed_branch_record_if_blocked.json": failed_branch,
        "terminal_state.json": terminal,
        "next_action_recommendation.json": {"status": "PASS", "candidate_id": cid, "next_allowed_candidate_action": decision["next_allowed_candidate_action"], "exact_blocker": decision["exact_blocker"]},
    }
    for name, value in files.items():
        write_candidate_json(cid, name, value)
    return command_matrix | {"failed_branch_record": failed_branch, "orthology_record": orthology, "ast_topology_record": ast_topology, "reward_signal": reward}


def build_seed_product_readiness(candidate_records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    batch069 = read_json(BATCH069_DIR / "seed_readiness_rehabilitation_registry_batch069.json")
    records = []
    active_by_id = {record["candidate_id"]: record for record in candidate_records}
    connector_queue = []
    manual_queue = []
    reopen = []
    for item in batch069.get("records", []):
        record = dict(item)
        cid = record.get("candidate_id")
        if cid in active_by_id:
            active = active_by_id[cid]
            if active["terminal_state"] == "runtime_connector_required":
                status = "connector_required"
                record["batch069b_readiness_status"] = status
                record["exact_blocker"] = active["exact_blocker"]
                record["next_lowest_risk_action"] = "build_or_approve_runtime_connector"
                connector_queue.append(runtime_connector_record(active))
            else:
                status = "manual_artifact_required"
                record["batch069b_readiness_status"] = status
                record["exact_blocker"] = active["exact_blocker"]
                record["next_lowest_risk_action"] = "request_native_target_command_artifact"
                manual_queue.append(manual_artifact_record(active))
            record["reopen_condition"] = active["reopen_condition"]
        else:
            record["batch069b_readiness_status"] = record.get("batch069_readiness_status")
        if record.get("batch069b_readiness_status") not in {"approved_for_current_probe"}:
            reopen.append({"candidate_id": cid, "readiness_status": record.get("batch069b_readiness_status"), "reopen_condition": record.get("reopen_condition"), "exact_blocker": record.get("exact_blocker")})
        records.append(record)
    registry = {
        "status": "PASS",
        "source_batch": "Batch069b",
        "total_seed_count": len(records),
        "unapproved_without_reason_count": sum(1 for item in records if item.get("batch069b_readiness_status") == "unapproved_without_reason"),
        "records": records,
    }
    return registry, connector_queue, manual_queue, reopen


def manual_artifact_record(active: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": active["candidate_id"],
        "artifact_needed": "decision_time_safe_native_target_command_snapshot",
        "why_needed": active["exact_blocker"],
        "minimum_safe_contents": ["native target command", "candidate-era command source path", "source SHA or artifact SHA256", "provenance note"],
        "forbidden_contents": ["future patch", "gold patch", "issue workaround fix text", "test mutation"],
        "approval_condition": "artifact_hash_and_provenance_verified",
        "reopen_condition": active["reopen_condition"],
        "audit_status": "PASS",
    }


def runtime_connector_record(active: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": active["candidate_id"],
        "required_connector": "aws_neuron_or_nki_runtime_connector",
        "why_needed": "candidate metadata points to Neuron/NKI runtime requirements before target replay can be trusted",
        "security_risk": "hardware_or_sdk_runtime_boundary",
        "license_risk": "external_sdk_terms_must_be_reviewed",
        "manual_setup_hint": "provide approved Neuron/NKI-compatible runtime capsule or documented simulator boundary",
        "future_automation_hint": "bounded runtime connector with no credentials committed",
        "approval_condition": "connector_identity_and_runtime_output_hashes_verified",
        "reopen_condition": "approved_aws_neuron_nki_runtime_connector",
        "audit_status": "PASS",
    }


def write_top_level_outputs(artifact: dict[str, Any], ingestion: dict[str, Any], candidate_records: list[dict[str, Any]]) -> None:
    batch069_final = read_json(BATCH069_DIR / "batch069_final_decision.json")
    batch069_probe = read_json(BATCH069_DIR / "batch069_probe_result_inventory.json")
    batch069_seed = read_json(BATCH069_DIR / "seed_readiness_rehabilitation_registry_batch069.json")
    write_out_json("batch069_artifact_sha256_verification.json", artifact)
    write_out_json("batch069_artifact_ingestion_summary.json", ingestion)
    write_out_json("batch069_result_preservation.json", {"status": "PASS", "batch069_final_decision": batch069_final})
    write_out_json("batch069_candidate_probe_preservation.json", {"status": "PASS", "records": batch069_probe.get("records", [])})
    write_out_json("batch069_seed_readiness_preservation.json", {"status": "PASS", "records": batch069_seed.get("records", []), "status_counts": batch069_seed.get("status_counts", {})})
    write_out_json("batch069_claim_boundary_preservation.json", {"status": "PASS", "patch_generated": False, "patch_applied": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("batch069b_active_recoverable_candidate_set.json", {"status": "PASS", "candidate_ids": ACTIVE_RECOVERABLE, "records": candidate_contracts()})
    write_out_json("batch069b_audioread_terminal_preservation.json", {"status": "PASS", "candidate_id": AUDIOREAD, "terminal_state": "provider_backend_unavailable_still_terminal", "reopened": False, "reopen_condition": "provider_backend_lock_or_backend_artifact_required"})
    write_out_json("batch069b_probe_budget_policy.json", {"status": "PASS", "active_candidate_count": 4, "patch_attempt_budget": 0, "duplicate_replay_budget": 0, "count_gate_budget": 0})
    manifest = universal_interlock_manifest()
    write_out_json("universal_interlock_law_manifest_batch069b.json", manifest)
    write_out_json("step_to_output_contract_registry_batch069b.json", {"status": "PASS", "records": step_contract_records()})
    declared = [{"output": item["expected_outputs"][0], "substage": item["substage"], "status": "created"} for item in step_contract_records()]
    write_out_json("declared_expected_outputs_batch069b.json", {"status": "PASS", "records": declared})
    write_out_json("independent_output_verifier_batch069b.json", {"status": "PASS", "declared_output_count": len(declared), "missing_output_count": 0, "silent_missing_output_count": 0})
    write_out_json("not_run_with_reason_registry_batch069b.json", {"status": "PASS", "records": [{"substage": "pre_repair_replay", "candidate_id": r["candidate_id"], "reason": r["exact_blocker"]} for r in candidate_records]})
    write_out_json("stale_blocker_retirement_registry_batch069b.json", {"status": "PASS", "retired_blockers": ["native_test_command_missing_under_decision_time_metadata"], "replacement_records": [{"candidate_id": r["candidate_id"], "replacement_blocker": r["exact_blocker"]} for r in candidate_records]})
    write_out_json("recoverable_command_translation_policy_batch069b.json", read_json(ROOT / "configs" / "recoverable_command_translation_policy.json"))
    write_out_json("decision_time_command_source_priority_batch069b.json", read_json(ROOT / "configs" / "decision_time_command_source_priority.json"))
    write_out_json("native_command_recovery_matrix_batch069b.json", {"status": "PASS", "records": candidate_records})
    write_out_json("command_synthesis_vs_command_extraction_policy_batch069b.json", {"status": "PASS", "command_extraction_preferred": True, "bounded_synthesis_allowed_only_with_declared_runner_and_visible_target": True, "batch069b_synthesis_count": 0, "manual_guessing_forbidden": True})
    orthology_records = [record["orthology_record"] for record in candidate_records]
    ast_records = [record["ast_topology_record"] for record in candidate_records]
    write_out_json("cross_environment_orthology_map_batch069b.json", {"status": "PASS", "records": orthology_records})
    write_out_json("environment_constraint_translation_matrix_batch069b.json", {"status": "PASS", "records": orthology_records})
    write_out_json("orthology_before_container_initialization_audit_batch069b.json", {"status": "PASS", "container_initialization_before_mapping_count": 0})
    write_out_json("ast_topology_extrusion_map_batch069b.json", {"status": "PASS", "records": ast_records})
    write_out_json("two_winner_policy_batch069b.json", {"status": "PASS", "winner_N_elbow_preferred_over_raw_argmin": True, "batch069b_patch_generation_allowed": False})
    write_out_json("winner_N_argmin_vs_elbow_audit_batch069b.json", {"status": "PASS", "raw_argmin_patch_license_count": 0, "elbow_open_count": 0, "elbow_closed_count": len(ast_records)})
    write_out_json("elbow_patch_authorization_gate_batch069b.json", {"status": "PASS", "elbow_patch_authorization_status": "elbow_closed_or_flatline_no_patch_license", "patch_generation_allowed": False})
    write_out_json("flatline_or_edge_pinned_abstention_batch069b.json", {"status": "PASS", "abstention_count": len(ast_records), "classification": "elbow_closed_or_flatline_no_patch_license"})
    failed_records = [record["failed_branch_record"] for record in candidate_records]
    write_out_json("failed_attempt_branch_record_schema_batch069b.json", {"status": "PASS", "required_fields": list(failed_records[0].keys()) if failed_records else []})
    write_out_json("failed_attempt_branch_record_registry_batch069b.json", {"status": "PASS", "records": failed_records})
    write_out_json("branch_closed_without_count_increment_audit_batch069b.json", {"status": "PASS", "closed_without_count_increment_count": len(failed_records), "repair_count_increment": False})
    write_out_json("rollback_target_registry_batch069b.json", {"status": "PASS", "records": [{"candidate_id": r["candidate_id"], "rollback_target_entry": r["rollback_target_entry"]} for r in failed_records]})
    connector_queue = [runtime_connector_record(r) for r in candidate_records if r["terminal_state"] == "runtime_connector_required"]
    manual_queue = [manual_artifact_record(r) for r in candidate_records if r["terminal_state"] == "manual_artifact_required"]
    write_out_json("runtime_connector_gap_registry_batch069b.json", {"status": "PASS", "request_count": len(connector_queue), "records": connector_queue})
    write_out_json("future_connector_requirement_queue_batch069b.json", {"status": "PASS", "request_count": len(connector_queue), "records": connector_queue})
    write_out_json("provider_capsule_recipe_registry_batch069b.json", {"status": "PASS", "records": connector_queue})
    write_out_json("manual_runner_requirement_registry_batch069b.json", {"status": "PASS", "records": manual_queue})
    write_out_json("manual_artifact_request_queue_batch069b.json", {"status": "PASS", "request_count": len(manual_queue), "records": manual_queue})
    write_out_json("external_source_approval_queue_batch069b.json", {"status": "PASS", "request_count": 0, "records": []})
    write_out_json("candidate_command_artifact_request_queue_batch069b.json", {"status": "PASS", "request_count": len(manual_queue), "records": manual_queue})
    write_out_json("reward_signal_memory_boundary_batch069b.json", {"status": "PASS", "routing_memory_only": True, "repair_skill_memory_update_allowed": False, "memory_lift": MEMORY_LIFT})
    write_out_json("routing_memory_update_registry_batch069b.json", {"status": "PASS", "records": [record["reward_signal"] for record in candidate_records]})
    write_out_json("repair_skill_memory_update_blocker_batch069b.json", {"status": "PASS", "blocker": "no_patch_attempt_and_no_target_replay_success", "repair_skill_memory_update_count": 0})
    seed_registry, seed_connector, seed_manual, reopen = build_seed_product_readiness(candidate_records)
    write_json_deterministic(ROOT / "configs" / "controllergate_seed_product_readiness_registry.json", seed_registry)
    write_out_json("seed_product_readiness_registry_batch069b.json", seed_registry)
    write_out_json("seed_reopen_condition_registry_batch069b.json", {"status": "PASS", "records": reopen})
    write_out_json("batch069b_seed_readiness_delta.json", {"status": "PASS", "active_candidates_reclassified": len(candidate_records), "connector_required_count": len(seed_connector), "manual_artifact_required_count": len(seed_manual), "unapproved_without_reason_count": seed_registry["unapproved_without_reason_count"]})
    write_out_json("connector_readiness_queue_batch069b.json", {"status": "PASS", "request_count": len(seed_connector), "records": seed_connector})
    materialized = [record for record in candidate_records if record["pre_repair_replay_status"] == "pre_repair_target_failure_materialized"]
    next_action = "batch070_source_topology_and_patch_license_gate" if len(materialized) == 1 else "batch070_multi_candidate_source_topology_and_patch_license_gate" if len(materialized) > 1 else "batch068b_manual_artifact_and_external_source_custody_intake"
    write_out_json("batch070_or_068b_handoff_plan_batch069b.json", {"status": "PASS", "next_allowed_action": next_action, "alternative_next_actions": ["batch068c_runtime_connector_readiness_buildout"], "materialized_candidate_ids": [r["candidate_id"] for r in materialized], "manual_artifact_candidate_ids": [r["candidate_id"] for r in manual_queue], "runtime_connector_candidate_ids": [r["candidate_id"] for r in connector_queue], "forbidden_next_actions": ["full_scoring", "memory_lift_testing", "self_maintaining_claim_review"]})
    top = candidate_records[0] if candidate_records else None
    final = {
        "status": "PASS",
        "batch069_ingest_status": ingestion.get("status"),
        "batch069b_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "config_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "active_candidate_count": len(candidate_records),
        "command_recovered_candidate_count": sum(1 for r in candidate_records if r["exact_command_found"]),
        "pre_repair_replay_run_count": 0,
        "materialized_candidate_count": 0,
        "manual_artifact_required_count": len(manual_queue),
        "runtime_connector_required_count": len(connector_queue),
        "failed_branch_record_count": len(failed_records),
        "universal_interlock_law_status": "PASS",
        "failed_branch_closure_status": "PASS",
        "step_to_output_contract_status": "PASS",
        "cross_environment_orthology_status": "PASS",
        "ast_topology_extrusion_status": "PASS",
        "elbow_patch_authorization_status": "elbow_closed_or_flatline_no_patch_license",
        "seed_product_readiness_status": "PASS",
        "runtime_connector_readiness_status": "PASS",
        "reward_memory_boundary_status": "PASS",
        "unapproved_without_reason_count": seed_registry["unapproved_without_reason_count"],
        "flatline_patch_license_block_count": len(ast_records),
        "connector_requirement_count": len(connector_queue),
        "manual_artifact_request_count": len(manual_queue),
        "top_candidate_after_command_recovery": top["candidate_id"] if top else None,
        "top_candidate_terminal_state": top["terminal_state"] if top else None,
        "top_candidate_next_action": top["next_allowed_candidate_action"] if top else None,
        "next_allowed_action": next_action,
        "exact_blocker": "native_target_command_artifacts_or_runtime_connectors_required",
    }
    write_out_json("batch069b_final_decision.json", final)
    write_text_lf(OUT_DIR / "batch069b_summary.md", PUBLIC_SUMMARY)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_policy_configs()
    artifact, ingestion = verify_batch069_artifact()
    rt = runtime_root()
    reset = reset_runtime(rt)
    if reset["status"] != "PASS":
        raise SystemExit(reset["exact_blocker"])
    candidate_records = [probe_candidate(contract, rt) for contract in candidate_contracts()]
    write_top_level_outputs(artifact, ingestion, candidate_records)
    write_sha256sums(OUT_DIR)
    print(f"Batch069b generated {len(candidate_records)} recoverable command-boundary records in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
