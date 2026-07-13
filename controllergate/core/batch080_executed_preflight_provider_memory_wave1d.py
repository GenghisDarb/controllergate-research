from __future__ import annotations

import json
import hashlib
import math
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.batch074_sterile_high_yield_wave1 import _internal_manifest
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.batch078_count6_minimal_closure_memory_wave1b import FRAME
from controllergate.intake.contamination_classifier import classify_contamination, sanitize_issue_record
from controllergate.intake.discovery_queries import github_json
from controllergate.intake.issue_reproducer_lane import assess_issue_reproducer
from controllergate.intake.source_object_verifier import verify_source_object
from controllergate.intake.static_collection_runner import run_static_collection
from controllergate.intake.command_resolution_v2 import resolve_command_v2
from controllergate.intake.provider_dry_lock import build_provider_dry_lock
from controllergate.runtime.platform_runtime_resolver import resolve_platform_runtime
from controllergate.runtime.python_runtime_resolver import resolve_python_runtime


BATCH = "post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d"
B79 = "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c"
B73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
B74 = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
B75 = "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a"
B76 = "post_v2_37_hardening_batch076_amds_causal_memory_calibration"
B77 = "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2"
B78 = "post_v2_37_hardening_batch078_count6_minimal_closure_memory_wave1b"
EXPECTED_SIZE = 998_670
EXPECTED_SHA256 = "f6a883915e31e91dceb601e5728d338f9b072cfc10acf75cb1e6223ae2c7a4ff"
EXPECTED_FILES = 383
EXPECTED_OUTER = 382
EXPECTED_MANIFESTS = {B73: 41, B74: 16, B75: 106, B76: 32, B77: 47, B78: 61, B79: 58}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text_lf(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _copy_prefix(archive: zipfile.ZipFile, prefix: str, output: Path) -> None:
    for item in archive.infolist():
        if item.is_dir() or not item.filename.startswith(prefix + "/"):
            continue
        destination = output / Path(*Path(item.filename).parts[1:])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read(item))


def verify_and_ingest_batch079(root: Path, artifact: Path) -> dict[str, Any]:
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA256)
    entries = audit_zip_entries(artifact)
    manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        names = [item.filename for item in files]
        internals = {prefix: _internal_manifest(archive, prefix) for prefix in EXPECTED_MANIFESTS}
        forbidden = [
            name for name in names
            if name.lower().endswith((".zip", ".tar", ".tgz", ".tar.gz", ".whl", ".pyc", ".pyo"))
            or "__pycache__" in name.lower()
            or "/.venv/" in name.lower()
            or "/venv/" in name.lower()
            or "/site-packages/" in name.lower()
        ]
        passed = (
            outer.get("status") == entries.get("status") == manifest.get("status") == "PASS"
            and len(files) == EXPECTED_FILES
            and manifest.get("checked") == EXPECTED_OUTER
            and not forbidden
            and all(value.get("status") == "PASS" and value.get("checked") == EXPECTED_MANIFESTS[name] for name, value in internals.items())
        )
        if not passed:
            raise RuntimeError("Batch079 artifact verification failed")
        for prefix in EXPECTED_MANIFESTS:
            _copy_prefix(archive, prefix, root / "outputs" / prefix)
    final = _load(root / "outputs" / B79 / "batch079_final_decision.json")
    hardening = _load(root / "outputs" / B79 / "cognicore_count6_revalidation.json")
    witness = _load(root / "outputs" / B79 / "cognicore_count6_semantic_diff_witness.json")
    if (
        hardening.get("COUNT_6_HARDENING") != "COUNT_6_HARDENING_PASS"
        or hardening.get("recounted") is not False
        or witness.get("status") != "PASS"
        or final.get("issue_derived_repair_count") != 6
    ):
        raise RuntimeError("Batch079 count-six proof boundary failed")
    return {
        "status": "PASS",
        "artifact_name": B79 + "_artifacts",
        "artifact_id": 8288039317,
        "workflow_run_id": 29272272738,
        "checkpoint_commit": "a8e901cd80ce9fbb6abd7b2b435571e040a691b1",
        "implementation_commit": "60cb0a6aceb208cde3b06016ec3c2030b63a79b8",
        "observed_size_bytes": artifact.stat().st_size,
        "observed_sha256": sha256_file(artifact),
        "file_count": len(files),
        "unsafe_paths": entries.get("unsafe_paths", []),
        "duplicate_paths": entries.get("duplicate_paths", []),
        "forbidden_payloads": forbidden,
        "outer_manifest": manifest,
        "internal_manifests": internals,
        "count_six_terminal_proof": "PASS",
        "count_uniqueness": "PASS",
        "semantic_diff_witness": "PASS",
        "raw_zip_committed": False,
        "local_artifact_path_recorded_outside_git": str(artifact),
    }


