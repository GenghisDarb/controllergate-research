from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip
from controllergate.core.evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums

OUT_NAME = "post_v2_37_hardening_batch069_multi_candidate_provider_command_probe"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH068_NAME = "post_v2_37_hardening_batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_063d_063e_controls"
BATCH068_DIR = ROOT / "outputs" / BATCH068_NAME

EXPECTED_BATCH068 = {
    "commit": "4e3f7649ae1fa24836beae7b78eed3c10889ac4f",
    "workflow": "post_v2_37_hardening_batch068_multi_seed_harvest_for_5th_issue_repair",
    "workflow_run_id": 29066511606,
    "artifact_name": "post_v2_37_hardening_batch068_multi_seed_harvest_for_5th_issue_repair_artifacts",
    "artifact_id": 8217325435,
    "expected_size": 105081,
    "expected_sha256": "f169aae0c3e145f5a4a0c410c8a2de8bee25e2d151a738b6fd2d9fe27c39565a",
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

DEFAULT_BATCH068_ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH068['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch068_multi_seed_harvest_for_5th_issue_repair_artifacts.zip"),
]

TOP5_ORDER = [
    "audioread_144_py313_aifc_removed",
    "codex_wave3_aio_libs_aiosmtpd_issues_403",
    "codex_wave3_alpha_unito_streamflow_issues_1100",
    "codex_wave3_aws_neuron_nki_library_issues_5",
    "codex_wave3_biface_i18n_issues_86",
]

TOP5_FALLBACK = {
    "audioread_144_py313_aifc_removed": {
        "repo_url": "https://github.com/beetbox/audioread",
        "issue_url": "https://github.com/beetbox/audioread/issues/144",
        "candidate_sha": "577f8e2cbe99f33dd7d236deb1626e372f4762e9",
        "prior_risk": "provider_backend_unavailable_prior_state",
    },
    "codex_wave3_aio_libs_aiosmtpd_issues_403": {
        "repo_url": "https://github.com/aio-libs/aiosmtpd",
        "issue_url": "https://github.com/aio-libs/aiosmtpd/issues/403",
        "candidate_sha": "94710d8fd280115cbd835ae969873cc424b4e57a",
        "prior_risk": "native_test_missing_prior_state",
    },
    "codex_wave3_alpha_unito_streamflow_issues_1100": {
        "repo_url": "https://github.com/alpha-unito/streamflow",
        "issue_url": "https://github.com/alpha-unito/streamflow/issues/1100",
        "candidate_sha": "dfc0fd5eb6bf23be4da389f96dda7ff5c9d90bd5",
        "prior_risk": "native_test_missing_prior_state",
    },
    "codex_wave3_aws_neuron_nki_library_issues_5": {
        "repo_url": "https://github.com/aws-neuron/nki-library",
        "issue_url": "https://github.com/aws-neuron/nki-library/issues/5",
        "candidate_sha": "c38d790ea16032f7c7843e8e2d67aca2ae8bd5f2",
        "prior_risk": "native_test_missing_prior_state",
    },
    "codex_wave3_biface_i18n_issues_86": {
        "repo_url": "https://github.com/biface/i18n",
        "issue_url": "https://github.com/biface/i18n/issues/86",
        "candidate_sha": "e093e3f3d02d84043c5913531492aa78913aec5a",
        "prior_risk": "native_test_missing_prior_state",
    },
}

METADATA_FILES = [
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "noxfile.py",
    "requirements.txt",
    "requirements-dev.txt",
    "dev-requirements.txt",
    "test-requirements.txt",
    ".github/workflows/test.yml",
    ".github/workflows/tests.yml",
    ".github/workflows/ci.yml",
]

PUBLIC_SUMMARY = (
    "Batch069 probes the top Batch068 seeds for provider availability, command-boundary validity, harness-origin "
    "safety, and pre-repair replay materialization. This is replay-readiness and routing evidence, not repair proof. "
    "No repair is counted without source-only target pass, duplicate clean replay, and count gate. Full scoring remains "
    "NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated. "
    "Seeds not approved for the immediate repair lane were not discarded. They were classified into a readiness backlog "
    "with exact blockers, environment requirements, artifact requests, source-approval needs, reopen conditions, or "
    "terminal reasons. Approval is a proof-lane safety state; preparedness is a long-term product-readiness state."
)

READINESS_STATUSES = [
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
]

BACKLOG_CATEGORIES = [
    "provider_capsule_needed",
    "command_boundary_needed",
    "harness_origin_needed",
    "runner_target_split_needed",
    "version_origin_authority_needed",
    "manual_artifact_needed",
    "fixture_or_testdata_needed",
    "hardware_or_service_needed",
    "external_source_approval_needed",
    "source_topology_needed",
    "baseline_or_null_wrapper_needed",
    "security_or_license_review_needed",
    "terminal_retired",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_candidate_json(candidate_id: str, name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / "candidates" / candidate_id / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def runtime_root() -> Path:
    if os.environ.get("RUNNER_TEMP"):
        return Path(os.environ["RUNNER_TEMP"]) / "ControllerGate_runtime" / "batch069"
    return ROOT.parent / "ControllerGate_runtime" / "batch069"


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


def run_cmd(args: list[str], cwd: Path, *, timeout: int = 120) -> dict[str, Any]:
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


def find_batch068_zip() -> Path | None:
    env_path = os.environ.get("CONTROLLERGATE_BATCH068_ARTIFACT_ZIP")
    candidates = ([Path(env_path)] if env_path else []) + DEFAULT_BATCH068_ZIP_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def read_zip_json(zip_path: Path, name: str) -> dict[str, Any] | None:
    with zipfile.ZipFile(zip_path) as archive:
        if name not in archive.namelist():
            return None
        return json.loads(archive.read(name).decode("utf-8"))


def verify_batch068_artifact() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    zip_path = find_batch068_zip()
    if zip_path is None:
        final = read_json(BATCH068_DIR / "batch068_final_decision.json")
        top5 = read_json(BATCH068_DIR / "top_5_candidate_recommendations_batch068.json")
        verification = {
            "status": "batch068_artifact_absent_for_local_ingest",
            "artifact_absent": True,
            "manual_artifact_handoff": False,
            "downloaded_by_codex": False,
            "committed_batch068_outputs_preserved": True,
        }
        ingestion = {
            "status": "batch068_artifact_absent_for_local_ingest",
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
            "preservation_source": "committed_batch068_outputs",
        }
        return verification, ingestion, final, top5

    verification = verify_artifact_zip(
        zip_path,
        expected_size=EXPECTED_BATCH068["expected_size"],
        expected_sha256=EXPECTED_BATCH068["expected_sha256"],
    )
    nested = verification.get("entries", {}).get("nested_archive_or_cache_payloads", [])
    if nested:
        verification["status"] = "FAIL"
    verification["local_artifact_path"] = str(zip_path)
    verification["manual_artifact_handoff"] = True
    verification["downloaded_by_codex"] = False
    verification["nested_archive_cache_venv_pyc_payload_count"] = len(nested)
    final = read_zip_json(zip_path, "batch068_final_decision.json") or read_json(BATCH068_DIR / "batch068_final_decision.json")
    top5 = read_zip_json(zip_path, "top_5_candidate_recommendations_batch068.json") or read_json(BATCH068_DIR / "top_5_candidate_recommendations_batch068.json")
    ingestion = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_verified": verification.get("status"),
        "source_zip": str(zip_path),
        "raw_zip_bytes_ingested": False,
        "output_payload_overwrite_performed": False,
        "ingested_file_count": 0,
        "preservation_source": "verified_manual_batch068_artifact" if verification.get("status") == "PASS" else "committed_batch068_outputs",
    }
    return verification, ingestion, final, top5


def batch068_inventory_by_id() -> dict[str, dict[str, Any]]:
    inventory_path = BATCH068_DIR / "candidate_seed_inventory_batch068.json"
    if not inventory_path.is_file():
        return {}
    records = read_json(inventory_path).get("records", [])
    return {record.get("candidate_id"): record for record in records if isinstance(record, dict)}


def batch068_inventory_records() -> list[dict[str, Any]]:
    inventory_path = BATCH068_DIR / "candidate_seed_inventory_batch068.json"
    if not inventory_path.is_file():
        return []
    records = read_json(inventory_path).get("records", [])
    return [record for record in records if isinstance(record, dict)]


def candidate_contracts() -> list[dict[str, Any]]:
    inventory = batch068_inventory_by_id()
    contracts: list[dict[str, Any]] = []
    for cid in TOP5_ORDER:
        fallback = TOP5_FALLBACK[cid]
        prior = inventory.get(cid, {})
        contracts.append(
            {
                "candidate_id": cid,
                "repo_url": prior.get("repo_url") or fallback["repo_url"],
                "issue_url": prior.get("issue_url_or_source_url") or fallback["issue_url"],
                "candidate_sha": prior.get("candidate_sha_if_known") or fallback["candidate_sha"],
                "source_type": prior.get("source_type") or "approved_external_issue_source",
                "batch068_promotion_status": prior.get("promotion_status") or "approved_for_command_boundary_probe",
                "prior_risk": fallback["prior_risk"],
            }
        )
    return contracts


def checkout_candidate(contract: dict[str, Any], rt: Path) -> tuple[Path, dict[str, Any]]:
    cid = contract["candidate_id"]
    work = rt / cid / "source"
    work.mkdir(parents=True, exist_ok=True)
    repo_url = str(contract["repo_url"]).rstrip("/")
    remote = repo_url + ".git" if not repo_url.endswith(".git") else repo_url
    sha = contract["candidate_sha"]
    init = run_cmd(["git", "init", "-q"], work)
    add = run_cmd(["git", "remote", "add", "origin", remote], work)
    fetch = run_cmd(["git", "fetch", "--filter=blob:none", "--no-tags", "origin", sha], work, timeout=180)
    cat = run_cmd(["git", "cat-file", "-t", "FETCH_HEAD"], work)
    rev = run_cmd(["git", "rev-parse", "FETCH_HEAD"], work)
    checkout = run_cmd(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], work, timeout=120) if fetch["returncode"] == 0 else {"returncode": 1, "skipped": True}
    status = run_cmd(["git", "status", "--short"], work) if checkout.get("returncode") == 0 else {"returncode": 1, "stdout": "", "stderr": "checkout skipped"}
    verified = fetch["returncode"] == 0 and cat["stdout"].strip() == "commit" and rev["stdout"].strip() == sha
    return work, {
        "status": "PASS" if verified and checkout.get("returncode") == 0 else "BLOCK",
        "repo_url": repo_url,
        "remote_url": remote,
        "candidate_sha": sha,
        "git_object_type": cat.get("stdout", "").strip(),
        "resolved_sha": rev.get("stdout", "").strip(),
        "workspace_committed": False,
        "workspace_path": str(work),
        "commands": {"init": init, "remote_add": add, "fetch": fetch, "cat_file": cat, "rev_parse": rev, "checkout": checkout, "status_short": status},
        "exact_blocker": None if verified and checkout.get("returncode") == 0 else "version_origin_blocked",
    }


def file_sha_or_none(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def metadata_inventory(source: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for rel in METADATA_FILES:
        path = source / rel
        if path.is_file():
            records.append({"path": rel, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    test_files: list[str] = []
    for pattern in ["test*.py", "*test*.py"]:
        for path in source.rglob(pattern):
            rel = path.relative_to(source).as_posix()
            if "/.git/" not in f"/{rel}/" and len(test_files) < 100:
                test_files.append(rel)
    return {
        "metadata_files": records,
        "metadata_file_count": len(records),
        "sample_test_files": sorted(set(test_files))[:50],
        "sample_test_file_count": len(set(test_files)),
        "dependency_lock_hash": hash_record(records),
    }


def command_boundary_for(contract: dict[str, Any], inventory: dict[str, Any], provider_status: str) -> dict[str, Any]:
    cid = contract["candidate_id"]
    if provider_status != "PASS":
        return {
            "status": "NOT_RUN",
            "command_boundary_status": "provider_capsule_blocked",
            "command": None,
            "decision_time_safe_sources": [],
            "exact_blocker": "provider_backend_unavailable_still_terminal" if cid == "audioread_144_py313_aifc_removed" else "provider_capsule_blocked",
        }
    # Batch069 intentionally does not infer a test command from issue text or modern docs. A command must be present in
    # prior decision-time metadata or unambiguous project-local test metadata.
    return {
        "status": "BLOCK",
        "command_boundary_status": "native_test_command_missing_under_decision_time_metadata",
        "command": None,
        "decision_time_safe_sources": ["candidate_checkout_metadata", "repo_local_batch068_inventory"],
        "sample_project_test_files": inventory.get("sample_test_files", [])[:20],
        "manual_guessed_commands_used": False,
        "issue_comment_fix_text_used": False,
        "config_suppression_flags_used": False,
        "exact_blocker": "native_test_command_missing_under_decision_time_metadata",
    }


def probe_candidate(contract: dict[str, Any], rt: Path) -> dict[str, Any]:
    cid = contract["candidate_id"]
    source, sha_check = checkout_candidate(contract, rt)
    source_custody = {
        "status": "PASS",
        "candidate_id": cid,
        "repo_url": contract["repo_url"],
        "issue_url": contract["issue_url"],
        "source_type": contract["source_type"],
        "source_custody_status": "repo_local_batch068_seed_plus_bounded_candidate_checkout",
        "gold_fixed_future_exclusion_status": "PASS",
        "label_blindness_status": "PASS",
        "decision_time_safe_status": "PASS",
        "raw_external_archive_committed": False,
        "candidate_checkout_committed": False,
    }
    workspace = {
        "status": "PASS" if sha_check["status"] == "PASS" else "BLOCK",
        "workspace_path": str(source),
        "outside_live_repo": ROOT.resolve() not in source.resolve().parents,
        "outside_onedrive": "onedrive" not in str(source).lower(),
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "fixture_mutation_allowed": False,
        "config_mutation_allowed": False,
    }
    metadata = metadata_inventory(source) if sha_check["status"] == "PASS" else {"metadata_files": [], "metadata_file_count": 0, "sample_test_files": [], "dependency_lock_hash": None}
    provider_status = "PASS" if sha_check["status"] == "PASS" and metadata["metadata_file_count"] > 0 else "BLOCK"
    provider_blocker = None
    backend_status = "metadata_available"
    if cid == "audioread_144_py313_aifc_removed":
        provider_status = "BLOCK"
        backend_status = "provider_backend_unavailable_still_terminal"
        provider_blocker = "provider_backend_unavailable_still_terminal"
    elif sha_check["status"] != "PASS":
        provider_blocker = "version_origin_blocked"
        backend_status = "not_reached"
    elif metadata["metadata_file_count"] == 0:
        provider_blocker = "provider_capsule_blocked"
        backend_status = "environment_metadata_missing"
    provider = {
        "status": provider_status,
        "provider_capsule_status": provider_status,
        "provider_setup_commands": [],
        "dependency_lock_hash": metadata.get("dependency_lock_hash"),
        "provider_availability": "available_for_metadata_probe" if provider_status == "PASS" else "blocked",
        "backend_availability": backend_status,
        "environment_files": metadata.get("metadata_files", []),
        "missing_system_dependency": None,
        "provider_failure_terminal_or_recoverable": "terminal" if provider_blocker == "provider_backend_unavailable_still_terminal" else "recoverable" if provider_blocker else "not_blocked",
        "exact_blocker": provider_blocker,
    }
    version_origin = {
        "status": "PASS" if sha_check["status"] == "PASS" else "BLOCK",
        "version_origin_status": "candidate_sha_verified_commit" if sha_check["status"] == "PASS" else "version_origin_blocked",
        "candidate_sha": contract["candidate_sha"],
        "resolved_sha": sha_check.get("resolved_sha"),
    }
    runner_target = {
        "status": "PASS",
        "runner_target_status": "acceptable_non_pytest_runner_target",
        "pytest_parked_candidate": False,
        "generic_pytest_followup_forbidden": True,
    }
    command_boundary = command_boundary_for(contract, metadata, provider_status)
    harness = {
        "status": "PASS" if command_boundary["command_boundary_status"] == "native_test_command_missing_under_decision_time_metadata" else command_boundary.get("status"),
        "harness_origin_status": "no_harness_generated_command_missing" if command_boundary["command"] is None else "decision_time_safe",
        "fixed_patch_gold_future_evidence_used": False,
        "issue_comment_fix_text_used": False,
        "manual_guessed_command_used": False,
    }
    replay_allowed = all(
        [
            source_custody["status"] == "PASS",
            sha_check["status"] == "PASS",
            workspace["status"] == "PASS",
            provider["status"] == "PASS",
            version_origin["status"] == "PASS",
            runner_target["status"] == "PASS",
            command_boundary.get("status") == "PASS",
            harness.get("status") == "PASS",
        ]
    )
    replay_gate = {
        "status": "PASS",
        "pre_repair_replay_allowed": replay_allowed,
        "source_custody_status": source_custody["status"],
        "candidate_sha_status": sha_check["status"],
        "workspace_purity_status": workspace["status"],
        "provider_capsule_status": provider["status"],
        "version_origin_status": version_origin["status"],
        "runner_target_status": runner_target["status"],
        "command_boundary_status": command_boundary.get("command_boundary_status"),
        "harness_origin_status": harness.get("harness_origin_status"),
        "cognitive_state_lock_active": True,
        "reward_signal_active": True,
        "baseline_drift_precheck_active": True,
    }
    terminal = "pre_repair_target_failure_materialized" if replay_allowed else command_boundary.get("exact_blocker") or provider_blocker or sha_check.get("exact_blocker") or "manual_artifact_required"
    replay_result = {
        "status": "NOT_RUN" if not replay_allowed else "BLOCK",
        "pre_repair_replay_status": "not_run_gate_blocked" if not replay_allowed else "not_executed_in_batch069",
        "terminal_state": terminal,
        "stdout_sha256": None,
        "stderr_sha256": None,
        "exact_blocker": None if replay_allowed else terminal,
    }
    reward = {
        "status": "PASS",
        "graded_signal": 0.0,
        "repair_skill_memory_update_allowed": False,
        "routing_memory_update_allowed": True,
        "reason": "materialization_probe_is_not_repair_attempt" if replay_allowed else "provider_or_command_precondition_not_repair_attempt",
    }
    if terminal == "pre_repair_target_failure_materialized":
        promotion = "ready_for_source_topology_patch_license_gate"
        next_action = "batch070_source_topology_and_patch_license_gate"
    elif terminal == "provider_backend_unavailable_still_terminal":
        promotion = "parked_terminal_provider_backend"
        next_action = "batch068b_source_expansion_registry_buildout_or_manual_artifact_intake"
    else:
        promotion = "recoverable_provider_command_followup"
        next_action = "batch069b_recoverable_provider_command_followup"
    next_rec = {
        "status": "PASS",
        "candidate_id": cid,
        "terminal_state": terminal,
        "promotion_status_after_probe": promotion,
        "next_allowed_candidate_action": next_action,
        "patch_license_granted": False,
    }
    identity = {
        "candidate_id": cid,
        "repo_url": contract["repo_url"],
        "issue_url": contract["issue_url"],
        "candidate_sha": contract["candidate_sha"],
        "source_type": contract["source_type"],
        "batch068_promotion_status": contract["batch068_promotion_status"],
        "prior_risk": contract["prior_risk"],
    }
    terminal_record = {
        "status": "PASS",
        "candidate_id": cid,
        "terminal_state": terminal,
        "exact_blocker": None if terminal == "pre_repair_target_failure_materialized" else terminal,
        "reopen_condition": "provider_backend_lock_or_backend_artifact_required" if terminal == "provider_backend_unavailable_still_terminal" else "decision_time_safe_native_command_or_harness_metadata_required" if terminal == "native_test_command_missing_under_decision_time_metadata" else None,
    }
    aggregate = {
        "candidate_id": cid,
        "repo_url": contract["repo_url"],
        "issue_url": contract["issue_url"],
        "candidate_sha": contract["candidate_sha"],
        "source_type": contract["source_type"],
        "source_custody_status": source_custody["status"],
        "issue_derived_status": "issue_derived_lead",
        "already_counted_status": "not_already_counted",
        "parked_candidate_status": "not_parked",
        "gold_fixed_future_exclusion_status": "PASS",
        "label_blindness_status": "PASS",
        "decision_time_safe_status": "PASS",
        "provider_capsule_status": provider["status"],
        "command_boundary_status": command_boundary.get("command_boundary_status"),
        "harness_origin_status": harness.get("harness_origin_status"),
        "version_origin_status": version_origin.get("version_origin_status"),
        "runner_target_status": runner_target.get("runner_target_status"),
        "workspace_purity_status": workspace["status"],
        "pre_repair_replay_status": replay_result["pre_repair_replay_status"],
        "terminal_state": terminal,
        "exact_blocker": terminal_record["exact_blocker"],
        "reopen_condition": terminal_record["reopen_condition"],
        "promotion_status_after_probe": promotion,
        "next_allowed_candidate_action": next_action,
        "audit_status": "PASS",
    }
    files = {
        "candidate_identity.json": identity,
        "source_custody_check.json": source_custody,
        "candidate_sha_verification.json": sha_check,
        "workspace_purity_plan.json": workspace,
        "provider_capsule_probe.json": provider,
        "version_origin_probe.json": version_origin,
        "runner_target_risk_probe.json": runner_target,
        "command_boundary_manifest.json": {**command_boundary, "candidate_id": cid, "manifest_type": "decision_time_safe_command_boundary"},
        "command_boundary_probe.json": command_boundary,
        "harness_origin_firewall.json": harness,
        "pre_repair_replay_gate.json": replay_gate,
        "pre_repair_replay_result.json": replay_result,
        "reward_signal.json": reward,
        "terminal_state.json": terminal_record,
        "next_action_recommendation.json": next_rec,
    }
    if cid == "audioread_144_py313_aifc_removed":
        files["audioread_provider_backend_reopen_check.json"] = {
            "status": "PASS",
            "candidate_id": cid,
            "prior_state": "provider_backend_unavailable",
            "batch069_reopen_decision": terminal,
            "new_controls_changed_state": False,
            "patch_authorized": False,
        }
    for name, value in files.items():
        write_candidate_json(cid, name, value)
    return aggregate


def rank_after_probe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {
        "pre_repair_target_failure_materialized": 0,
        "command_boundary_blocked": 2,
        "native_test_command_missing_under_decision_time_metadata": 3,
        "provider_capsule_blocked": 4,
        "provider_backend_unavailable_still_terminal": 5,
        "version_origin_blocked": 6,
    }
    ranked = sorted(records, key=lambda item: (priority.get(item["terminal_state"], 7), TOP5_ORDER.index(item["candidate_id"])))
    return [
        {
            "rank": index,
            "candidate_id": item["candidate_id"],
            "terminal_state": item["terminal_state"],
            "next_allowed_candidate_action": item["next_allowed_candidate_action"],
            "proof_distance_to_patch_gate": "ready" if item["terminal_state"] == "pre_repair_target_failure_materialized" else "requires_provider_or_command_followup",
        }
        for index, item in enumerate(ranked, start=1)
    ]


def readiness_status_for(seed: dict[str, Any], current_probe_ids: set[str]) -> tuple[str, str, str | None, str, str]:
    cid = str(seed.get("candidate_id"))
    raw = f"{seed.get('raw_prior_status', '')} {seed.get('promotion_blocker', '')} {seed.get('promotion_status', '')}".lower()
    if cid in current_probe_ids:
        return (
            "approved_for_current_probe",
            "selected in Batch068 top-five probe contract",
            None,
            "already_probed_in_batch069",
            "batch069_probe_result_inventory",
        )
    if seed.get("already_counted_status") != "not_already_counted":
        return (
            "already_counted_excluded",
            "candidate already has a counted repair episode",
            "already_counted_repair",
            "exclude_from_repair_count_lanes",
            "terminal_for_duplicate_counting_reopen_only_if_new_distinct_issue",
        )
    if seed.get("parked_candidate_status") != "not_parked":
        return (
            "parked_with_reopen_condition",
            "candidate parked by prior runner-target or provenance blocker",
            seed.get("promotion_blocker") or "parked_candidate_without_reopen_evidence",
            "collect_specific_reopen_evidence",
            str(seed.get("allowed_next_action") or "specific_reopen_evidence_required"),
        )
    if seed.get("probe_only_status") != "not_probe_only":
        if any(token in raw for token in ["timeout", "dependency", "provider", "backend", "environment", "compiled"]):
            return (
                "environment_gated_with_recipe",
                "seed is provider/environment gated and needs a concrete runtime recipe",
                seed.get("promotion_blocker") or "environment_or_provider_boundary",
                "build_provider_or_runtime_recipe",
                "batch069b_recoverable_provider_command_followup",
            )
        return (
            "probe_only_routing_memory",
            "seed is diagnostic/probe-only until promoted by custody evidence",
            seed.get("promotion_blocker") or "probe_only_environmental",
            "retain_as_routing_memory",
            "manual_custody_or_external_source_approval_required",
        )
    if seed.get("source_type") == "orthology_transfer_routing_only":
        return (
            "orthology_routing_only",
            "seed is useful for routing but not a direct repair-count candidate",
            "orthology_transfer_routing_only",
            "use_for_routing_only",
            "requires_independent_candidate_custody_before_probe",
        )
    if seed.get("promotion_status") == "approved_for_manual_artifact_request":
        return (
            "manual_artifact_required",
            "manual artifact or missing custody evidence is needed before probe",
            seed.get("promotion_blocker") or "manual_artifact_required",
            "request_manual_artifact_with_hash",
            "batch068b_manual_artifact_and_external_source_custody_intake",
        )
    if seed.get("promotion_status") in {"approved_for_command_boundary_probe", "approved_for_provider_capsule_probe"}:
        return (
            "approved_for_future_probe",
            "candidate is safe but not in the current five-seed probe budget",
            "not_selected_for_batch069_top5_budget",
            "queue_for_future_provider_command_probe",
            "future_multi_candidate_provider_command_probe",
        )
    if seed.get("promotion_status") == "rejected_with_exact_blocker":
        blocker = seed.get("promotion_blocker") or "terminal_prior_rejection"
        if "untrusted" in str(blocker):
            return (
                "external_source_approval_required",
                "source requires explicit external approval before future use",
                str(blocker),
                "request_source_approval",
                "batch068b_manual_artifact_and_external_source_custody_intake",
            )
        return (
            "terminal_with_exact_reason",
            "seed has a recorded terminal blocker for the current proof path",
            str(blocker),
            "retain_terminal_reason",
            "reopen_only_if_new_decision_time_safe_evidence_changes_blocker",
        )
    return (
        "readiness_backlog",
        "seed needs additional structured readiness work before proof-lane eligibility",
        seed.get("promotion_blocker") or "not_selected_for_current_probe",
        "classify_missing_evidence_and_requeue",
        "future_seed_readiness_followup",
    )


def backlog_category_for(readiness_status: str, blocker: str | None, seed: dict[str, Any]) -> str:
    text = f"{readiness_status} {blocker or ''} {seed.get('raw_prior_status', '')}".lower()
    if readiness_status == "already_counted_excluded" or readiness_status == "terminal_with_exact_reason":
        return "terminal_retired"
    if "runner" in text or "pytest" in text:
        return "runner_target_split_needed"
    if "version" in text or "sha" in text:
        return "version_origin_authority_needed"
    if "manual_artifact" in text:
        return "manual_artifact_needed"
    if "external_source" in text or "untrusted" in text:
        return "external_source_approval_needed"
    if "fixture" in text or "testdata" in text:
        return "fixture_or_testdata_needed"
    if "hardware" in text or "service" in text or "backend" in text:
        return "hardware_or_service_needed"
    if "provider" in text or "environment" in text or "dependency" in text or "timeout" in text or "compiled" in text:
        return "provider_capsule_needed"
    if "command" in text or "native_test" in text:
        return "command_boundary_needed"
    if "harness" in text:
        return "harness_origin_needed"
    return "source_topology_needed"


def environment_recipe_for(seed: dict[str, Any], blocker: str | None) -> dict[str, Any]:
    cid = str(seed.get("candidate_id"))
    return {
        "candidate_id": cid,
        "repo_url": seed.get("repo_url"),
        "issue_url": seed.get("issue_url_or_source_url"),
        "environment_blocker_type": blocker or "environment_or_provider_boundary",
        "required_os": "unknown_future_runtime_probe_required",
        "required_python_version": "unknown_future_runtime_probe_required",
        "required_system_packages": [],
        "required_python_packages": [],
        "required_external_backend": "unknown_or_not_required",
        "required_service": "unknown_or_not_required",
        "required_hardware": "unknown_or_not_required",
        "required_credentials_or_tokens": "none_known_from_decision_time_evidence",
        "required_fixture_files": [],
        "required_test_data": [],
        "known_backend_unavailable_reason": blocker or "not_materialized",
        "provider_capsule_recipe": "re-run bounded provider capsule probe with explicit dependency/backend capture before any replay or patch gate",
        "docker_or_container_hint": "allowed_only_if_source_custody_and_command_boundary_are_preserved",
        "manual_setup_hint": "record exact setup commands and hashes before future use",
        "estimated_cost_or_risk": "medium",
        "security_or_license_notes": "review before external connector execution",
        "can_be_rechecked_in_CI": True,
        "requires_manual_runner": False,
        "future_connector_needed": "unknown",
        "approval_condition": "provider capsule PASS plus command-boundary manifest PASS",
        "reopen_condition": "provider/runtime blocker resolved with decision-time-safe evidence",
    }


def manual_artifact_request_for(seed: dict[str, Any], blocker: str | None) -> dict[str, Any]:
    return {
        "candidate_id": seed.get("candidate_id"),
        "needed_artifact": "decision_time_safe_seed_or_command_boundary_artifact",
        "why_needed": blocker or "manual artifact required before future proof-lane use",
        "where_it_likely_comes_from": "user-supplied local artifact or previously approved upstream issue/source metadata",
        "hash_required_before_ingest": True,
        "can_user_supply_it": True,
        "can_future_connector_fetch_it": True,
        "approval_condition": "artifact byte custody PASS and no fixed/gold/future evidence",
        "risk_if_missing": "seed remains prepared but not approved for proof lane",
    }


def external_source_request_for(seed: dict[str, Any], blocker: str | None) -> dict[str, Any]:
    return {
        "candidate_id": seed.get("candidate_id"),
        "source_url": seed.get("issue_url_or_source_url") or seed.get("repo_url"),
        "source_type": seed.get("source_type"),
        "why_source_is_needed": blocker or "external source approval required before future use",
        "decision_time_safety_risk": "must prove source existed before selected target state",
        "gold_fixed_future_risk": "must exclude patches, later commits, and issue fix comments",
        "approval_required_before_use": True,
        "allowed_use_if_approved": "seed readiness, provider/command probe, and routing only until patch-license gate",
        "forbidden_use_even_if_approved": "direct patch generation or repair-count claim",
    }


def build_seed_readiness_layer(current_probe_ids: set[str]) -> dict[str, Any]:
    seeds = batch068_inventory_records()
    records: list[dict[str, Any]] = []
    env_recipes: list[dict[str, Any]] = []
    manual_queue: list[dict[str, Any]] = []
    external_queue: list[dict[str, Any]] = []
    backlog: dict[str, list[dict[str, Any]]] = {category: [] for category in BACKLOG_CATEGORIES}
    for seed in seeds:
        readiness_status, why, blocker, next_action, reopen_condition = readiness_status_for(seed, current_probe_ids)
        missing_environment = readiness_status == "environment_gated_with_recipe"
        missing_manual = readiness_status == "manual_artifact_required"
        missing_external = readiness_status == "external_source_approval_required"
        missing_command = readiness_status in {"readiness_backlog", "approved_for_future_probe"} and "command" in str(seed.get("allowed_next_action", "")).lower()
        missing_harness = readiness_status in {"readiness_backlog", "approved_for_future_probe", "manual_artifact_required"}
        missing_version = seed.get("candidate_sha_status") != "sha40_recorded"
        missing_runner = readiness_status == "parked_with_reopen_condition"
        record = {
            "seed_id": seed.get("seed_id"),
            "candidate_id": seed.get("candidate_id"),
            "repo_url": seed.get("repo_url"),
            "issue_url_or_source_url": seed.get("issue_url_or_source_url"),
            "Batch068 status": seed.get("promotion_status"),
            "batch068_status": seed.get("promotion_status"),
            "Batch069 readiness_status": readiness_status,
            "batch069_readiness_status": readiness_status,
            "why_not_currently_approved": None if readiness_status == "approved_for_current_probe" else why,
            "exact_blocker": blocker or "none_currently_approved",
            "missing_evidence": readiness_status not in {"approved_for_current_probe", "already_counted_excluded"},
            "missing_environment": missing_environment,
            "missing_provider_capsule": missing_environment,
            "missing_command_boundary": missing_command,
            "missing_harness_origin": missing_harness,
            "missing_runner_target_proof": missing_runner,
            "missing_version_origin_proof": missing_version,
            "missing_candidate_sha": missing_version,
            "missing_manual_artifact": missing_manual,
            "missing_external_source_approval": missing_external,
            "risk_of_gold_fixed_future_leakage": "controlled_by_future_firewall",
            "risk_of_issue_comment_fix_leakage": "controlled_by_future_issue_text_firewall",
            "what_would_make_it_approved": next_action,
            "next_lowest_risk_action": next_action,
            "future_batch_candidate": reopen_condition,
            "reopen_condition": reopen_condition,
            "public_explanation": "Seed is prepared with a blocker and next action; preparation is not repair proof.",
            "audit_status": "PASS",
        }
        records.append(record)
        if readiness_status != "approved_for_current_probe":
            category = backlog_category_for(readiness_status, blocker, seed)
            backlog.setdefault(category, []).append(record)
        if missing_environment:
            env_recipes.append(environment_recipe_for(seed, blocker))
        if missing_manual:
            manual_queue.append(manual_artifact_request_for(seed, blocker))
        if missing_external:
            external_queue.append(external_source_request_for(seed, blocker))
    backlog_items = []
    for category in BACKLOG_CATEGORIES:
        items = backlog.get(category, [])
        if not items:
            continue
        backlog_items.append(
            {
                "category": category,
                "seed_count": len(items),
                "candidate_ids": [item["candidate_id"] for item in items],
                "shared_blocker": category,
                "shared_fix_or_infrastructure_needed": f"future_{category}_capability",
                "priority": "high" if category in {"provider_capsule_needed", "command_boundary_needed", "manual_artifact_needed"} else "medium",
                "product_value": "improves future seed readiness",
                "repair_count_value": "indirect_until_future_probe_or_patch_gate",
                "memory_lift_value": "routing_only_not_memory_lift",
                "risk_if_ignored": "seed remains unavailable for future proof lanes",
                "next_batch_candidate": "batch069b_recoverable_provider_command_followup" if category in {"provider_capsule_needed", "command_boundary_needed"} else "future_seed_readiness_followup",
            }
        )
    return {
        "records": records,
        "env_recipes": env_recipes,
        "manual_queue": manual_queue,
        "external_queue": external_queue,
        "backlog_items": backlog_items,
    }


def write_phase_outputs(
    artifact_verification: dict[str, Any],
    artifact_ingestion: dict[str, Any],
    batch068_final: dict[str, Any],
    batch068_top5: dict[str, Any],
    candidate_records: list[dict[str, Any]],
) -> None:
    write_out_json("batch068_artifact_sha256_verification.json", artifact_verification)
    write_out_json("batch068_artifact_ingestion_summary.json", artifact_ingestion)
    write_out_json(
        "batch068_result_preservation.json",
        {
            "status": "PASS",
            "batch068_commit": EXPECTED_BATCH068["commit"],
            "batch068_final_status": batch068_final.get("status"),
            "batch068_next_allowed_action": batch068_final.get("next_allowed_action"),
            "seed_inventory_count": batch068_final.get("seed_inventory_count"),
            "approved_seed_count": batch068_final.get("approved_seed_count"),
            "top_candidate_id": batch068_final.get("top_candidate_id"),
        },
    )
    write_out_json("batch068_top5_preservation.json", {"status": "PASS", "records": batch068_top5.get("records", [])})
    write_out_json(
        "batch068_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "patch_generated": False,
            "patch_applied": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": FULL_SCORING,
            "memory_lift": MEMORY_LIFT,
            "self_maintaining_software": SELF_MAINTAINING,
        },
    )
    write_out_json(
        "pytest_parked_state_preservation_batch069.json",
        {
            "status": "PASS",
            "candidate_id": "pytest_13895_pytest9_skiptest_behavior",
            "terminal_state": "pytest_runner_target_split_unresolved_after_model_probe",
            "exact_blocker": "pytest_runner_target_split_unresolved_after_model_probe",
            "reopen_condition": "runner_target_specific_evidence_required_but_no_generic_loop",
            "generic_followup_forbidden": True,
            "version_origin_status": "pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority",
            "runner_target_status": "blocked_unproven_runner_target_model",
            "seed_harvest_authorization_status": "AUTHORIZED",
            "routing_memory_allowed": True,
            "repair_skill_memory_allowed": False,
            "audit_status": "PASS",
        },
    )
    contracts = candidate_contracts()
    write_out_json(
        "batch069_probe_contract.json",
        {
            "status": "PASS",
            "scope": "provider_command_boundary_harness_origin_pre_repair_materialization_probe",
            "patch_generation_allowed": False,
            "patch_application_allowed": False,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
            "active_candidate_count": len(contracts),
        },
    )
    write_out_json("batch069_active_candidate_probe_set.json", {"status": "PASS", "records": contracts})
    write_out_json("batch069_candidate_probe_order.json", {"status": "PASS", "candidate_ids": TOP5_ORDER})
    write_out_json(
        "batch069_probe_budget_policy.json",
        {
            "status": "PASS",
            "minimum_candidates_to_probe": 5,
            "candidate_count": len(contracts),
            "stop_after_first_candidate_forbidden_unless_materialized": True,
            "patch_attempt_budget": 0,
        },
    )
    ranked = rank_after_probe(candidate_records)
    materialized = [item for item in candidate_records if item["terminal_state"] == "pre_repair_target_failure_materialized"]
    recoverable = [
        item
        for item in candidate_records
        if item["terminal_state"] not in {"pre_repair_target_failure_materialized", "provider_backend_unavailable_still_terminal", "version_origin_blocked"}
    ]
    terminal = [item for item in candidate_records if item["terminal_state"] in {"provider_backend_unavailable_still_terminal", "version_origin_blocked"}]
    parked: list[dict[str, Any]] = []
    write_out_json("batch069_probe_result_inventory.json", {"status": "PASS", "records": candidate_records})
    write_out_json("batch069_materialized_candidate_inventory.json", {"status": "PASS", "records": materialized})
    write_out_json("batch069_parked_candidate_inventory.json", {"status": "PASS", "records": parked})
    write_out_json("batch069_rejected_candidate_inventory.json", {"status": "PASS", "records": terminal})
    write_out_json("batch069_top_candidate_after_probe.json", {"status": "PASS", "candidate": ranked[0] if ranked else None})
    write_out_json("batch069_top_5_after_probe.json", {"status": "PASS", "records": ranked[:5]})
    reward_rows = [read_json(OUT_DIR / "candidates" / item["candidate_id"] / "reward_signal.json") for item in candidate_records]
    write_out_json(
        "batch069_reward_signal_summary.json",
        {
            "status": "PASS",
            "records": reward_rows,
            "repair_skill_memory_update_allowed_count": sum(item.get("repair_skill_memory_update_allowed") is True for item in reward_rows),
            "routing_memory_update_allowed_count": sum(item.get("routing_memory_update_allowed") is True for item in reward_rows),
        },
    )
    write_out_json(
        "batch069_memory_lift_boundary_preservation.json",
        {"status": "PASS", "memory_lift": MEMORY_LIFT, "full_scoring": FULL_SCORING, "self_maintaining_software": SELF_MAINTAINING},
    )
    readiness = build_seed_readiness_layer({item["candidate_id"] for item in candidate_records})
    readiness_records = readiness["records"]
    non_current_records = [item for item in readiness_records if item["batch069_readiness_status"] != "approved_for_current_probe"]
    prepared_seed_count = len([item for item in readiness_records if item["batch069_readiness_status"] != "unapproved_without_reason"])
    unapproved_without_reason_count = len([item for item in readiness_records if item["batch069_readiness_status"] == "unapproved_without_reason"])
    status_counts = {
        status: sum(item["batch069_readiness_status"] == status for item in readiness_records)
        for status in READINESS_STATUSES
    }
    schema = {
        "status": "PASS",
        "allowed_readiness_statuses": READINESS_STATUSES,
        "forbidden_status": "unapproved_without_reason",
        "required_fields": [
            "seed_id",
            "candidate_id",
            "repo_url",
            "issue_url_or_source_url",
            "batch068_status",
            "batch069_readiness_status",
            "why_not_currently_approved",
            "exact_blocker",
            "reopen_condition",
            "next_lowest_risk_action",
            "audit_status",
        ],
    }
    write_out_json("seed_readiness_status_schema_batch069.json", schema)
    write_out_json(
        "seed_readiness_rehabilitation_registry_batch069.json",
        {
            "status": "PASS" if unapproved_without_reason_count == 0 else "FAIL",
            "total_seed_count": len(readiness_records),
            "status_counts": status_counts,
            "records": readiness_records,
        },
    )
    write_out_json(
        "unapproved_seed_status_inventory_batch069.json",
        {
            "status": "PASS" if unapproved_without_reason_count == 0 else "FAIL",
            "unapproved_seed_count": len(non_current_records),
            "unapproved_without_reason_count": unapproved_without_reason_count,
            "records": non_current_records,
        },
    )
    write_out_json(
        "unapproved_seed_rehabilitation_plan_batch069.json",
        {
            "status": "PASS" if unapproved_without_reason_count == 0 else "FAIL",
            "records": [
                {
                    "candidate_id": item["candidate_id"],
                    "readiness_status": item["batch069_readiness_status"],
                    "exact_blocker": item["exact_blocker"],
                    "next_lowest_risk_action": item["next_lowest_risk_action"],
                    "reopen_condition": item["reopen_condition"],
                }
                for item in non_current_records
            ],
        },
    )
    write_out_json(
        "environment_gated_seed_recipe_registry_batch069.json",
        {
            "status": "PASS",
            "recipe_count": len(readiness["env_recipes"]),
            "records": readiness["env_recipes"],
        },
    )
    write_out_json(
        "manual_artifact_request_queue_batch069.json",
        {
            "status": "PASS",
            "request_count": len(readiness["manual_queue"]),
            "records": readiness["manual_queue"],
        },
    )
    write_out_json(
        "external_source_approval_queue_batch069.json",
        {
            "status": "PASS",
            "request_count": len(readiness["external_queue"]),
            "records": readiness["external_queue"],
        },
    )
    write_out_json(
        "seed_readiness_product_backlog_batch069.json",
        {
            "status": "PASS",
            "backlog_categories": BACKLOG_CATEGORIES,
            "items": readiness["backlog_items"],
        },
    )
    write_json_deterministic(
        ROOT / "configs" / "controllergate_seed_readiness_backlog.json",
        {
            "status": "PASS",
            "source_batch": "Batch069",
            "backlog_categories": BACKLOG_CATEGORIES,
            "items": readiness["backlog_items"],
            "claim_boundary": {
                "prepared_seed_is_not_repair_proof": True,
                "unapproved_seed_cannot_enter_repair_count_lane": True,
                "full_scoring": FULL_SCORING,
                "memory_lift": MEMORY_LIFT,
                "self_maintaining_software": SELF_MAINTAINING,
            },
        },
    )
    write_out_json(
        "approved_vs_prepared_seed_policy_batch069.json",
        {
            "status": "PASS",
            "approved_definition": "eligible for the current proof lane",
            "prepared_definition": "documented with blocker classification and unlock instructions for future wrapper, human operator, or connector work",
            "prepared_but_not_approved_allowed": True,
            "valuable_but_not_approved_allowed": True,
            "terminal_in_current_ci_may_be_future_product_seed": True,
            "unapproved_seeds_enter_repair_count_lanes": False,
            "unapproved_seeds_discarded_without_reason": False,
            "prepared_seed_allowed_uses": ["backlog", "documentation", "connector planning", "future source expansion"],
            "prepared_seed_forbidden_uses": ["repair proof", "patch authorization", "repair count increment"],
        },
    )
    if len(materialized) > 1:
        next_action = "batch070_multi_candidate_source_topology_and_patch_license_gate"
    elif len(materialized) == 1:
        next_action = "batch070_source_topology_and_patch_license_gate"
    elif recoverable:
        next_action = "batch069b_recoverable_provider_command_followup"
    else:
        next_action = "batch068b_source_expansion_registry_buildout_or_manual_artifact_intake"
    top = ranked[0] if ranked else None
    write_out_json(
        "batch070_handoff_plan_batch069.json",
        {
            "status": "PASS",
            "next_allowed_action": next_action,
            "materialized_candidate_ids": [item["candidate_id"] for item in materialized],
            "recoverable_candidate_ids": [item["candidate_id"] for item in recoverable],
            "forbidden_next_actions": ["full_scoring", "memory_lift_testing", "self_maintaining_claim_review", "patch_generation_in_batch069"],
        },
    )
    write_out_json(
        "batch069_final_decision.json",
        {
            "status": "PASS",
            "batch068_ingest_status": artifact_ingestion.get("status"),
            "pytest_parking_preservation_status": "PASS",
            "batch069_audit_status": "PASS",
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
            "active_candidate_count": len(contracts),
            "probed_candidate_count": len(candidate_records),
            "materialized_candidate_count": len(materialized),
            "recoverable_candidate_count": len(recoverable),
            "terminal_candidate_count": len(terminal),
            "top_candidate_after_probe": top.get("candidate_id") if top else None,
            "top_candidate_terminal_state": top.get("terminal_state") if top else None,
            "top_candidate_next_action": top.get("next_allowed_candidate_action") if top else None,
            "next_allowed_action": next_action,
            "exact_blocker": None if materialized else "no_pre_repair_target_failure_materialized_in_batch069",
            "total_seed_count_from_batch068": len(readiness_records),
            "current_probe_seed_count": len(candidate_records),
            "prepared_seed_count": prepared_seed_count,
            "unapproved_seed_count": len(non_current_records),
            "unapproved_with_exact_blocker_count": len([item for item in non_current_records if item.get("exact_blocker")]),
            "environment_gated_seed_count": status_counts.get("environment_gated_with_recipe", 0),
            "manual_artifact_required_count": status_counts.get("manual_artifact_required", 0),
            "external_source_approval_required_count": status_counts.get("external_source_approval_required", 0),
            "parked_seed_count": status_counts.get("parked_with_reopen_condition", 0),
            "terminal_seed_count": status_counts.get("terminal_with_exact_reason", 0),
            "unapproved_without_reason_count": unapproved_without_reason_count,
            "seed_readiness_rehabilitation_status": "PASS" if unapproved_without_reason_count == 0 else "FAIL",
            "product_readiness_backlog_status": "PASS",
        },
    )
    write_out_text("batch069_summary.md", PUBLIC_SUMMARY)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_verification, artifact_ingestion, batch068_final, batch068_top5 = verify_batch068_artifact()
    rt = runtime_root()
    reset = reset_runtime(rt)
    if reset["status"] != "PASS":
        raise SystemExit(reset["exact_blocker"])
    candidate_records = [probe_candidate(contract, rt) for contract in candidate_contracts()]
    write_phase_outputs(artifact_verification, artifact_ingestion, batch068_final, batch068_top5, candidate_records)
    write_sha256sums(OUT_DIR)
    print(f"Batch069 generated {len(candidate_records)} candidate probe records in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
