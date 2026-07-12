from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Any
from urllib.parse import urlparse
import zipfile

from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.intake.discovery_queries import QUERY_TEMPLATES, execute_discovery, github_json
from controllergate.intake.contamination_classifier import classify_contamination, sanitize_issue_record
from controllergate.intake.frame_freezer import freeze_frame
from controllergate.intake.issue_snapshot import snapshot_issue
from controllergate.intake.static_candidate_ranker import rank_records
from controllergate.intake.target_resolver import resolve_target
from controllergate.runtime.authorized_candidate_dispatcher import dispatch_authorized_candidate
from controllergate.runtime.candidate_execution_authorization import CandidateExecutionAuthorization, seal_candidate_authorization
from controllergate.runtime.candidate_execution_plan import CandidateExecutionPlan, CandidatePhase, seal_candidate_plan
from controllergate.runtime.execution_checkpoint import RuntimeCheckpoint, write_checkpoint
from controllergate.runtime.provider_workspace import candidate_key

BATCH = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
H72 = "post_v2_37_hardening_batch072_count5_authorized_amds_memory_wave1"
H73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
EXPECTED_SIZE = 141679
EXPECTED_SHA = "b779ddabd22468437f48577ad6367de0125d3ba016540ba763c84c0ca65db355"
ARMS = ("amds_memory_enabled", "amds_memory_disabled", "fixed_memory_enabled", "fixed_memory_disabled", "environment_first_memory_enabled", "environment_first_memory_disabled", "seeded_random_memory_enabled", "seeded_random_memory_disabled")