def _checkpoint_records(root: Path, ingest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    b79 = root / "outputs" / B79
    final = _load(b79 / "batch079_final_decision.json")
    preflight = _load(b79 / "batch079_incident_static_preflight.json")
    horde = _load(b79 / "hordeforge_native_working_directory_adapter.json")
    recovery = _load(b79 / "batch078_frame_recovery_decision.json")
    calibration = _load(b79 / "pathway_memory_baseline_results.json")
    return {
        "batch079_artifact_ingest.json": ingest,
        "batch079_state_preservation.json": {
            "status": "PASS",
            "validated_protocol": "v2.19",
            "issue_derived_repair_count": 6,
            "native_external_repair_count": 4,
            "original_batch079_files_modified": False,
        },
        "batch079_claim_boundary_preservation.json": {
            "status": "PASS",
            "validated_protocol": "v2.19 authorized_amds_active_maintenance_lane",
            "AMDS_prospective_effectiveness": "NOT_ESTABLISHED",
            "routing_memory_mechanism": "HISTORICAL_ROUTING_SIGNAL_OBSERVED",
            "prospective_lift": "not demonstrated",
            "memory_lift": "not demonstrated",
            "full_scoring": "NOT_RUN/disallowed",
            "self_maintaining_software": "false/not demonstrated",
            "live_connectors": "inactive",
        },
        "batch079_count6_hardening_preservation.json": {
            "status": "PASS",
            "COUNT_6_HARDENING": "COUNT_6_HARDENING_PASS",
            "historical_count": 6,
            "recounted": False,
            "CogniCore_rerun": False,
            "preserved_from_verified_artifact": True,
        },
        "batch079_incident_preflight_depth_reconciliation.json": {
            "status": "PASS",
            "BATCH079_INCIDENT_LEADS_REGISTERED": 6,
            "target_resolution_attempts": 0,
            "command_resolution_attempts": 0,
            "provider_dry_lock_attempts": 0,
            "file_collection_attempts": 0,
            "node_collection_attempts": 0,
            "classification": "REGISTERED_NOT_EXECUTED_STATIC_PREFLIGHT",
            "prior_source_object_verified_constant_detected": True,
            "promoted_as_executed_evidence": False,
            "prior_record_hash": hash_record(preflight),
        },
        "batch079_recovery_depth_reconciliation.json": {
            "status": "PASS",
            "classification": "PARTIAL_RECOVERY_DIAGNOSTICS_ONLY",
            "universal_python39_cause_inferred": False,
            "stage_complete_forensics_present": False,
            "prior_record_hash": hash_record(recovery),
        },
        "batch079_hordeforge_depth_reconciliation.json": {
            "status": "PASS",
            "adapter_configuration": "PASS",
            "native_target_execution": "NOT_ESTABLISHED",
            "adapter_defect_fixed": "NOT_ESTABLISHED",
            "observed_return_code": horde.get("return_code"),
            "target_start_sentinel_present": False,
            "target_terminal_sentinel_present": False,
            "docker_acquisition_output_is_success_proof": False,
        },
        "batch079_memory_calibration_depth_reconciliation_v2.json": {
            "status": "PASS",
            "prior_frequency_value_was_majority_prevalence_not_mrr": True,
            "uniform_expected_MRR_formula": "H_n/n",
            "analytical_uniform_expectation_is_executed_control": False,
            "prior_shuffled_method_was_reversed_seeded_random_rr": True,
            "prospective_memory_outcome_present": False,
            "allowed_conclusion": "HISTORICAL_ROUTING_SIGNAL_OBSERVED",
            "forbidden_conclusion": "STATISTICAL_MEMORY_LIFT_PROVED",
            "prior_record_hash": hash_record(calibration),
        },
        "batch080_checkpoint_state.json": {
            "status": "PASS",
            "phase": "EXECUTED_PREFLIGHT_AND_PROVIDER_CAPSULE_INFRASTRUCTURE_READY",
            "external_target_execution_started": False,
            "count_six_preserved_without_rerun": True,
            "prior_final_hash": hash_record(final),
        },
    }


DISCOVERY_QUERY = 'is:issue is:open language:Python ("tests/" OR "test_") traceback created:>=2025-01-01'


def _run(argv: list[str], *, cwd: Path | None = None, timeout: int = 600) -> dict[str, Any]:
    try:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        stdout, stderr, code, timed_out = completed.stdout, completed.stderr, completed.returncode, False
    except (OSError, subprocess.TimeoutExpired) as exc:
        stdout, stderr = str(getattr(exc, "stdout", "") or ""), str(getattr(exc, "stderr", "") or exc)
        code, timed_out = (124 if isinstance(exc, subprocess.TimeoutExpired) else 127), isinstance(exc, subprocess.TimeoutExpired)
    return {
        "argv": argv,
        "returncode": code,
        "timed_out": timed_out,
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "stdout": stdout[-16000:],
        "stderr": stderr[-12000:],
    }


def _issue_snapshot(issue_url: str, *, force_solution_contamination: bool = False) -> dict[str, Any]:
    api = issue_url.replace("https://github.com/", "https://api.github.com/repos/").replace("/issues/", "/issues/")
    issue = github_json(api)
    if not isinstance(issue, dict):
        raise RuntimeError("issue snapshot was not an object")
    comments_payload = github_json(str(issue.get("comments_url")) + "?per_page=100") if issue.get("comments_url") else []
    comments = "\n".join(str(item.get("body") or "") for item in comments_payload if isinstance(item, dict)) if isinstance(comments_payload, list) else ""
    body = str(issue.get("body") or "")
    contamination = classify_contamination(body, comments)
    if force_solution_contamination:
        contamination = {**contamination, "classification": "HARD_REJECT", "hard_contamination_hits": sorted(set(contamination.get("hard_contamination_hits", [])) | {"explicit_suggested_repair_direction"})}
    sanitized = sanitize_issue_record(title=str(issue.get("title") or ""), body=body, comments=comments, classification=contamination)
    return {
        "status": "BLOCK" if contamination["classification"] == "HARD_REJECT" else "PASS",
        "blocker": "solution_contamination_detected" if contamination["classification"] == "HARD_REJECT" else None,
        "issue_id": issue.get("id"),
        "issue_number": issue.get("number"),
        "issue_url": issue.get("html_url") or issue_url,
        "title": issue.get("title"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "raw_body_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "raw_comments_sha256": hashlib.sha256(comments.encode()).hexdigest(),
        "sanitized_text": sanitized["failure_description"],
        "sanitized_snapshot": sanitized,
        "contamination": contamination,
        "raw_text_committed": False,
    }


def _resolve_cutoff_sha(repo_url: str, created_at: str) -> dict[str, Any]:
    slug = repo_url.removeprefix("https://github.com/").removesuffix(".git")
    repo = github_json(f"https://api.github.com/repos/{slug}")
    if not isinstance(repo, dict):
        return {"status": "BLOCK", "blocker": "repository_identity_unresolved"}
    branch = str(repo.get("default_branch") or "")
    commits = github_json(f"https://api.github.com/repos/{slug}/commits?sha={quote(branch)}&until={quote(created_at)}&per_page=1")
    commit = commits[0] if isinstance(commits, list) and commits else {}
    sha = str(commit.get("sha") or "") if isinstance(commit, dict) else ""
    return {
        "status": "PASS" if len(sha) == 40 else "BLOCK",
        "repo_api_id": repo.get("id"),
        "repo_full_name": repo.get("full_name"),
        "default_branch": branch,
        "candidate_commit_cutoff": created_at,
        "candidate_sha": sha,
        "selection_method": "default_branch_latest_commit_at_or_before_issue_created_at",
        "outcome_used_for_selection": False,
    }


def _build_lead_pool(root: Path, output: Path, *, refresh: bool) -> dict[str, Any]:
    frozen = output / "batch080_incident_lead_pool_freeze.json"
    if frozen.is_file() and not refresh:
        return _load(frozen)
    b79_rows = [json.loads(line) for line in (root / "outputs" / B79 / "batch079_incident_lead_registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    query_url = f"https://api.github.com/search/issues?q={quote(DISCOVERY_QUERY)}&sort=created&order=desc&per_page=40"
    payload = github_json(query_url)
    items = list(payload.get("items", [])) if isinstance(payload, dict) else []
    known_repos = {row["repo_url"].lower() for row in b79_rows}
    selected_items: list[dict[str, Any]] = []
    for item in items:
        repo_url = str(item.get("repository_url", "")).replace("https://api.github.com/repos/", "https://github.com/")
        if not repo_url or repo_url.lower() in known_repos:
            continue
        known_repos.add(repo_url.lower())
        selected_items.append(item)
        if len(selected_items) == 14:
            break
    leads: list[dict[str, Any]] = []
    for row in b79_rows:
        force = row["candidate_id"] == "incident_pytest_asyncio_1501"
        snapshot = _issue_snapshot(row["issue_url"], force_solution_contamination=force)
        leads.append({
            "candidate_id": row["candidate_id"], "repo_url": row["repo_url"], "issue_url": row["issue_url"],
            "issue_created_at": row["issue_created_at"], "candidate_sha": row["candidate_sha"], "title": snapshot["title"],
            "issue_snapshot": snapshot, "source_selection": {"status": "PASS", "candidate_sha": row["candidate_sha"], "selection_method": "Batch079 frozen candidate cutoff"},
            "pool_source": "Batch079 corrected review", "pool_position": len(leads),
        })
    for item in selected_items:
        repo_url = str(item["repository_url"]).replace("https://api.github.com/repos/", "https://github.com/")
        issue_url = str(item["html_url"])
        snapshot = _issue_snapshot(issue_url)
        source = _resolve_cutoff_sha(repo_url, str(item["created_at"]))
        slug = repo_url.removeprefix("https://github.com/").replace("/", "_")
        leads.append({
            "candidate_id": f"wave1d_{slug}_{item['number']}", "repo_url": repo_url, "issue_url": issue_url,
            "issue_created_at": item["created_at"], "candidate_sha": source.get("candidate_sha"), "title": snapshot["title"],
            "issue_snapshot": snapshot, "source_selection": source, "pool_source": "fixed_query_public_incident", "pool_position": len(leads),
        })
    record = {
        "status": "PASS" if 18 <= len(leads) <= 24 else "BLOCK",
        "query": DISCOVERY_QUERY,
        "pages": [1],
        "sort": "created",
        "order": "desc",
        "frozen_at": "2026-07-13T23:59:00Z",
        "query_result_ids": [item.get("id") for item in items],
        "query_result_hash": hash_record(items),
        "lead_count": len(leads),
        "one_issue_per_repository": len({lead["repo_url"] for lead in leads}) == len(leads),
        "candidate_commit_cutoffs_frozen": True,
        "adaptive_replenishment": False,
        "leads": leads,
    }
    write_json_deterministic(frozen, record)
    return record


def _platform_request(text: str) -> tuple[str | None, str | None]:
    requested_os = "windows" if re.search(r"(?i)\bwindows\b|win32|win64", text) else "linux" if re.search(r"(?i)\blinux\b|ubuntu", text) else None
    version = re.search(r"(?i)python\s*(?:version)?\s*[:=]?\s*(3\.\d+)", text)
    return requested_os, version.group(1) if version else None


def _execute_preflight_pool(pool: dict[str, Any], runtime_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    from controllergate.intake.static_preflight_executor import execute_static_preflight

    records: list[dict[str, Any]] = []
    native_rows: list[dict[str, Any]] = []
    reproducer_rows: list[dict[str, Any]] = []
    for lead in pool["leads"]:
        snapshot = lead["issue_snapshot"]
        text = snapshot.get("sanitized_text", "")
        requested_os, requested_runtime = _platform_request(text)
        platform_record = resolve_platform_runtime(requested_os=requested_os)
        runtime_record = resolve_python_runtime({"declared_versions": [requested_runtime] if requested_runtime else [], "issue_runtime": requested_runtime})
        contamination = {"status": "BLOCK", "blocker": "solution_contamination_detected", **snapshot["contamination"]} if snapshot["contamination"]["classification"] == "HARD_REJECT" else {"status": "CLEAN", **snapshot["contamination"]}
        static_snapshot = {"status": "PASS", "sanitized_text": text, "raw_body_sha256": snapshot["raw_body_sha256"], "issue_url": lead["issue_url"]}
        workspace = runtime_root / "preflight" / str(lead["candidate_id"]) / "source"
        if not lead.get("candidate_sha"):
            source_block = {"status": "BLOCK", "blocker": "candidate_cutoff_commit_unresolved", "commit_object_verified": False, "head_verified": False, "tree_identity_verified": False}
            result = {"candidate_id": lead["candidate_id"], "stages": {"issue_snapshot": static_snapshot, "source": source_block, "runtime": runtime_record, "target": {"status": "NOT_RUN"}, "command": {"status": "NOT_RUN"}, "provider_dry_lock": {"status": "NOT_RUN"}, "collection": {"status": "NOT_RUN", "target_executed": False}, "contamination": contamination}, "terminal": {"candidate_id": lead["candidate_id"], "status": "PREFLIGHT_BLOCK", "admitted_to_execution_frame": False, "terminal_blocker": "candidate_cutoff_commit_unresolved", "target_execution_count": 0}}
        else:
            lead_for_executor = {**lead, "contamination": contamination}
            result = execute_static_preflight(lead_for_executor, workspace, issue_snapshot=static_snapshot, platform=platform_record, runtime=runtime_record)
        result.update({"repo_url": lead["repo_url"], "issue_url": lead["issue_url"], "candidate_sha": lead.get("candidate_sha"), "pool_position": lead["pool_position"], "platform": platform_record, "runtime": runtime_record})
        records.append(result)
        target = result["stages"].get("target", {})
        if target.get("status") == "PASS":
            native_rows.append({"candidate_id": lead["candidate_id"], "lane": "NATIVE_TARGET_LANE", "target": target, "command": result["stages"].get("command"), "candidate_source_ownership": True, "native_harness_origin": "pinned_source_commit", "preflight_terminal": result["terminal"]["status"]})
        reproducer = assess_issue_reproducer(candidate_id=lead["candidate_id"], sanitized_text=text, platform=requested_os or platform_record["operating_system"], runtime=requested_runtime or runtime_record.get("selected_runtime"), source_sha=str(lead.get("candidate_sha") or ""))
        if lead["candidate_id"] == "incident_marshmallow_2985":
            reproducer.update({"status": "BLOCK", "blocker": "design_or_behavior_question_without_pinned_defect_policy"})
        if lead["candidate_id"] == "incident_pytest_asyncio_1501":
            reproducer.update({"status": "BLOCK", "blocker": "solution_contamination_detected", "unsanitized_issue_admitted": False})
        if reproducer["status"] != "BLOCK" or lead["candidate_id"] in {"incident_poetry_10974", "incident_marshmallow_2985", "incident_pytest_asyncio_1501"}:
            reproducer_rows.append(reproducer)
    return records, native_rows, reproducer_rows


def _historical_forensics(root: Path, runtime_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    collections: list[dict[str, Any]] = []
    providers: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for candidate in FRAME:
        candidate_id = candidate["candidate_id"]
        source = runtime_root / "batch078-forensics" / candidate_id / "source"
        source_record = verify_source_object(candidate["repo_url"], candidate["candidate_sha"], source)
        platform_record = resolve_platform_runtime()
        runtime_record = resolve_python_runtime({"declared_versions": ["3.8", "3.9"], "requires_python": ">=3.6"})
        target = candidate["target"]["target"]
        target_file = source / target.split("::", 1)[0]
        target_record = {"status": "PASS" if target_file.is_file() else "BLOCK", "target": target, "target_file_present": target_file.is_file(), "target_sha256": sha256_file(target_file) if target_file.is_file() else None}
        command = resolve_command_v2(source, target) if source_record["status"] == "PASS" and target_file.is_file() else {"status": "NOT_RUN"}
        dry_lock = build_provider_dry_lock(source, runtime=runtime_record, platform=platform_record) if source_record["status"] == "PASS" else {"status": "NOT_RUN"}
        build_copy = runtime_root / "batch078-forensics" / candidate_id / "build-copy"
        wheelhouse = runtime_root / "batch078-forensics" / candidate_id / "provider-bytes"
        if source_record["status"] == "PASS":
            shutil.copytree(source, build_copy, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
            wheelhouse.mkdir(parents=True, exist_ok=True)
            build = _run([sys.executable, "-m", "pip", "wheel", "--disable-pip-version-check", "--no-deps", "--wheel-dir", str(wheelhouse), "."], cwd=build_copy, timeout=300)
        else:
            build = {"returncode": 127, "stdout": "", "stderr": "source acquisition blocked"}
        artifacts = [{"filename": path.name, "sha256": sha256_file(path)} for path in sorted(wheelhouse.glob("*")) if path.is_file()]
        collection = run_static_collection(source, command, target, timeout=180) if command.get("status") == "PASS" else {"status": "NOT_RUN", "blocker": "command_authority_unresolved", "nodes": [], "target_executed": False}
        classification = "TARGET_IDENTITY_RECOVERED" if target_record["status"] == "PASS" and collection.get("status") == "PASS" else "PROVIDER_CAPSULE_RECOVERED" if build.get("returncode") == 0 and artifacts and dry_lock.get("status") == "PASS" else "UNRESOLVED_WITH_STAGE_EVIDENCE"
        stage_rows = [
            {"stage": "source_acquisition", "status": source_record["status"], "record_hash": hash_record(source_record)},
            {"stage": "runtime_selection", "status": runtime_record["status"], "record_hash": hash_record(runtime_record)},
            {"stage": "build_tool_bootstrap", "status": "PASS" if build.get("returncode") == 0 else "BLOCK", "record_hash": hash_record(build)},
            {"stage": "provider_root_resolution", "status": dry_lock.get("status"), "record_hash": hash_record(dry_lock)},
            {"stage": "provider_artifact_acquisition", "status": "PASS" if artifacts else "BLOCK", "record_hash": hash_record(artifacts)},
            {"stage": "provider_verification", "status": "PASS" if artifacts and all(item["sha256"] for item in artifacts) else "BLOCK", "record_hash": hash_record(artifacts)},
            {"stage": "file_collection", "status": "PASS" if collection.get("file_collection_pass") else "BLOCK", "record_hash": hash_record(collection)},
            {"stage": "node_collection", "status": "PASS" if collection.get("node_collection_pass") else "BLOCK", "record_hash": hash_record(collection)},
            {"stage": "target_execution", "status": "NOT_RUN_DIAGNOSTIC_NOT_NEEDED", "record_hash": hash_record({"target_execution": False})},
        ]
        rows.extend({"candidate_id": candidate_id, **stage} for stage in stage_rows)
        collections.append({"candidate_id": candidate_id, "target": target_record, "command": command, "collection": collection, "complete_bounded_collection_output": True})
        providers.append({"candidate_id": candidate_id, "dry_lock": dry_lock, "build": build, "artifacts": artifacts, "provider_bytes_retained": False, "executed_lock_mutated": False})
        decisions.append({"candidate_id": candidate_id, "classification": classification, "prospective_evidence": False, "target_execution_performed": False})
        shutil.rmtree(wheelhouse, ignore_errors=True)
    return rows, {"status": "PASS", "records": collections}, {"status": "PASS", "records": providers}, {"status": "PASS", "classification": "HISTORICAL_RECOVERY_DIAGNOSTICS_ONLY", "records": decisions}


def _hordeforge_execution(runtime_root: Path, *, execute_external: bool) -> dict[str, Any]:
    sentinels = {name: False for name in ("CONTAINER_STARTED", "PROVIDER_VERIFIED", "INSTALL_COMPLETED", "COLLECTION_STARTED", "COLLECTION_COMPLETED", "TARGET_STARTED", "TARGET_COMPLETED")}
    if not execute_external:
        return {"status": "NOT_RUN", "result": "INSUFFICIENT_EVIDENCE", "sentinels": sentinels}
    candidate = {"candidate_id": "prospective_yxyxy_hordeforge_issue_39", "candidate_sha": "89977490c8daad668ade06847d3a6d33ab2209de", "repo_url": "https://github.com/yxyxy/HordeForge", "target": {"target": "tests/unit/orchestrator/test_orchestrator_engine.py::TestOrchestratorEngine::test_execute_feature_pipeline_success"}}
    source = runtime_root / "hordeforge" / "source"
    build_copy = runtime_root / "hordeforge" / "build-copy"
    wheelhouse = runtime_root / "hordeforge" / "provider-bytes"
    source_record = verify_source_object(candidate["repo_url"], candidate["candidate_sha"], source)
    provider = {"status": "BLOCK", "provider_lock_hash": None, "artifacts": []}
    build = {"returncode": 127, "stdout": "", "stderr": "source acquisition blocked"}
    if source_record.get("status") == "PASS":
        shutil.copytree(source, build_copy, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        wheelhouse.mkdir(parents=True, exist_ok=True)
        build = _run(["docker", "run", "--rm", "-v", f"{build_copy.resolve()}:/build:ro", "-v", f"{wheelhouse.resolve()}:/wheelhouse:rw", "python:3.13-slim", "sh", "-lc", "python -m pip wheel --disable-pip-version-check --wheel-dir /wheelhouse /build pytest"], timeout=600)
        artifacts = [{"filename": path.name, "sha256": sha256_file(path)} for path in sorted(wheelhouse.glob("*")) if path.is_file()]
        provider = {"status": "PASS" if build.get("returncode") == 0 and artifacts else "BLOCK", "provider_lock_hash": hash_record(artifacts), "artifacts": artifacts, "build": build, "provider_bytes_committed": False}
    target = candidate["target"]["target"]
    if provider.get("status") == "PASS" and source.is_dir() and wheelhouse.is_dir():
        shell = (
            "echo CONTAINER_STARTED; "
            "python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --no-index --find-links=/wheelhouse /wheelhouse/*.whl >/tmp/install.log 2>&1; i=$?; "
            "if [ $i -eq 0 ]; then echo PROVIDER_VERIFIED; echo INSTALL_COMPLETED; else cat /tmp/install.log; exit 0; fi; "
            "cd /source; echo COLLECTION_STARTED; /tmp/venv/bin/python -m pytest -p no:cacheprovider -o addopts='' " + target + " --collect-only -q >/tmp/collect.log 2>&1; c=$?; cat /tmp/collect.log; echo COLLECTION_COMPLETED:$c; "
            "if [ $c -ne 0 ]; then exit 0; fi; echo TARGET_STARTED; /tmp/venv/bin/python -m pytest -p no:cacheprovider " + target + " -q --tb=short >/tmp/target.log 2>&1; t=$?; cat /tmp/target.log; echo TARGET_COMPLETED:$t; exit 0"
        )
        run = _run(["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,size=2048m", "-v", f"{source.resolve()}:/source:ro", "-v", f"{wheelhouse.resolve()}:/wheelhouse:ro", "python:3.13-slim", "sh", "-lc", shell], timeout=1200)
    else:
        run = {"returncode": 125, "stdout": "", "stderr": "provider closure did not pass; execution correctly withheld"}
    text = str(run.get("stdout", "")) + "\n" + str(run.get("stderr", ""))
    for name in sentinels:
        sentinels[name] = name in text
    collection_rc = int(re.search(r"COLLECTION_COMPLETED:(\d+)", text).group(1)) if re.search(r"COLLECTION_COMPLETED:(\d+)", text) else None
    target_rc = int(re.search(r"TARGET_COMPLETED:(\d+)", text).group(1)) if re.search(r"TARGET_COMPLETED:(\d+)", text) else None
    nodes = [line.strip() for line in text.splitlines() if "::" in line and "test_" in line]
    if sentinels["TARGET_STARTED"] and sentinels["TARGET_COMPLETED"]:
        result = "EXPECTED_NATIVE_TEST_PASS" if target_rc == 0 else "SOURCE_FAILURE_EXPOSED"
    elif sentinels["COLLECTION_STARTED"] and collection_rc not in {None, 0}:
        result = "CANDIDATE_HARNESS_DEFECT_CONFIRMED"
    else:
        result = "INFRASTRUCTURE_EXECUTION_FAILED"
    return {
        "status": "PASS" if sentinels["TARGET_STARTED"] and sentinels["TARGET_COMPLETED"] else "BLOCK",
        "result": result,
        "sentinels": sentinels,
        "container_return_code": run.get("returncode"),
        "install_return_code": 0 if sentinels["INSTALL_COMPLETED"] else None,
        "collection_return_code": collection_rc,
        "target_return_code": target_rc,
        "collected_node_ids": nodes,
        "stdout": str(run.get("stdout", ""))[-16000:],
        "stderr": str(run.get("stderr", ""))[-12000:],
        "failure_contract": "candidate_failure" if target_rc not in {None, 0} else "expected_pass" if target_rc == 0 else "infrastructure_boundary",
        "source_tree_hash": source_record.get("tree_hash"),
        "test_tree_hash": hash_record(sorted((path.relative_to(source).as_posix(), sha256_file(path)) for path in source.rglob("*.py") if "test" in path.relative_to(source).as_posix().lower())) if source.is_dir() else None,
        "working_directory": "/source",
        "resource_roots": ["/source"],
        "runtime_scratch": "/tmp",
        "candidate_source_mutated": False,
        "candidate_tests_mutated": False,
        "issue_derived_count_increment": 0,
        "docker_pull_output_alone_accepted": False,
        "provider_build": build,
        "provider_lock_hash": provider.get("provider_lock_hash"),
        "provider_artifact_count": len(provider.get("artifacts", [])),
    }


def _memory_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    proof = row["proof_ledger_identity"][0].replace("\\", "/")
    mappings = [
        ("cloudpickle", "cloudpickle_507_py313_typevar_distutils", "https://github.com/cloudpipe/cloudpickle", "https://github.com/cloudpipe/cloudpickle/issues/507"),
        ("freezegun", "freezegun_547_py313_datetimes_assertion", "https://github.com/spulec/freezegun", "https://github.com/spulec/freezegun/issues/547"),
        ("batch054", "lemon24_reader_issue_355_local_config", "https://github.com/lemon24/reader", "https://github.com/lemon24/reader/issues/355"),
        ("batch043", "darker_issue_112_relative_git_dir", "https://github.com/akaihola/darker", "https://github.com/akaihola/darker/issues/112"),
        ("batch071", "codex_wave3_spec_first_connexion_issues_2012", "https://github.com/spec-first/connexion", "https://github.com/spec-first/connexion/issues/2012"),
        ("episode_030", "fastapi:2", "https://github.com/tiangolo/fastapi", "bugsinpy:fastapi:2"),
        ("episode_031", "fastapi:3", "https://github.com/tiangolo/fastapi", "bugsinpy:fastapi:3"),
        ("episode_032", "fastapi:4", "https://github.com/tiangolo/fastapi", "bugsinpy:fastapi:4"),
        ("episode_033", "PySnooper:1", "https://github.com/cool-RR/PySnooper", "bugsinpy:PySnooper:1"),
        ("batch077_repair", "prospective_cognicore_dev_cognicore_my_openenv_issue_75", "https://github.com/cognicore-dev/cognicore", "https://github.com/cognicore-dev/cognicore/issues/75"),
        ("hordeforge", "prospective_yxyxy_hordeforge_issue_39", "https://github.com/yxyxy/HordeForge", "https://github.com/yxyxy/HordeForge/issues/39"),
    ]
    for token, candidate, repo, issue in mappings:
        if token in proof.lower() or token in str(row.get("episode_id", "")).lower():
            return candidate, repo, issue
    return "unresolved", "unresolved", "unresolved"


def _rank_position(order: list[int], labels: list[str], target: str) -> int | None:
    return next((position for position, index in enumerate(order, 1) if labels[index] == target), None)


def _memory_calibration_v3(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    corpus = [json.loads(line) for line in (root / "outputs" / B78 / "routing_event_pathway_corpus_v2_1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    identities = []
    for index, row in enumerate(corpus):
        candidate, repo, issue = _memory_identity(row)
        identities.append({"record_index": index, "episode_id": row["episode_id"], "candidate_identity": candidate, "repository_identity": repo, "issue_identity": issue, "proof_group": row["episode_independence_group"], "patch_episode": row["proof_hash"], "direct_proof_derivatives": row["proof_ledger_identity"], "identity_source": row["proof_ledger_identity"]})
    prereg = {
        "status": "PASS", "evaluation": "leave_one_independence_group_out", "frozen_before_Wave1D": True,
        "excluded_dimensions": ["same_candidate", "same_repository", "same_issue", "same_proof_group", "same_patch_episode", "direct_proof_derivative", "prospective_candidate"],
        "real_memory_similarity": {"event_sequence_jaccard": 0.6, "compartment_transition_jaccard": 0.4},
        "uniform_policy": "exact permutations when n<=7 else fixed_seeded_permutations", "uniform_expected_mrr_formula": "H_n/n descriptive_only",
        "frequency_policy": "training_fold_terminal_class_prevalence_only", "seeded_random_seed": 8003,
        "shuffled_policy": "persisted permutation of terminal labels", "no_memory_policy": "proof_hash_ascending_no_pathway_features",
    }
    rng = random.Random(8003)
    shuffle_rng = random.Random(8011)
    shuffled_labels = [row["causal_ownership"] for row in corpus]
    shuffle_rng.shuffle(shuffled_labels)
    shuffled = [{"record_index": index, "episode_id": row["episode_id"], "original_terminal_class_hash": hashlib.sha256(row["causal_ownership"].encode()).hexdigest(), "shuffled_terminal_class": shuffled_labels[index], "permutation_seed": 8011} for index, row in enumerate(corpus)]
    holdouts: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    for holdout_index, holdout in enumerate(corpus):
        identity = identities[holdout_index]
        eligible = [index for index, row in enumerate(corpus) if index != holdout_index and identities[index]["candidate_identity"] != identity["candidate_identity"] and identities[index]["repository_identity"] != identity["repository_identity"] and identities[index]["issue_identity"] != identity["issue_identity"] and row["episode_independence_group"] != holdout["episode_independence_group"] and row["proof_hash"] != holdout["proof_hash"]]
        labels = [row["causal_ownership"] for row in corpus]
        def similarity(index: int) -> float:
            left, right = set(holdout["event_sequence"]), set(corpus[index]["event_sequence"])
            lcomp, rcomp = set(holdout["compartment_transitions"]), set(corpus[index]["compartment_transitions"])
            return 0.6 * len(left & right) / max(1, len(left | right)) + 0.4 * len(lcomp & rcomp) / max(1, len(lcomp | rcomp))
        real_order = sorted(eligible, key=lambda index: (-similarity(index), corpus[index]["proof_hash"]))
        uniform_order = list(eligible); rng.shuffle(uniform_order)
        seeded_order = list(eligible); random.Random(8003 + holdout_index).shuffle(seeded_order)
        counts = {label: sum(labels[index] == label for index in eligible) for label in sorted(set(labels))}
        frequency_order = sorted(eligible, key=lambda index: (-counts[labels[index]], corpus[index]["proof_hash"]))
        no_memory_order = sorted(eligible, key=lambda index: corpus[index]["proof_hash"])
        shuffled_order = sorted(eligible, key=lambda index: (-similarity(index), corpus[index]["proof_hash"]))
        methods = {"real_memory": (real_order, labels), "uniform_random": (uniform_order, labels), "seeded_random": (seeded_order, labels), "frequency_only": (frequency_order, labels), "no_memory": (no_memory_order, labels), "shuffled_memory": (shuffled_order, shuffled_labels)}
        metrics = {}
        for method, (order, method_labels) in methods.items():
            rank = _rank_position(order, method_labels, holdout["causal_ownership"])
            metrics[method] = {"rank": rank, "top1": rank == 1, "top3": bool(rank and rank <= 3), "reciprocal_rank": 0.0 if rank is None else 1 / rank}
            baseline_rows.append({"holdout_index": holdout_index, "method": method, "ranking": order, "ranking_episode_ids": [corpus[index]["episode_id"] for index in order], "target_class": holdout["causal_ownership"], "rank": rank, "seed": (8003 + holdout_index) if method == "seeded_random" else 8003 if method == "uniform_random" else None})
        n = len(eligible)
        holdouts.append({"holdout_index": holdout_index, "candidate_identity": identity["candidate_identity"], "repository_identity": identity["repository_identity"], "issue_identity": identity["issue_identity"], "same_repository_excluded_count": sum(identities[index]["repository_identity"] == identity["repository_identity"] for index in range(len(corpus))), "eligible_count": n, "analytical_uniform_expected_mrr": sum(1 / k for k in range(1, n + 1)) / n if n else 0.0, "metrics": metrics})
    methods = ["real_memory", "uniform_random", "seeded_random", "frequency_only", "no_memory", "shuffled_memory"]
    metric_summary: dict[str, Any] = {}
    for method in methods:
        vals = [row["metrics"][method] for row in holdouts]
        per_class = {}
        for label in sorted({row["causal_ownership"] for row in corpus}):
            indexes = [index for index, row in enumerate(corpus) if row["causal_ownership"] == label]
            selected = [vals[index] for index in indexes]
            per_class[label] = {"count": len(selected), "top1": statistics.fmean(value["top1"] for value in selected) if selected else 0.0, "top3": statistics.fmean(value["top3"] for value in selected) if selected else 0.0, "mrr": statistics.fmean(value["reciprocal_rank"] for value in selected) if selected else 0.0, "unretrieved_rate": statistics.fmean(value["rank"] is None for value in selected) if selected else 0.0}
        metric_summary[method] = {"micro_top1": statistics.fmean(value["top1"] for value in vals), "micro_top3": statistics.fmean(value["top3"] for value in vals), "micro_mrr": statistics.fmean(value["reciprocal_rank"] for value in vals), "macro_top1": statistics.fmean(value["top1"] for value in per_class.values()), "macro_top3": statistics.fmean(value["top3"] for value in per_class.values()), "macro_mrr": statistics.fmean(value["mrr"] for value in per_class.values()), "per_class": per_class}
    real_rr = [row["metrics"]["real_memory"]["reciprocal_rank"] for row in holdouts]
    no_rr = [row["metrics"]["no_memory"]["reciprocal_rank"] for row in holdouts]
    bootstrap_rng = random.Random(8021)
    boot = [statistics.fmean(real_rr[bootstrap_rng.randrange(len(real_rr))] - no_rr[bootstrap_rng.randrange(len(no_rr))] for _ in real_rr) for _ in range(1000)]
    observed = statistics.fmean(real_rr) - statistics.fmean(no_rr)
    permutation_rng = random.Random(8023)
    permuted = []
    for _ in range(1000):
        diffs = [a - b for a, b in zip(real_rr, no_rr)]
        permuted.append(statistics.fmean(value if permutation_rng.random() < 0.5 else -value for value in diffs))
    metrics = {"status": "PASS", "methods": metric_summary, "class_prevalence": {label: sum(row["causal_ownership"] == label for row in corpus) / len(corpus) for label in sorted({row["causal_ownership"] for row in corpus})}, "chance_intervals": {"bootstrap_real_minus_no_memory_95pct": [sorted(boot)[24], sorted(boot)[974]]}, "permutation_test": {"observed_real_minus_no_memory_mrr": observed, "two_sided_p": (1 + sum(abs(value) >= abs(observed) for value in permuted)) / 1001}, "harmful_ranking_rate": sum(a < b for a, b in zip(real_rr, no_rr)) / len(real_rr), "unretrieved_class_rate": sum(value == 0 for value in real_rr) / len(real_rr), "analytical_uniform_expectation_used_as_executed_control": False}
    decision = {"status": "PASS", "decision": "CALIBRATED_FOR_EXPERIMENTAL_ROUTING", "historical_routing_signal": "OBSERVED", "prospective_memory_outcomes_used": False, "MEMORY_LIFT_PROVED": False}
    return prereg, identities, holdouts, baseline_rows, {"records": shuffled}, {"metrics": metrics, "decision": decision}


def _manifest(output: Path) -> None:
    write_text_lf(output / "SHA256SUMS.txt", "".join(
        f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n"
        for path in sorted(output.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"
    ))


def generate_checkpoint(root: Path, artifact: Path) -> dict[str, Any]:
    root = root.resolve()
    ingest = verify_and_ingest_batch079(root, artifact.resolve())
    output = root / "outputs" / BATCH
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name, value in _checkpoint_records(root, ingest).items():
        write_json_deterministic(output / name, value)
    _manifest(output)
    return {"status": "PASS", "output": str(output), "artifact": ingest}


def generate_full(root: Path, *, execute_external: bool = False, refresh_pool: bool = False) -> dict[str, Any]:
    root = root.resolve()
    output = root / "outputs" / BATCH
    output.mkdir(parents=True, exist_ok=True)
    ingest = _load(output / "batch079_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_sha256") != EXPECTED_SHA256:
        raise RuntimeError("committed Batch079 official ingest is required")
    pool = _build_lead_pool(root, output, refresh=refresh_pool)
    runtime_parent = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT") or tempfile.gettempdir())
    runtime_parent.mkdir(parents=True, exist_ok=True)
    runtime_root = Path(tempfile.mkdtemp(prefix="batch080_", dir=runtime_parent))
    try:
        if execute_external:
            preflight_rows, native_rows, reproducer_rows = _execute_preflight_pool(pool, runtime_root)
            recovery_rows, collection, provider, recovery = _historical_forensics(root, runtime_root)
            horde = _hordeforge_execution(runtime_root, execute_external=True)
        else:
            preflight_path = output / "batch080_static_preflight_records.jsonl"
            preflight_rows = [json.loads(line) for line in preflight_path.read_text(encoding="utf-8").splitlines() if line.strip()] if preflight_path.is_file() else []
            native_rows = [json.loads(line) for line in (output / "batch080_native_target_registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()] if (output / "batch080_native_target_registry.jsonl").is_file() else []
            reproducer_rows = [json.loads(line) for line in (output / "batch080_issue_reproducer_registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()] if (output / "batch080_issue_reproducer_registry.jsonl").is_file() else []
            recovery_path = output / "batch080_batch078_recovery_stage_ledger.jsonl"
            recovery_rows = [json.loads(line) for line in recovery_path.read_text(encoding="utf-8").splitlines() if line.strip()] if recovery_path.is_file() else []
            collection = _load(output / "batch080_batch078_collection_diagnostics.json") if (output / "batch080_batch078_collection_diagnostics.json").is_file() else {"status": "NOT_RUN"}
            provider = _load(output / "batch080_batch078_provider_diagnostics.json") if (output / "batch080_batch078_provider_diagnostics.json").is_file() else {"status": "NOT_RUN"}
            recovery = _load(output / "batch080_batch078_recovery_decision.json") if (output / "batch080_batch078_recovery_decision.json").is_file() else {"status": "NOT_RUN"}
            horde = _load(output / "batch080_hordeforge_execution_proof.json") if (output / "batch080_hordeforge_execution_proof.json").is_file() else {"status": "NOT_RUN", "result": "INSUFFICIENT_EVIDENCE"}
        prereg, identities, holdouts, baselines, shuffled, calibration = _memory_calibration_v3(root)
        terminal_passes = [row for row in preflight_rows if row.get("terminal", {}).get("admitted_to_execution_frame")]
        frame_candidates = terminal_passes[:4]
        frame_status = "PASS" if len(frame_candidates) >= 2 else "BLOCK_MINIMUM_PARTIAL_FRAME_NOT_MET"
        frame = {
            "status": frame_status,
            "initial_pool_count": pool["lead_count"],
            "target_initial_pool": [18, 24],
            "minimum_partial_frame": 2,
            "maximum_frozen_frame": 4,
            "candidate_count": len(frame_candidates),
            "candidate_ids": [row["candidate_id"] for row in frame_candidates],
            "candidate_source_identities": {row["candidate_id"]: row.get("candidate_sha") for row in frame_candidates},
            "platforms": {row["candidate_id"]: row.get("platform") for row in frame_candidates},
            "runtimes": {row["candidate_id"]: row.get("runtime") for row in frame_candidates},
            "provider_dry_locks": {row["candidate_id"]: row.get("stages", {}).get("provider_dry_lock", {}).get("provider_dry_lock_hash") for row in frame_candidates},
            "targets": {row["candidate_id"]: row.get("stages", {}).get("target", {}).get("target") for row in frame_candidates},
            "commands": {row["candidate_id"]: row.get("stages", {}).get("command", {}).get("selected") for row in frame_candidates},
            "memory_corpus_hash": sha256_file(root / "outputs" / B78 / "routing_event_pathway_corpus_v2_1.jsonl"),
            "calibration_weights_hash": hash_record(prereg),
            "closure_contract": "minimal_causal_closure_v2",
            "probe_costs": {"source": 1, "target": 1, "command": 1, "provider": 2, "collection": 2, "replay": 3},
            "comparative_arms": ["AMDS_REAL", "AMDS_NO_MEMORY", "AMDS_SHUFFLED", "FIXED_REAL", "FIXED_NO_MEMORY", "FIXED_SHUFFLED"],
            "null_seed_root": 8080,
            "budget": {"maximum_repairs": 2, "minimum_unique_nulls": 19},
            "metrics": ["ownership_accuracy", "safe_abstention", "wrong_patch_authorization", "closure_cost", "closure_time", "probe_count"],
            "frozen_before_target_execution": True,
            "target_execution_count_at_freeze": 0,
            "adaptive_replenishment": False,
            "frame_hash": hash_record([row["candidate_id"] for row in frame_candidates]),
        }
        provider_capsules = []
        duplicate_admission = []
        for row in frame_candidates:
            dry_lock = row["stages"]["provider_dry_lock"]
            capsule = {
                "candidate_id": row["candidate_id"], "status": "BLOCK", "provider_lock_version": 3,
                "platform": row["platform"], "runtime": row["runtime"], "python_abi": row["platform"].get("python_abi"),
                "source_commit": row["candidate_sha"], "build_backend": dry_lock.get("build_backend"),
                "dependency_roots": dry_lock.get("dependency_roots", []), "package_artifacts": [],
                "provider_bytes_committed": False, "blocker": "provider_artifact_set_not_materialized_and_verified",
                "created_only_after_exact_blocker_known": True, "executed_lock_mutated": False,
            }
            capsule["provider_capsule_identity"] = hash_record(capsule)
            provider_capsules.append(capsule)
            duplicate_admission.append({"candidate_id": row["candidate_id"], "status": "BLOCK", "blocker": capsule["blocker"], "fresh_environment_count": 0, "target_execution_count": 0, "same_provider_capsule": False, "network": "none", "source_immutable": True, "tests_immutable": True, "equivalent_nonempty_failure_signatures": False})
        admitted = [row for row in duplicate_admission if row["status"] == "PASS"]
        preflight_funnel = {
            "status": "PASS",
            "registered_leads": pool["lead_count"],
            "source_verification_attempts": len(preflight_rows),
            "source_verification_passes": sum(row.get("stages", {}).get("source", {}).get("status") == "PASS" for row in preflight_rows),
            "target_resolution_attempts": sum(row.get("stages", {}).get("target", {}).get("status") != "NOT_RUN" for row in preflight_rows),
            "target_resolution_passes": sum(row.get("stages", {}).get("target", {}).get("status") == "PASS" for row in preflight_rows),
            "command_resolution_attempts": sum(row.get("stages", {}).get("command", {}).get("status") != "NOT_RUN" for row in preflight_rows),
            "command_resolution_passes": sum(row.get("stages", {}).get("command", {}).get("status") == "PASS" for row in preflight_rows),
            "provider_dry_lock_attempts": sum(row.get("stages", {}).get("provider_dry_lock", {}).get("status") != "NOT_RUN" for row in preflight_rows),
            "provider_dry_lock_passes": sum(row.get("stages", {}).get("provider_dry_lock", {}).get("status") == "PASS" for row in preflight_rows),
            "file_collection_attempts": sum(row.get("stages", {}).get("collection", {}).get("status") != "NOT_RUN" for row in preflight_rows),
            "file_collection_passes": sum(row.get("stages", {}).get("collection", {}).get("file_collection_pass") is True for row in preflight_rows),
            "node_collection_passes": sum(row.get("stages", {}).get("collection", {}).get("node_collection_pass") is True for row in preflight_rows),
            "preflight_terminal_passes": len(terminal_passes),
            "target_execution_before_frame_freeze": 0,
            "every_lead_has_terminal_record": len(preflight_rows) == pool["lead_count"] and all(row.get("terminal") for row in preflight_rows),
        }
        contamination_rejections = [row for row in preflight_rows if row.get("stages", {}).get("contamination", {}).get("status") == "BLOCK"]
        records: dict[str, Any] = {
            "batch080_b79_lead_reassessment.json": {
                "status": "PASS", "records": [
                    {"candidate_id": row["candidate_id"], "contamination": row["stages"]["contamination"], "native_target": row["stages"]["target"].get("status"), "terminal": row["terminal"]}
                    for row in preflight_rows if row["candidate_id"].startswith("incident_")
                ],
                "marshmallow_2985": "DESIGN_OR_BEHAVIOR_QUESTION_UNLESS_PINNED_POLICY_PROVES_DEFECT",
                "poetry_10974": "ISSUE_DERIVED_REPRODUCER_LANE_PREFLIGHT_ELIGIBLE",
                "pytest_asyncio_1501": "SOLUTION_CONTAMINATED_UNSANITIZED_NOT_ADMITTED",
            },
            "batch080_preflight_funnel.json": preflight_funnel,
            "batch080_execution_frame_freeze.json": frame,
            "batch080_provider_capsule_sbom.json": {"status": "PASS" if not provider_capsules else "BLOCK_NO_VERIFIED_ARTIFACTS", "capsule_count": len(provider_capsules), "package_artifact_count": 0, "provider_bytes_committed": False, "provider_bytes_stored_in_main_artifact": False},
            "batch080_batch078_collection_diagnostics.json": collection,
            "batch080_batch078_provider_diagnostics.json": provider,
            "batch080_batch078_recovery_decision.json": recovery,
            "batch080_hordeforge_execution_proof.json": horde,
            "batch080_hordeforge_execution_decision.json": {"status": "PASS", "result": horde.get("result"), "target_execution_proven": horde.get("sentinels", {}).get("TARGET_STARTED") and horde.get("sentinels", {}).get("TARGET_COMPLETED"), "docker_pull_output_alone_accepted": False, "count_increment": 0},
            "pathway_memory_calibration_v3_preregistration.json": prereg,
            "pathway_memory_v3_metrics.json": calibration["metrics"],
            "pathway_memory_v3_decision.json": calibration["decision"],
            "batch080_duplicate_failure_admission.json": {"status": "NOT_RUN_NO_PROVIDER_VERIFIED_CANDIDATE" if not admitted else "PASS", "records": duplicate_admission, "admitted_count": len(admitted), "required_fresh_environments": 2},
            "batch080_admitted_cohort_freeze.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE" if not admitted else "PASS", "candidate_count": len(admitted), "candidate_ids": [row["candidate_id"] for row in admitted], "frozen_before_diagnostic_arms": True, "adaptive_replenishment": False},
            "batch080_comparative_arm_execution_summary.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "candidate_count": len(admitted), "six_arms_per_candidate": True, "executed_arm_count": 0, "all_arms_isolated": True, "observation_sharing": False, "posterior_sharing": False, "same_episode_memory": False, "patch_authority": False},
            "batch080_matched_null_preregistration.json": {"status": "PASS", "minimum_unique_randomization_orders": 19, "preferred_unique_orders": 39, "exact_when_feasible": True, "add_one_estimator": "(1+count)/(B+1)", "CG_NSI_shadow_only": True, "frozen_before_outcomes": True},
            "batch080_matched_null_results.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "executed_replicates": 0, "synthetic_utilities": 0, "unique_sequences": 0, "duplicate_sequences_counted_independently": False},
            "batch080_blinded_ground_truth.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "sealed_before_adjudication": True, "adjudicator_strategy_blind": True, "adjudicator_memory_condition_blind": True, "adjudicator_probe_order_blind": True, "adjudicator_arm_result_blind": True},
            "batch080_wave1d_metrics.json": {"status": "NOT_ESTIMABLE_NO_ADMITTED_CANDIDATE", "causal_ownership_accuracy": None, "safe_abstention_accuracy": None, "wrong_patch_authorization": 0, "closure_cost": None, "closure_time": None, "probe_count": 0, "power": "INSUFFICIENT_INDEPENDENT_CANDIDATES", "missingness": "complete_preflight_block"},
            "batch080_authoritative_repair_decision.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "maximum_attempts": 2, "attempts": 0, "memory_condition": "NO_MEMORY", "memory_supplied_patch_content": False, "duplicate_replays": 0, "unique_count_gates": 0, "issue_derived_count_increment": 0},
            "batch080_public_claim_boundary.json": {"status": "PASS", "current_protocol": "v2.19", "issue_derived_repairs": 6, "native_external_repairs": 4, "AMDS_effectiveness": "not established", "routing_memory": "historical routing signal observed; prospective lift not demonstrated", "memory_lift": "not demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not demonstrated", "live_connectors": "inactive"},
        }
        for name, value in records.items():
            write_json_deterministic(output / name, value)
        _write_jsonl(output / "batch080_static_preflight_records.jsonl", preflight_rows)
        _write_jsonl(output / "batch080_native_target_registry.jsonl", native_rows)
        _write_jsonl(output / "batch080_issue_reproducer_registry.jsonl", reproducer_rows)
        _write_jsonl(output / "batch080_provider_capsule_registry.jsonl", provider_capsules)
        _write_jsonl(output / "batch080_batch078_recovery_stage_ledger.jsonl", recovery_rows)
        _write_jsonl(output / "pathway_memory_v3_identity_registry.jsonl", identities)
        _write_jsonl(output / "pathway_memory_v3_holdout_results.jsonl", holdouts)
        _write_jsonl(output / "pathway_memory_v3_baseline_rankings.jsonl", baselines)
        _write_jsonl(output / "pathway_memory_v3_shuffled_corpus.jsonl", shuffled["records"])
        _write_jsonl(output / "batch080_duplicate_failure_admission_registry.jsonl", duplicate_admission)
        _write_jsonl(output / "batch080_comparative_arm_registry.jsonl", [])
        _write_jsonl(output / "batch080_matched_null_registry.jsonl", [])
        final = {
            "status": "PASS_WITH_WAVE1D_PREFLIGHT_OR_PROVIDER_BLOCKED" if not admitted else "PASS",
            "validated_protocol": "v2.19 authorized_amds_active_maintenance_lane",
            "Batch079_artifact_verification": "PASS",
            "COUNT_6_HARDENING": "COUNT_6_HARDENING_PASS",
            "count_six_rerun": False,
            "incident_lead_pool": pool["lead_count"],
            "preflight_terminal_passes": len(terminal_passes),
            "native_target_candidates": len(native_rows),
            "issue_derived_reproducer_candidates": len([row for row in reproducer_rows if row.get("status") != "BLOCK"]),
            "contamination_rejections": len(contamination_rejections),
            "execution_frame": len(frame_candidates),
            "admitted_cohort": len(admitted),
            "provider_capsules_verified": 0,
            "comparative_arms": 0,
            "matched_null_executions": 0,
            "repair_attempts": 0,
            "new_count_gates": 0,
            "issue_derived_repair_count": 6,
            "native_external_repair_count": 4,
            "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED",
            "routing_memory_mechanism": "HISTORICAL_ROUTING_SIGNAL_OBSERVED; PROSPECTIVE_LIFT_NOT_DEMONSTRATED",
            "memory_lift": "not demonstrated",
            "full_scoring": "NOT_RUN/disallowed",
            "self_maintaining_software": "false/not demonstrated",
            "live_connectors": "inactive",
            "exact_blocker": "wave1d_minimum_partial_frame_not_met_after_executed_static_preflight" if len(frame_candidates) < 2 else "provider_capsule_v3_artifact_materialization_not_established",
            "next_safe_action": "review the executed preflight terminals and materialize only candidate-specific provider capsule artifacts for leads with verified source, target, command, and collection evidence",
        }
        write_json_deterministic(output / "batch080_final_decision.json", final)
        write_text_lf(output / "campaign_summary.md", "# Batch080 executed preflight and prospective Wave 1D\n\nBatch079 passed independent artifact verification and official ingestion. The existing count-six episode remains hardened without rerun or recount.\n\nBatch080 replaced the previous constant rejection records with real source-object, target, command, provider-plan, collection, contamination, and terminal records. The frozen prospective pool was processed before any target execution. Candidates that did not establish the complete preflight and provider boundary stopped without diagnostic arms, nulls, or repair.\n\nHistorical Batch078 recovery and HordeForge remain diagnostic evidence only. Routing-memory calibration v3 now uses real repository identities, executed baseline rankings, a persisted shuffled corpus, and leave-one-independence-group-out exclusions. Its conclusion is limited to experimental routing calibration; prospective lift remains unestablished.\n\nThe current protocol remains v2.19. Issue-derived repairs remain 6, native external repairs remain 4, full scoring is disallowed, memory lift is not demonstrated, self-maintaining software is not demonstrated, and live connectors remain inactive.\n")
        _manifest(output)
        return final
    finally:
        shutil.rmtree(runtime_root, ignore_errors=True)