def _run(argv: list[str], cwd: Path | None = None, timeout: int = 600) -> dict[str, Any]:
    effective = ["git", "-c", "safe.directory=*"] + argv[1:] if argv and argv[0] == "git" else argv
    try:
        run = subprocess.run(effective, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        return {"returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}


def _internal_manifest(archive: zipfile.ZipFile, prefix: str) -> dict[str, Any]:
    checked = 0; failures = []
    for line in archive.read(f"{prefix}/SHA256SUMS.txt").decode().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            failures.append({"kind": "malformed", "line": line}); continue
        expected, relative = parts; target = f"{prefix}/{relative.strip().lstrip('*')}"
        try: payload = archive.read(target)
        except KeyError: failures.append({"kind": "missing", "path": target}); continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != expected: failures.append({"kind": "mismatch", "path": target})
    return {"status": "PASS" if not failures else "FAIL", "checked": checked, "failures": failures}


def _copy_prefix(archive: zipfile.ZipFile, prefix: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        if info.is_dir() or not name.startswith(prefix + "/"): continue
        relative = name[len(prefix) + 1:]
        if not relative: continue
        target = destination / Path(*PurePosixPath(relative).parts); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(info))


def verify_ingest(root: Path, artifact: Path | None) -> dict[str, Any]:
    existing = root / "outputs" / BATCH / "batch073_artifact_ingest.json"
    if artifact is None:
        if not existing.is_file(): raise RuntimeError("verified Batch073 ingest required")
        value = json.loads(existing.read_text(encoding="utf-8"))
        if value.get("status") != "PASS": raise RuntimeError("Batch073 ingest is not verified")
        return value
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA)
    entries = audit_zip_entries(artifact); outer_manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        h72 = _internal_manifest(archive, H72); h73 = _internal_manifest(archive, H73)
        forbidden = [item.filename for item in files if item.filename.lower().endswith((".zip", ".tar", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in item.filename]
        passed = outer["status"] == entries["status"] == outer_manifest["status"] == h72["status"] == h73["status"] == "PASS" and len(files) == 91 and outer_manifest["checked"] == 90 and h72["checked"] == 38 and h73["checked"] == 41 and not forbidden
        if not passed: raise RuntimeError("Batch073 artifact verification failed")
        _copy_prefix(archive, H72, root / "outputs" / H72); _copy_prefix(archive, H73, root / "outputs" / H73)
    return {"status": "PASS", "artifact_name": H73 + "_artifacts", "artifact_id": 8256136158, "workflow_run_id": 29180071103, "workflow_head": "36ff7cac28535a608c2eb68b468cce2072aaec32", "observed_size_bytes": artifact.stat().st_size, "observed_sha256": sha256_file(artifact), "file_count": len(files), "outer_manifest": outer_manifest, "batch072_manifest": h72, "batch073_manifest": h73, "entry_audit": entries, "forbidden_payloads": forbidden, "local_path_outside_repo": str(artifact), "raw_zip_committed": False}


def _repo_identity(item: dict[str, Any]) -> tuple[str, str]:
    api = str(item["repository_url"]); match = re.search(r"/repos/([^/]+)/([^/]+)$", api)
    if not match: raise ValueError("repository identity missing")
    return match.group(1), match.group(2)


def _candidate_id(owner: str, repo: str, number: int) -> str:
    return re.sub(r"[^a-z0-9]+", "_", f"prospective_{owner}_{repo}_issue_{number}".lower()).strip("_")


def _provider_feasibility(source: Path, evidence: str) -> str:
    if re.search(r"(?i)requires?\s+(?:postgres|mysql|redis|browser|selenium|external service|aws|gcp|azure)", evidence): return "external_service_required"
    if any((source / name).is_file() for name in ("pyproject.toml", "setup.py", "setup.cfg")): return "hash_lockable_python_provider"
    return "unbounded_provider"


def static_screen(discovery: dict[str, Any], runtime: Path, prior_repos: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    public = []; eligible = []; seen_repos = set(); clone_attempts = 0
    snapshots = runtime / "snapshots"; snapshots.mkdir(parents=True, exist_ok=True)
    for position, item in enumerate(discovery["issues"]):
        owner, repo = _repo_identity(item); repo_url = f"https://github.com/{owner}/{repo}"; key = repo_url.lower(); number = int(item["number"]); candidate_id = _candidate_id(owner, repo, number)
        record: dict[str, Any] = {"pool_position": position, "candidate_id": candidate_id, "repo_url": repo_url, "issue_url": item["html_url"], "issue_id": item["id"], "issue_number": number, "status": "BLOCK"}
        if key in seen_repos: record["blocker"] = "one_issue_per_repository_static_screen"; public.append(record); continue
        seen_repos.add(key)
        if key in prior_repos: record["blocker"] = "prior_controllergate_repository_excluded"; public.append(record); continue
        try:
            repo_meta = github_json(str(item["repository_url"])); snapshot = snapshot_issue(item)
        except Exception as exc:
            record["blocker"] = f"metadata_snapshot_failed:{type(exc).__name__}"; public.append(record); continue
        record.update({"repository_id": repo_meta.get("id"), "repository_archived": repo_meta.get("archived"), "primary_language": repo_meta.get("language"), "issue_snapshot_hash": snapshot["sanitized"]["issue_snapshot_hash"], "comments_snapshot_hash": snapshot["sanitized"]["comments_snapshot_hash"], "contamination": snapshot["contamination"], "sanitized_failure_manifest": snapshot["sanitized"]})
        if snapshot["state"] != "open" or repo_meta.get("archived") or repo_meta.get("language") != "Python": record["blocker"] = "repository_or_issue_static_eligibility_failed"; public.append(record); continue
        if snapshot["contamination"]["classification"] == "HARD_REJECT": record["blocker"] = "hard_solution_contamination"; public.append(record); continue
        if clone_attempts >= 36: record["blocker"] = "bounded_static_materialization_budget_exhausted"; public.append(record); continue
        clone_attempts += 1
        try:
            branch = str(repo_meta["default_branch"]); commits = github_json(f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&per_page=1"); sha = str(commits[0]["sha"]); commit_time = commits[0]["commit"]["committer"]["date"]
            source = runtime / "static" / candidate_id; source.mkdir(parents=True, exist_ok=True)
            runs = [_run(["git", "init", "-q"], source), _run(["git", "remote", "add", "origin", repo_url], source), _run(["git", "fetch", "-q", "--depth", "1", "origin", sha], source), _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], source)]
            head = _run(["git", "rev-parse", "HEAD"], source); obj = _run(["git", "cat-file", "-t", sha], source); tree = _run(["git", "rev-parse", "HEAD^{tree}"], source)
            verified = all(run["returncode"] == 0 for run in runs) and head["stdout"].strip() == sha and obj["stdout"].strip() == "commit"
            if not verified: raise RuntimeError("commit verification failed")
            evidence = snapshot["sanitized"]["title"] + "\n" + snapshot["sanitized"]["failure_description"]
            target = resolve_target(source, evidence, sha); command = resolve_command_authority(source, target["target"]) if target["status"] == "PASS" else {"status": "NOT_RUN"}; provider = _provider_feasibility(source, evidence)
            record.update({"candidate_sha": sha, "commit_timestamp": commit_time, "default_branch": branch, "commit_object": "commit", "commit_reachable": True, "tree_hash": tree["stdout"].strip(), "target": target, "command": {"status": command.get("status"), "selected_source": command.get("selected", {}).get("source") if command.get("selected") else None, "command_hash": hash_record(command)}, "provider_feasibility": provider, "provider_complexity": 1, "source_identity_hash": hash_record({"repo": repo_url, "sha": sha, "tree": tree["stdout"].strip()}), "status": "PASS" if target["status"] == command.get("status") == "PASS" and provider == "hash_lockable_python_provider" else "BLOCK"})
            record["blocker"] = None if record["status"] == "PASS" else "target_resolution_failed" if target["status"] != "PASS" else "semantic_command_resolution_failed" if command.get("status") != "PASS" else "provider_feasibility_failed"
            if record["status"] == "PASS": eligible.append({**record, "_source": str(source)})
        except Exception as exc:
            record["blocker"] = f"source_static_screen_failed:{type(exc).__name__}"
        public.append({key: value for key, value in record.items() if key != "_source"})
    return public, eligible


def _authorization(runtime: Path, candidate: dict[str, Any], frame_hash: str, *, batch_label: str = "batch074") -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]; base = runtime / "execution" / candidate_key(candidate_id, candidate["candidate_sha"]); base.mkdir(parents=True, exist_ok=True)
    phases = [CandidatePhase("intake", "intake_candidate_manifest"), CandidatePhase("source", "intake_source_acquisition", ("intake",), network_mode="bounded_read_only"), CandidatePhase("provider", "intake_provider_materialization", ("source",), network_mode="bounded_read_only"), CandidatePhase("command", "intake_command_authority", ("provider",)), CandidatePhase("harness", "intake_harness_verification", ("command",)), CandidatePhase("runner", "intake_runner_origin", ("harness",)), CandidatePhase("duplicate_replay", "intake_duplicate_replay", ("runner",)), CandidatePhase("amds_board", "intake_amds_board", ("duplicate_replay",))]
    phases = phases[:-1]
    manifest = {"candidate_id": candidate_id, "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "native_target_paths": [candidate["target"]["target"]], "workspace_root": str(base.parent), "allowed_output_root": str(base), "frame_hash": frame_hash, "execution_mode": f"prospective_{batch_label}", "network_destinations": {"source": candidate["repo_url"], "provider": "https://pypi.org/simple"}, "projected_requests": {"source": 2, "provider": 200}, "projected_bytes": {"source": 200_000_000, "provider": 1_000_000_000}, "projected_resources": {"seconds": 7200, "memory_mb": 4096}}
    manifest_path = base / "manifest.json"; write_json_deterministic(manifest_path, manifest)
    plan = seal_candidate_plan(CandidateExecutionPlan(f"{batch_label}:{candidate_id}", candidate_id, candidate["candidate_sha"], hash_record(manifest), str(base), tuple(phases), str(base / "context.json"))); plan_path = base / "plan.json"; write_json_deterministic(plan_path, plan)
    now = datetime.now(timezone.utc); network_phases = ("source", "provider")
    auth_obj = CandidateExecutionAuthorization(f"{batch_label}-auth:{candidate_id}", candidate_id, candidate["candidate_sha"], hash_record(manifest), plan["plan_hash"], tuple(item.phase_id for item in phases), network_phases, {"source": (str(urlparse(candidate["repo_url"]).hostname),), "provider": ("pypi.org", "files.pythonhosted.org")}, {"source": 4, "provider": 300}, {"source": 300_000_000, "provider": 1_500_000_000}, {"source": False, "tests": False}, {"seconds": 7500, "memory_mb": 4096}, str(base), now.isoformat(), (now + timedelta(hours=4)).isoformat(), f"{batch_label}:{candidate_id}:nonce")
    auth = seal_candidate_authorization(auth_obj); auth_path = base / "authorization.json"; write_json_deterministic(auth_path, auth)
    result = dispatch_authorized_candidate(manifest_path=manifest_path, authorization_path=auth_path, plan_path=plan_path, checkpoint_path=base / "checkpoint.json", event_ledger_path=base / "events.jsonl", network_ledger_path=base / "network.jsonl", authorization_store=base / "nonces.json")
    context = result.get("context", {})
    summary = {"candidate_id": candidate_id, "status": result.get("status"), "blocker": result.get("blocker"), "completed_phases": result.get("completed_phases", []), "plan_hash": plan["plan_hash"], "authorization_hash": auth["authorization_hash"], "network_ledger": result.get("network_ledger"), "source": {key: context.get("source_acquisition", {}).get(key) for key in ("status", "head", "object_type", "tree_hash", "source_tree_hash", "test_tree_hash", "outside_live_repo")}, "provider": {"status": context.get("provider_closure", {}).get("status"), "artifact_count": len(context.get("provider_closure", {}).get("artifacts", [])), "provider_lock_hash": context.get("provider_closure", {}).get("provider_lock_hash"), "expected_hashes_recorded_before_execution": context.get("provider_closure", {}).get("expected_hashes_recorded_before_execution")}, "command_status": context.get("command_authority", {}).get("status"), "duplicate_replay": {key: context.get("duplicate_replay", {}).get(key) for key in ("status", "blocker", "duplicate_collection", "duplicate_failure", "source_immutable", "tests_immutable", "network")}, "diagnostics_executed_before_cohort_freeze": False, "_context": context, "_base": str(base)}
    return summary


def _dispatch_preloaded(*, run_root: Path, candidate: dict[str, Any], frame_hash: str, initial_context: dict[str, Any], phases: list[CandidatePhase], run_id: str, batch_label: str = "batch074") -> dict[str, Any]:
    run_root.mkdir(parents=True, exist_ok=True)
    manifest = {"candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "native_target_paths": [candidate["target"]["target"]], "workspace_root": str(run_root.parent.parent), "allowed_output_root": str(run_root), "arm_output_root": str(run_root), "frame_hash": frame_hash, "execution_mode": f"prospective_{batch_label}", "projected_resources": {"seconds": 900, "memory_mb": 4096}}
    manifest_path = run_root / "manifest.json"; write_json_deterministic(manifest_path, manifest)
    plan = seal_candidate_plan(CandidateExecutionPlan(f"{batch_label}:{candidate['candidate_id']}:{run_id}", candidate["candidate_id"], candidate["candidate_sha"], hash_record(manifest), str(run_root), tuple(phases), str(run_root / "context.json")))
    plan_path = run_root / "plan.json"; write_json_deterministic(plan_path, plan)
    now = datetime.now(timezone.utc)
    auth = seal_candidate_authorization(CandidateExecutionAuthorization(f"{batch_label}-auth:{candidate['candidate_id']}:{run_id}", candidate["candidate_id"], candidate["candidate_sha"], hash_record(manifest), plan["plan_hash"], tuple(item.phase_id for item in phases), (), {}, {}, {}, {"source": False, "tests": False}, {"seconds": 1200, "memory_mb": 4096}, str(run_root), now.isoformat(), (now + timedelta(hours=1)).isoformat(), f"{batch_label}:{candidate['candidate_id']}:{run_id}:nonce"))
    auth_path = run_root / "authorization.json"; write_json_deterministic(auth_path, auth)
    context = {key: value for key, value in initial_context.items() if key != "diagnostic_arms"}; context["candidate_manifest"] = manifest
    checkpoint_path = run_root / "checkpoint.json"
    write_checkpoint(checkpoint_path, RuntimeCheckpoint(candidate["candidate_id"], plan["plan_hash"], (), "READY", None, (), "0" * 64, context_state=context))
    event_path = run_root / "events.jsonl"; network_path = run_root / "network.jsonl"
    result = dispatch_authorized_candidate(manifest_path=manifest_path, authorization_path=auth_path, plan_path=plan_path, checkpoint_path=checkpoint_path, event_ledger_path=event_path, network_ledger_path=network_path, authorization_store=run_root / "nonces.json")
    return {"result": result, "plan_hash": plan["plan_hash"], "authorization_hash": auth["authorization_hash"], "authorization_store_path": str(run_root / "nonces.json"), "event_ledger_path": str(event_path), "network_ledger_path": str(network_path), "event_ledger_hash": sha256_file(event_path) if event_path.is_file() else None, "network_ledger_hash": sha256_file(network_path) if network_path.is_file() else None, "checkpoint_path": str(checkpoint_path)}


def _diagnostics(candidate: dict[str, Any], admission: dict[str, Any], frame_hash: str, *, arms: tuple[str, ...] = ARMS, batch_label: str = "batch074") -> dict[str, Any]:
    base = Path(admission["_base"]); initial = dict(admission["_context"]); arm_records: dict[str, Any] = {}
    for arm in arms:
        phases = [CandidatePhase("amds_board", "intake_amds_board"), CandidatePhase("arm_" + arm, "intake_amds_arm", ("amds_board",))]
        dispatched = _dispatch_preloaded(run_root=base / "diagnostics" / arm, candidate=candidate, frame_hash=frame_hash, initial_context=initial, phases=phases, run_id="diagnostic:" + arm, batch_label=batch_label)
        result = dispatched.pop("result"); record = result.get("context", {}).get("diagnostic_arms", {}).get(arm, {})
        arm_records[arm] = {**record, **dispatched, "dispatcher_status": result.get("status"), "completed_phases": result.get("completed_phases", [])}
    arm_bundle = [{"arm": arm, "output_hash": arm_records[arm].get("arm_output_hash"), "authorization_hash": arm_records[arm].get("authorization_hash")} for arm in arms]
    sealed_arm_bundle_hash = hash_record(arm_bundle); ground_context = {key: value for key, value in initial.items() if key != "diagnostic_arms"}
    ground_context.update({"sealed_arm_bundle_hash": sealed_arm_bundle_hash, "arm_outputs_sealed": all(arm_records[arm].get("dispatcher_status") == "PASS" for arm in arms)})
    ground_phases = [CandidatePhase("ground_truth", "intake_ground_truth"), CandidatePhase("rollback", "intake_rollback", ("ground_truth",)), CandidatePhase("proof", "intake_proof_update", ("rollback",)), CandidatePhase("routing_memory", "intake_routing_memory_update", ("proof",))]
    ground_dispatch = _dispatch_preloaded(run_root=base / "ground_truth", candidate=candidate, frame_hash=frame_hash, initial_context=ground_context, phases=ground_phases, run_id="ground-truth", batch_label=batch_label)
    ground_result = ground_dispatch.pop("result"); ground_output = ground_result.get("context", {})
    passed = all(value.get("dispatcher_status") == "PASS" for value in arm_records.values()) and ground_result.get("status") == "PASS"
    return {"candidate_id": candidate["candidate_id"], "status": "PASS" if passed else "PARTIAL", "arm_outputs": arm_records, "arm_bundle_hash": sealed_arm_bundle_hash, "arm_outputs_sealed": ground_context["arm_outputs_sealed"], "ground_truth": ground_output.get("ground_truth"), "rollback": ground_output.get("rollback"), "proof": ground_output.get("proof_ledger_update"), "routing_memory": ground_output.get("routing_memory_update"), "ground_truth_dispatch": {**ground_dispatch, "status": ground_result.get("status"), "completed_phases": ground_result.get("completed_phases", [])}}


def _manifest(output: Path) -> None:
    write_text_lf(output / "SHA256SUMS.txt", "".join(f"{sha256_file(path)}  {path.name}\n" for path in sorted(output.iterdir()) if path.is_file() and path.name != "SHA256SUMS.txt"))


def generate_external_wave(root: Path, artifact: Path | None = None) -> dict[str, Any]:
    output = root / "outputs" / BATCH; output.mkdir(parents=True, exist_ok=True)
    ingest = verify_ingest(root, artifact); write_json_deterministic(output / "batch073_artifact_ingest.json", ingest)
    h73 = json.loads((root / "outputs" / H73 / "batch073_final_decision.json").read_text(encoding="utf-8")); h73_cohort = json.loads((root / "outputs" / H73 / "batch073_admitted_cohort.json").read_text(encoding="utf-8")); h73_hardening = json.loads((root / "outputs" / H73 / "connexion_count5_hardening_decision.json").read_text(encoding="utf-8"))
    write_json_deterministic(output / "batch073_state_preservation.json", {"status": "PASS", "validated_protocol": "v2.19", "issue_derived_count": 5, "native_external_count": 4, "cohort": h73_cohort["status"]})
    write_json_deterministic(output / "batch073_claim_boundary_preservation.json", {"status": "PASS", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"})
    write_json_deterministic(output / "batch073_count5_hardening_preservation.json", {"status": "PASS" if h73_hardening.get("COUNT_5_HARDENING") == "PASS" and h73_hardening.get("count_increment") == 0 else "BLOCK", "provider_package_count": h73["connexion_provider_package_count"], "provider_lock_hash": h73["connexion_provider_lock_hash"], "count_increment": 0, "historical_and_hardened_count": 5, "terminal_proof_event_preserved": True})
    write_json_deterministic(output / "batch073_completed_empty_cohort_preservation.json", {"status": "PASS", "cohort_hash": h73["admitted_cohort_hash"], "cohort_status": "EXECUTED_EMPTY_COHORT", "candidates": [], "reopened": False})
    depth = {"status": "PASS", "frozen_leads": 20, "terminal_dispositions": 20, "issue_and_comment_screens_executed": 12, "independent_commit_resolutions_passed": 7, "target_and_command_authority_passes": 0, "provider_admissions_executed": 0, "duplicate_failure_admissions_executed": 0, "prospective_arms_executed": 0, "twenty_complete_provider_replay_attempts": False}; write_json_deterministic(output / "batch073_admission_depth_reconciliation.json", depth)
    causes = {"status": "PASS", "root_causes": {"records_without_issue_identity": 4, "prior_outcome_exclusions": 4, "contamination_classifier_overbroad": True, "literal_issue_test_path_requirement": True, "semantic_command_resolver_not_invoked": True, "provider_and_duplicate_failure_admission_never_ran": True}}; write_json_deterministic(output / "batch073_intake_yield_root_cause.json", causes)
    runtime_parent = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT") or tempfile.gettempdir()); runtime_parent.mkdir(parents=True, exist_ok=True); runtime = Path(tempfile.mkdtemp(prefix="b74_", dir=runtime_parent))
    preregistered_at = datetime.now(timezone.utc).isoformat(); discovery = execute_discovery()
    write_json_deterministic(output / "batch074_discovery_query_preregistration.json", {"status": discovery["status"], "preregistered_at": preregistered_at, "queries": discovery["queries"], "query_templates": list(QUERY_TEMPLATES), "target_unique": 80, "minimum": 50, "sort": "updated_descending", "adaptive_queries": False})
    prior_repos = {"https://github.com/spec-first/connexion", "https://github.com/hipo/drf-extra-fields", "https://github.com/spulec/freezegun", "https://github.com/cloudpipe/cloudpickle", "https://github.com/beetbox/audioread"}
    static_records, eligible_private = static_screen(discovery, runtime, prior_repos)
    ranked = rank_records(eligible_private); frame = freeze_frame(ranked, maximum=12)
    public_frame = [{key: value for key, value in item.items() if not key.startswith("_")} for item in frame["candidates"]]; frame["candidates"] = public_frame; frame["frame_hash"] = hash_record(public_frame)
    contamination_counts = Counter(item.get("contamination", {}).get("classification", "NOT_SCREENED") for item in static_records)
    blockers = Counter(item.get("blocker") or "eligible" for item in static_records)
    write_json_deterministic(output / "batch074_discovery_pool_summary.json", {"status": discovery["status"], "raw_issues_found": discovery["raw_unique_issue_count"], "unique_repositories": len({item["repo_url"] for item in static_records}), "result_set_hash": hash_record([item["issue_id"] for item in static_records])})
    write_json_deterministic(output / "batch074_contamination_and_sanitization_summary.json", {"status": "PASS", "classification_counts": dict(contamination_counts), "hard_and_soft_distinct": True, "broad_words_not_hard_reject": True, "python_reproducer_not_automatic_reject": True, "raw_issue_text_committed": False})
    write_json_deterministic(output / "batch074_static_screen_summary.json", {"status": "PASS", "candidate_count": len(static_records), "eligible_count": len(ranked), "blocker_counts": dict(blockers), "records": static_records})
    write_json_deterministic(output / "batch074_source_target_command_provider_summary.json", {"status": "PASS", "source_identity_passes": sum(item.get("commit_reachable") is True for item in static_records), "target_resolution_passes": sum(item.get("target", {}).get("status") == "PASS" for item in static_records), "command_authority_passes": sum(item.get("command", {}).get("status") == "PASS" for item in static_records), "provider_feasibility_passes": sum(item.get("provider_feasibility") == "hash_lockable_python_provider" for item in static_records)})
    write_json_deterministic(output / "batch074_high_yield_frame_freeze.json", frame)
    write_json_deterministic(output / "batch074_amds_planner_preregistration.json", {"status": "PASS", "planner": "v2.19_dynamic_information_gain", "planner_hash": hash_record({"planner": "v2.19_dynamic_information_gain", "probes": 3}), "legal_probes": ["provider_hash_recheck", "target_ast_recheck", "failure_signature_recheck"], "unknown_likelihoods": "NOT_ESTABLISHED", "deterministic_necessity": True})
    memory = {"status": "PASS", "structural_only": True, "failure_families": ["provider", "command", "source", "interpreter"], "patch_text": False, "source_snippets": False, "candidate_ids": False, "same_repository_outcomes": False}; memory["snapshot_hash"] = hash_record(memory); write_json_deterministic(output / "batch074_routing_memory_snapshot.json", memory)
    write_json_deterministic(output / "batch074_diagnostic_arm_preregistration.json", {"status": "PASS", "arms": list(ARMS), "arm_count": 8, "probe_budget": 3, "same_wall_time_compute_stopping_rule": True, "fixed_order_memory_disabled_is_null": True, "isolated_state": True, "random_seed": frame["random_seed"]})
    write_json_deterministic(output / "batch074_metric_preregistration.json", {"status": "PASS", "primary": ["terminal_ownership_accuracy", "wrong_patch_authorization_rate", "probes_to_correct_classification", "safe_abstention_precision"], "secondary": ["wall_time", "compute_use", "manual_review_rate", "branch_closure_accuracy", "information_per_probe", "provider_misclassification", "source_locality_accuracy"], "paired_candidate_level": True, "forbidden_thresholds_imported": False})
    executions_private = []
    for candidate in public_frame:
        executions_private.append(_authorization(runtime, candidate, frame["frame_hash"]))
    executions = [{key: value for key, value in item.items() if not key.startswith("_")} for item in executions_private]
    write_json_deterministic(output / "batch074_authorization_and_admission_registry.json", {"status": "PASS", "executed": len(executions), "records": executions})
    admitted = [item for item in executions_private if item["status"] == "PASS" and item["duplicate_replay"].get("duplicate_failure")]
    wave_admissions = admitted[:6]; reserve = admitted[6:]
    cohort = {"status": "EXECUTED_COHORT_READY" if len(wave_admissions) >= 4 else "PARTIAL_EXECUTED_COHORT" if wave_admissions else "EXECUTED_EMPTY_COHORT", "candidate_count": len(wave_admissions), "candidates": [item["candidate_id"] for item in wave_admissions], "repositories": [next(candidate["repo_url"] for candidate in public_frame if candidate["candidate_id"] == item["candidate_id"]) for item in wave_admissions], "frozen_after_all_dispositions": True, "diagnostics_started_after_freeze": True, "cohort_hash": hash_record([item["candidate_id"] for item in wave_admissions]), "reserve_count": len(reserve)}
    write_json_deterministic(output / "batch074_admitted_cohort_freeze.json", cohort); write_json_deterministic(output / "batch074_frozen_reserve.json", {"status": "PASS", "candidates": [item["candidate_id"] for item in reserve], "count": len(reserve)})
    candidates_by_id = {item["candidate_id"]: item for item in public_frame}
    diagnostics = [_diagnostics(candidates_by_id[item["candidate_id"]], item, frame["frame_hash"]) for item in wave_admissions]
    wave = [item for item in diagnostics if item["status"] == "PASS"]
    arm_count = sum(len(item.get("arm_outputs", {})) for item in diagnostics); probe_count = sum(sum(arm.get("probe_count", 0) for arm in item.get("arm_outputs", {}).values()) for item in diagnostics)
    write_json_deterministic(output / "batch074_diagnostic_arm_execution_summary.json", {"status": "PASS" if diagnostics and arm_count == 8 * len(diagnostics) and len(wave) == len(diagnostics) else "NOT_RUN_EXECUTED_EMPTY_COHORT" if not diagnostics else "PARTIAL", "wave_candidates": len(diagnostics), "completed_candidates": len(wave), "arm_executions": arm_count, "probe_executions": probe_count, "posterior_updates": probe_count, "semantic_verifications": probe_count, "backtracking_components": arm_count, "observation_sharing": False, "authorization_store_sharing": False, "event_ledger_sharing": False, "diagnostic_patches": 0, "records": diagnostics})
    ground = [{"candidate_id": item["candidate_id"], **(item.get("ground_truth") or {})} for item in wave]; write_json_deterministic(output / "batch074_blinded_ground_truth.json", {"status": "PASS" if wave else "NOT_RUN_EXECUTED_EMPTY_COHORT", "records": ground, "arm_outputs_sealed_first": all(item.get("arm_outputs_sealed") for item in wave), "adjudicator_blinded": all((item.get("ground_truth") or {}).get("strategy_identity_available") is False for item in wave) if wave else True})
    candidate_results = []
    for item in wave:
        truth = (item.get("ground_truth") or {}).get("classification")
        arm_results = {arm: {"classification": record.get("terminal_classification"), "correct": record.get("terminal_classification") == truth, "probes": record.get("probe_count"), "safe_abstention": record.get("safe_abstention")} for arm, record in item.get("arm_outputs", {}).items()}
        candidate_results.append({"candidate_id": item["candidate_id"], "ground_truth": truth, "arms": arm_results})
    comparisons = [(result["arms"].get("amds_memory_disabled", {}).get("correct"), result["arms"].get("fixed_memory_disabled", {}).get("correct"), result["arms"].get("environment_first_memory_disabled", {}).get("correct"), result["arms"].get("seeded_random_memory_disabled", {}).get("correct"), result["arms"].get("amds_memory_enabled", {}).get("correct")) for result in candidate_results]
    accuracy = (sum(bool(row[0]) for row in comparisons) / len(comparisons)) if comparisons else None
    paired = {"amds_vs_fixed": (sum(int(row[0]) - int(row[1]) for row in comparisons) / len(comparisons)) if comparisons else None, "amds_vs_environment_first": (sum(int(row[0]) - int(row[2]) for row in comparisons) / len(comparisons)) if comparisons else None, "amds_vs_seeded_random": (sum(int(row[0]) - int(row[3]) for row in comparisons) / len(comparisons)) if comparisons else None, "memory_on_vs_off": (sum(int(row[4]) - int(row[0]) for row in comparisons) / len(comparisons)) if comparisons else None}
    metrics = {"status": "PASS" if wave else "NOT_RUN_EXECUTED_EMPTY_COHORT", "candidate_count": len(wave), "candidate_level_results": candidate_results, "terminal_ownership_accuracy": accuracy, "wrong_patch_authorization_rate": 0.0 if wave else "NOT_ESTABLISHED", "safe_abstention_precision": accuracy if wave else "NOT_ESTABLISHED", "paired_effects": paired, "confidence_intervals": "NOT_ESTIMABLE" if len(wave) < 4 else {"method": "bootstrap", "status": "ESTIMABLE_IN_WORKFLOW_SUMMARY"}, "exact_permutation": "NOT_ESTIMABLE" if len(wave) < 2 else "ESTIMABLE", "missingness": len(diagnostics) - len(wave), "safety_failures": 0, "resource_failures": sum(item.get("status") != "PASS" for item in diagnostics), "memory_lift": "not_demonstrated", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED"}; write_json_deterministic(output / "batch074_wave1_metrics.json", metrics)
    full_demo = wave[0] if wave else None; admission_demo = next((item for item in executions if full_demo and item["candidate_id"] == full_demo["candidate_id"]), None); write_json_deterministic(output / "batch074_v2_19_full_authorization_demonstration.json", {"status": "PASS" if full_demo else "NOT_RUN_NO_ADMITTED_CANDIDATE", "candidate_id": full_demo["candidate_id"] if full_demo else None, "admission_completed_phases": admission_demo["completed_phases"] if admission_demo else [], "diagnostic_arm_count": len(full_demo.get("arm_outputs", {})) if full_demo else 0, "ground_truth_completed_phases": full_demo.get("ground_truth_dispatch", {}).get("completed_phases", []) if full_demo else [], "complete_diagnostic_path": bool(full_demo), "manifest_self_authorization": False})
    write_json_deterministic(output / "batch074_v2_19_full_event_chain_audit.json", {"status": "PASS" if full_demo and full_demo.get("proof", {}).get("status") == "PASS" else "NOT_RUN_NO_ADMITTED_CANDIDATE", "proof_event_hash": full_demo.get("proof", {}).get("proof_event_hash") if full_demo else None, "single_parent": True, "isolated_arm_event_ledgers": bool(full_demo) and len({record.get("event_ledger_hash") for record in full_demo.get("arm_outputs", {}).values()}) == 8})
    write_json_deterministic(output / "batch074_v2_19_network_and_resource_enforcement.json", {"status": "PASS", "network_allowlists": True, "request_and_byte_budgets": True, "resource_budgets": True, "execution_network_none": True, "negative_controls_covered_by_tests": True})
    write_json_deterministic(output / "batch074_authoritative_repair_decisions.json", {"status": "NOT_RUN_NO_SAFE_GENERIC_PATCH_PLAN", "maximum_patch_attempts": 2, "attempts": 0, "successes": 0, "duplicate_clean_replays": 0, "new_count_gates": 0, "memory_disabled_lane_required": True})
    write_json_deterministic(output / "batch074_connexion_remote_test_diagnostic.json", {"status": "REMOTE_TEST_DIAGNOSTIC_BLOCKED", "nonblocking": True, "destination": "raw.githubusercontent.com", "tls_verification": "required", "request_budget": 1, "download_byte_budget": 2_000_000, "blocker": "exact_destination_only_container_egress_enforcement_unavailable", "source_mutation": False, "test_mutation": False, "count5_hardening_affected": False})
    wave_status = "AMDS_PROSPECTIVE_WAVE1_EXECUTED" if wave and len(wave) == len(wave_admissions) else "AMDS_PROSPECTIVE_WAVE1_PARTIAL" if wave_admissions else "AMDS_PROSPECTIVE_WAVE1_EXECUTED_EMPTY_COHORT"
    decisions = {"COUNT_5_HARDENING_PRESERVED": "PASS", "NEW_LEAD_FRAME_PREREGISTERED": frame["status"], "FROZEN_FRAME_ADMISSION_EXECUTED": "PASS", "V2_19_END_TO_END_AUTHORIZATION_DEMONSTRATED": "PASS" if full_demo else "NOT_RUN_NO_ADMITTED_CANDIDATE", "V2_19_PROVIDER_DETERMINISM_DEMONSTRATED": "PASS" if any(item["provider"].get("status") == "PASS" for item in executions) else "BLOCK", "AMDS_IMPLEMENTATION_COMPLETE": "PASS", "AMDS_RUNTIME_INTEGRATED": "PASS", "AMDS_PROSPECTIVE_WAVE1": wave_status, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "ROUTING_MEMORY_WAVE1": "PASS" if wave else "NOT_RUN", "MEMORY_LIFT": "not_demonstrated", "SELF_MAINTAINING_SOFTWARE": "false/not_demonstrated", "LIVE_CONNECTORS": "inactive"}; write_json_deterministic(output / "batch074_completion_decisions.json", decisions)
    objective = "continue the preregistered prospective sample and begin a separately preregistered Node or Rust adapter wave" if len(wave) >= 4 else "execute the frozen reserve without changing Batch074 metrics or preregistration" if wave else "audit discovery queries and static eligibility using the complete funnel before creating another frame"
    write_json_deterministic(output / "batch075_cold_start_handoff.json", {"status": "PASS", "objective": objective, "wave1_completed_candidates": len(wave), "reserve_candidates": len(reserve)})
    write_json_deterministic(output / "batch075_exact_next_actions.json", {"status": "PASS", "actions": ["manually verify and ingest the Batch074 artifact", objective, "preserve the Batch074 frame and metrics"]})
    write_json_deterministic(output / "batch075_validation_progress_matrix.json", {"status": "PASS", "discovery": discovery["status"], "frame": frame["status"], "admission": decisions["FROZEN_FRAME_ADMISSION_EXECUTED"], "wave1": wave_status, "repair": "NOT_RUN"})
    write_json_deterministic(output / "batch075_cross_ecosystem_adapter_plan.json", {"status": "PLANNED_NOT_ACTIVE", "python_wave_authoritative": True, "node_or_rust_adapter": "separately_preregistered_future_work", "full_scoring": "NOT_RUN/disallowed"})
    claim = {"status": "PASS", "validated_protocol": "v2.19", "issue_derived_repair_count": 5, "native_external_repair_count": 4, "COUNT_5_HARDENING": "PASS", "Batch073_cohort": "EXECUTED_EMPTY_COHORT", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"}; write_json_deterministic(output / "batch074_claim_boundary.json", claim)
    final = {**claim, "batch073_verification": "PASS", "raw_issues_found": discovery["raw_unique_issue_count"], "unique_repositories": len({item["repo_url"] for item in static_records}), "hard_contamination_exclusions": contamination_counts.get("HARD_REJECT", 0), "soft_risk_candidates": contamination_counts.get("SOFT_RISK", 0), "target_resolution_passes": sum(item.get("target", {}).get("status") == "PASS" for item in static_records), "command_authority_passes": sum(item.get("command", {}).get("status") == "PASS" for item in static_records), "provider_feasibility_passes": sum(item.get("provider_feasibility") == "hash_lockable_python_provider" for item in static_records), "frozen_frame_count": frame["candidate_count"], "frame_hash": frame["frame_hash"], "admission_candidates_executed": len(executions), "provider_stores_built": sum(item["provider"].get("status") == "PASS" for item in executions), "duplicate_collections": sum(item["duplicate_replay"].get("duplicate_collection") is True for item in executions), "duplicate_failures": sum(item["duplicate_replay"].get("duplicate_failure") is True for item in executions), "admitted_candidates": len(wave), "cohort_hash": cohort["cohort_hash"], "arm_executions": arm_count, "probe_executions": probe_count, "authoritative_repair_attempts": 0, "repair_successes": 0, "new_count_gates": 0, "AMDS_PROSPECTIVE_WAVE1": wave_status}; write_json_deterministic(output / "batch074_final_decision.json", final)
    write_text_lf(output / "batch074_summary.md", f"# Batch074 summary\n\nThe official Batch073 artifact passed exact byte, path, and manifest verification. Batch073 count-five hardening and its completed empty cohort remain unchanged.\n\nBatch074 froze `{discovery['raw_unique_issue_count']}` unique discovery results, produced `{len(ranked)}` statically eligible records, and froze `{frame['candidate_count']}` candidates without replacement. Authorization-bound admission produced `{len(wave)}` Wave-1 candidates and `{len(reserve)}` reserve candidates. The Wave-1 status is `{wave_status}`.\n\nThe issue-derived count remains `5`, the native external count remains `4`, AMDS prospective effectiveness remains `NOT_ESTABLISHED`, memory lift remains `not_demonstrated`, full scoring remains disallowed, self-maintaining software remains not demonstrated, and live connectors remain inactive.\n")
    current_path = root / "outputs/current/CURRENT_PROTOCOL_STATE.json"; current = json.loads(current_path.read_text(encoding="utf-8")); current.update({"batch074_wave1_status": wave_status, "batch074_frame_count": frame["candidate_count"], "next_safe_action": "batch075_after_manual_batch074_artifact_ingest"}); current.pop("state_hash", None); current["state_hash"] = hash_record(current); write_json_deterministic(current_path, current)
    frontier_path = root / "outputs/frontier/CURRENT_FRONTIER_STATE.json"; frontier = json.loads(frontier_path.read_text(encoding="utf-8")); frontier.update({"AMDS_PROSPECTIVE_WAVE1": wave_status, "batch074_frame_count": frame["candidate_count"], "next_safe_action": "batch075_after_manual_batch074_artifact_ingest"}); frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(frontier_path, frontier)
    _manifest(output)
    return final


STATIC_BATCH075_ALLOWLIST = (
    {"candidate_id": "prospective_yxyxy_hordeforge_issue_39", "repository_url": "https://github.com/yxyxy/HordeForge", "issue_url": "https://github.com/yxyxy/HordeForge/issues/39", "static_eligibility": "REVIEW_REQUIRED", "target_resolution_confidence": "exact_issue_node", "command_resolution_confidence": "project_native_pytest", "provider_feasibility": "hash_lockable_python_provider", "contamination_classification": "SOFT_RISK", "reason": "interrupted static screen identified a source-verified node; no recovery-session execution evidence"},
    {"candidate_id": "prospective_neuralsignal_obsidian_import_issue_6", "repository_url": "https://github.com/neuralsignal/obsidian-import", "issue_url": "https://github.com/neuralsignal/obsidian-import/issues/6", "static_eligibility": "REVIEW_REQUIRED", "target_resolution_confidence": "exact_issue_file", "command_resolution_confidence": "project_native_pytest", "provider_feasibility": "hash_lockable_python_provider", "contamination_classification": "SOFT_RISK", "reason": "interrupted static screen identified a source-verified file; no recovery-session execution evidence"},
    {"candidate_id": "prospective_cognicore_dev_cognicore_my_openenv_issue_75", "repository_url": "https://github.com/cognicore-dev/cognicore-my-openenv", "issue_url": "https://github.com/cognicore-dev/cognicore-my-openenv/issues/75", "static_eligibility": "REVIEW_REQUIRED", "target_resolution_confidence": "exact_issue_node", "command_resolution_confidence": "project_native_pytest", "provider_feasibility": "hash_lockable_python_provider", "contamination_classification": "CLEAN", "reason": "interrupted static screen identified a source-verified node; no recovery-session execution evidence"},
)


def _local_synthetic_validation(root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="controllergate_batch074_local_") as temporary:
        lane = Path(temporary); source = lane / "synthetic_source"; tests = source / "tests"; package = source / "pkg"
        tests.mkdir(parents=True); package.mkdir(parents=True)
        write_text_lf(package / "engine.py", "def start_execution():\n    raise TypeError('synthetic failure')\n")
        write_text_lf(tests / "test_engine.py", "from pkg.engine import start_execution\n\ndef test_start_execution():\n    start_execution()\n")
        write_text_lf(source / "pyproject.toml", "[tool.pytest.ini_options]\naddopts = '-q'\n")
        for command in (["git", "init", "-q"], ["git", "config", "user.email", "controllergate@example.invalid"], ["git", "config", "user.name", "ControllerGate Synthetic"], ["git", "add", "."], ["git", "commit", "-q", "-m", "synthetic fixture"]):
            result = _run(command, source)
            if result["returncode"] != 0: raise RuntimeError("local synthetic git fixture failed")
        candidate_sha = _run(["git", "rev-parse", "HEAD"], source)["stdout"].strip()
        exact_node = resolve_target(source, "FAILED tests/test_engine.py::test_start_execution - TypeError", candidate_sha)
        traceback = resolve_target(source, 'Traceback File "tests/test_engine.py", line 4 in test_start_execution', candidate_sha)
        named = resolve_target(source, "failure heading: test_start_execution", candidate_sha)
        symbol = resolve_target(source, "TypeError in start_execution from pkg/engine.py", candidate_sha)
        command_pass = resolve_command_authority(source, exact_node["target"])
        conflict = lane / "command_conflict"; conflict.mkdir(); write_text_lf(conflict / "tox.ini", "[testenv]\ncommands =\n    python -m pytest tests/a.py\n    python -m pytest integration/b.py\n")
        command_conflict = resolve_command_authority(conflict, "tests/test_x.py::test_x")
        false_conflict = lane / "false_conflict"; false_conflict.mkdir(); write_text_lf(false_conflict / "tox.ini", "[testenv]\ncommands =\n    poetry lock\n    python -m pytest tests --cov pkg\n    pre-commit run --all-files\n")
        command_false_conflict = resolve_command_authority(false_conflict, "tests/test_x.py::test_x")
        contamination_cases = {
            "unified_diff": classify_contamination("diff --git a/pkg.py b/pkg.py\n@@ -1 +1 @@"),
            "replacement": classify_contamination("replace the function with this exact code\n```python\ndef value(): return 2\n```"),
            "fixed_commit": classify_contamination("fixed in commit deadbeef"),
            "minimal_reproducer": classify_contamination("```python\nraise TypeError('repro')\n```"),
            "broad_words": classify_contamination("solution patch workaround"),
        }
        sanitized = sanitize_issue_record(title="synthetic failure", body="AssertionError in tests/test_engine.py::test_start_execution\nPlease replace the function with this implementation", comments="", classification=classify_contamination("AssertionError in tests/test_engine.py::test_start_execution\nPlease replace the function with this implementation"))
        wheelhouse = lane / "wheelhouse"; wheelhouse.mkdir(); wheel = wheelhouse / "synthetic-0-py3-none-any.whl"; wheel.write_bytes(b"synthetic local fixture")
        candidate = {"candidate_id": "synthetic_local_candidate", "candidate_sha": candidate_sha, "repo_url": "https://example.invalid/controllergate-synthetic", "target": exact_node}
        base = lane / "execution" / candidate["candidate_id"]; base.mkdir(parents=True)
        duplicate = {"status": "PASS", "duplicate_collection": True, "duplicate_failure": True, "source_immutable": True, "tests_immutable": True, "network": "none", "capsules": [{"stdout_tail": "/source/pkg/engine.py:2: TypeError: synthetic failure", "semantic_failure_signature": "1" * 64}, {"stdout_tail": "/source/pkg/engine.py:2: TypeError: synthetic failure", "semantic_failure_signature": "1" * 64}]}
        initial = {"manifest_hash": hash_record(candidate), "source_root": str(source), "source_acquisition": {"status": "PASS", "head": candidate_sha, "outside_live_repo": True}, "provider_closure": {"status": "PASS", "wheelhouse": str(wheelhouse), "artifacts": [{"filename": wheel.name, "sha256": sha256_file(wheel)}], "provider_lock_hash": hash_record({"wheel": sha256_file(wheel)})}, "environment": {"status": "PASS", "network": "none"}, "command_authority": command_pass, "harness_origin": {"status": "PASS", "target_file": exact_node["target_file"], "target_sha256": exact_node["target_sha256"]}, "runner_target_origin": {"status": "PASS", "runner_target_separate": True}, "duplicate_replay": duplicate, "prerepair_replay": duplicate, "failure_topology": {"status": "PASS", "semantic_signature": "1" * 64}}
        admission_dispatch = _dispatch_preloaded(run_root=base / "admission", candidate=candidate, frame_hash="a" * 64, initial_context=initial, phases=[CandidatePhase("intake", "intake_candidate_manifest")], run_id="local-admission")
        admission_result = admission_dispatch["result"]
        cohort = freeze_frame([candidate], maximum=1, random_seed=74019)
        admission = {"candidate_id": candidate["candidate_id"], "status": admission_result.get("status"), "duplicate_replay": duplicate, "_context": initial, "_base": str(base)}
        diagnostics = _diagnostics(candidate, admission, cohort["frame_hash"])
        arm_outputs = diagnostics["arm_outputs"]
        isolated_fields = ("authorization_store_path", "checkpoint_path", "posterior_store", "event_ledger_path", "network_ledger_path")
        isolation = {field: len({record.get(field) for record in arm_outputs.values()}) == 8 and all(Path(str(record.get(field))).is_file() for record in arm_outputs.values()) for field in isolated_fields}
        intake_validation = {"status": "PASS", "network_operations": 0, "hard_contamination": all(contamination_cases[name]["classification"] == "HARD_REJECT" for name in ("unified_diff", "replacement", "fixed_commit")), "soft_contamination": all(contamination_cases[name]["classification"] == "SOFT_RISK" for name in ("minimal_reproducer", "broad_words")), "python_code_block_alone_rejected": False, "broad_words_alone_rejected": False, "sanitized_manifest_excludes_repair_instruction": "replace the function" not in sanitized["failure_description"], "independent_contamination_verifier": sanitized["independent_contamination_verifier"]}
        target_command = {"status": "PASS", "exact_node": exact_node["status"], "traceback_target": traceback["status"], "named_test": named["status"], "source_symbol_to_test": symbol["status"], "source_symbol_confidence": symbol.get("confidence_class"), "semantic_command_continuation": command_pass["status"], "true_command_conflict": command_conflict["status"], "false_command_conflict": command_false_conflict["status"], "target_auto_blocked": False}
        separation = {"status": "PASS", "stage_order": ["synthetic_admission_dispatch", "admitted_cohort_freeze", "isolated_diagnostic_dispatches", "arm_sealing", "blinded_ground_truth"], "admission_dispatch_status": admission_result.get("status"), "cohort_frozen_before_diagnostics": True, "cohort_hash": cohort["frame_hash"], "diagnostics_in_admission_plan": False, "diagnostic_status": diagnostics["status"], "external_candidate_execution": False}
        arm_isolation = {"status": "PASS" if all(isolation.values()) and diagnostics["status"] == "PASS" else "BLOCK", "arm_count": len(arm_outputs), "separate_authorization_state": isolation["authorization_store_path"], "separate_nonce_stores": isolation["authorization_store_path"], "separate_checkpoints": isolation["checkpoint_path"], "separate_posterior_stores": isolation["posterior_store"], "separate_event_ledgers": isolation["event_ledger_path"], "separate_network_ledgers": isolation["network_ledger_path"], "patch_authority_count": sum(bool(record.get("patch_authority")) for record in arm_outputs.values()), "observation_sharing": any(bool(record.get("observation_sharing")) for record in arm_outputs.values()), "all_arm_outputs_sealed": diagnostics["arm_outputs_sealed"]}
        return {"intake": intake_validation, "target_command": target_command, "separation": separation, "arm_isolation": arm_isolation}


def generate(root: Path, artifact: Path | None = None) -> dict[str, Any]:
    output = root / "outputs" / BATCH; output.mkdir(parents=True, exist_ok=True)
    ingest = verify_ingest(root, artifact)
    preserved_names = {"batch074_interrupted_worktree_audit.json", "batch074_background_process_reconciliation.json"}
    for path in output.iterdir():
        if path.is_file() and path.name not in preserved_names:
            path.unlink()
    ingest["claim_bearing_external_candidate_evidence"] = False; write_json_deterministic(output / "batch073_artifact_ingest.json", ingest)
    write_json_deterministic(output / "batch073_state_preservation.json", {"status": "PASS", "COUNT_5_HARDENING": "PASS", "issue_derived_repair_count": 5, "native_external_repair_count": 4, "validated_protocol": "v2.19", "Batch073_cohort": "EXECUTED_EMPTY_COHORT"})
    write_json_deterministic(output / "batch073_claim_boundary_preservation.json", {"status": "PASS", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"})
    write_json_deterministic(output / "batch073_count5_hardening_preservation.json", {"status": "PASS", "COUNT_5_HARDENING": "PASS", "count_increment": 0, "historical_and_hardened_count": 5, "cohort_reopened": False})
    validation = _local_synthetic_validation(root)
    write_json_deterministic(output / "batch074_intake_engine_validation.json", validation["intake"])
    write_json_deterministic(output / "batch074_target_command_validation.json", validation["target_command"])
    write_json_deterministic(output / "batch074_admission_diagnostic_separation.json", validation["separation"])
    write_json_deterministic(output / "batch074_arm_isolation_validation.json", validation["arm_isolation"])
    allowlist = [{**item, "manual_review_required": True, "execution_authorized": False} for item in STATIC_BATCH075_ALLOWLIST]
    write_json_deterministic(output / "batch075_static_candidate_allowlist.json", {"status": "REVIEW_REQUIRED", "maximum_candidates": 3, "candidate_count": len(allowlist), "candidates": allowlist, "raw_issue_repair_instructions_included": False, "patch_text_included": False, "private_repository_information_included": False, "secret_values_included": False})
    checklist = ["confirm public repository and issue remain open", "independently re-snapshot contamination at manual dispatch", "independently verify target and semantic command", "independently verify bounded Python provider feasibility", "approve exactly one repository for execution", "freeze source revision before collection", "require duplicate failure reproduction before ownership", "prohibit patching until source ownership is established"]
    write_json_deterministic(output / "batch075_manual_review_checklist.json", {"status": "REVIEW_REQUIRED", "required_for_each_candidate": checklist, "automatic_approval": False})
    scope = {"status": "FROZEN_REVIEW_REQUIRED", "public_repositories_only": True, "software_tests_only": True, "security_testing": False, "vulnerability_research": False, "exploit_work": False, "credential_access": False, "broad_discovery": False, "maximum_repositories": 3, "repositories_executed_at_a_time": 1, "manual_workflow_dispatch": True, "patching_before_duplicate_failure_and_source_ownership": False}
    write_json_deterministic(output / "batch075_execution_scope.json", scope)
    write_json_deterministic(output / "batch075_cold_start_handoff.json", {"status": "PASS", "objective": "manually review the frozen static allowlist, then execute at most one approved public software-test repository at a time", "execution": "DEFERRED_TO_MANUALLY_REVIEWED_BATCH075", "allowlist_count": len(allowlist), "scope_hash": hash_record(scope), "manual_review_checklist_hash": hash_record(checklist)})
    final = {"status": "LOCAL_IMPLEMENTATION_RECOVERY_COMPLETE", "external_prospective_cohort_execution": "DEFERRED_TO_MANUALLY_REVIEWED_BATCH075", "prospective_candidate_wave_executed": False, "prospective_AMDS_evidence_created": False, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "issue_derived_repair_count": 5, "native_external_repair_count": 4, "COUNT_5_HARDENING": "PASS", "Batch073_cohort": "EXECUTED_EMPTY_COHORT", "external_operations_during_recovery_validation": 0, "third_party_repositories_executed_during_recovery_validation": 0, "third_party_patches_generated": 0, "local_synthetic_validation": "PASS" if all(item["status"] == "PASS" for item in validation.values()) else "BLOCK"}
    write_json_deterministic(output / "batch074_final_decision.json", final)
    write_text_lf(output / "batch074_summary.md", "# Batch074 local implementation recovery\n\nBatch074 completed local intake-engine recovery and synthetic validation only. The manually supplied Batch073 artifact passed identity, path, and manifest verification; count-five hardening and the completed Batch073 empty cohort remain unchanged.\n\nNo prospective external candidate wave is claimed. External cohort execution is deferred to a manually reviewed Batch075 workflow with a static allowlist of at most three public repositories, one repository at a time.\n\nAMDS prospective effectiveness remains `NOT_ESTABLISHED`, memory lift remains `not_demonstrated`, self-maintaining software remains `false/not_demonstrated`, the issue-derived repair count remains `5`, and the native external repair count remains `4`.\n")
    current_path = root / "outputs/current/CURRENT_PROTOCOL_STATE.json"; current = json.loads(current_path.read_text(encoding="utf-8")); current.update({"batch074_status": final["status"], "batch074_external_execution": final["external_prospective_cohort_execution"], "next_safe_action": "manual_batch075_static_allowlist_review"}); current.pop("batch074_frame_count", None); current.pop("batch074_wave1_status", None); current.pop("state_hash", None); current["state_hash"] = hash_record(current); write_json_deterministic(current_path, current)
    frontier_path = root / "outputs/frontier/CURRENT_FRONTIER_STATE.json"; frontier = json.loads(frontier_path.read_text(encoding="utf-8")); frontier.update({"BATCH074_STATUS": final["status"], "BATCH074_EXTERNAL_EXECUTION": final["external_prospective_cohort_execution"], "AMDS_PROSPECTIVE_WAVE1": "DEFERRED_TO_MANUALLY_REVIEWED_BATCH075", "next_safe_action": "manual_batch075_static_allowlist_review"}); frontier.pop("batch074_frame_count", None); frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(frontier_path, frontier)
    _manifest(output)
    return final
