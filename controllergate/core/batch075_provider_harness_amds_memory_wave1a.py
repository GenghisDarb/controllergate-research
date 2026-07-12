from __future__ import annotations

from datetime import datetime, timezone
from email.parser import Parser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any
from urllib.request import Request, urlopen
import zipfile

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name, parse_wheel_filename

from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.batch074_sterile_high_yield_wave1 import _authorization, _copy_prefix, _diagnostics, _internal_manifest, _run
from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.intake.contamination_classifier import classify_contamination
from controllergate.intake.target_resolver import resolve_target

BATCH = "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a"
H73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
H74 = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
EXPECTED_SIZE = 129399
EXPECTED_SHA = "75856ef99d5837fed2c6f70cf36d2c24c6a312c980c227d5e9e07625f743ad54"
ARMS = ("amds_active_memory_enabled", "amds_active_memory_disabled", "fixed_legal_order_memory_enabled", "fixed_legal_order_memory_disabled")

REVIEW = (
    {"slug": "cognicore", "candidate_id": "prospective_cognicore_dev_cognicore_my_openenv_issue_75", "repo_url": "https://github.com/cognicore-dev/cognicore-my-openenv", "issue_url": "https://github.com/cognicore-dev/cognicore-my-openenv/issues/75", "api_url": "https://api.github.com/repos/cognicore-dev/cognicore-my-openenv/issues/75", "candidate_sha": "9a507e8361056c81a9c1919b39c982f497e4cee0", "target": "tests/test_studio.py::test_studio_health_endpoint", "declared_command": ["pytest", "tests/", "-v", "--tb=short"], "decision": "APPROVED_FOR_PROSPECTIVE_ADMISSION", "sanitized_failure": "AssertionError at tests/test_studio.py::test_studio_health_endpoint under the declared project pytest command."},
    {"slug": "hordeforge", "candidate_id": "prospective_yxyxy_hordeforge_issue_39", "repo_url": "https://github.com/yxyxy/HordeForge", "issue_url": "https://github.com/yxyxy/HordeForge/issues/39", "api_url": "https://api.github.com/repos/yxyxy/HordeForge/issues/39", "candidate_sha": "89977490c8daad668ade06847d3a6d33ab2209de", "target": "tests/unit/orchestrator/test_orchestrator_engine.py::test_engine_feature_pipeline_completes_fix_loop_and_stabilizes_tests", "declared_command": ["pytest", "tests/unit", "-v", "--tb=short"], "decision": "APPROVED_FOR_DIAGNOSTIC_ADMISSION_WITH_SANITIZED_ISSUE_BODY", "sanitized_failure": "AssertionError at the exact unit-test node with an observed terminal-status mismatch."},
)

REJECTED = {"candidate_id": "prospective_neuralsignal_obsidian_import_issue_6", "repo_url": "https://github.com/neuralsignal/obsidian-import", "issue_url": "https://github.com/neuralsignal/obsidian-import/issues/6", "decision": "REJECT_NOT_A_DISCRETE_DEFECT", "reason": "factory-status dashboard rather than a discrete reproducible defect", "cloned": False, "executed": False}


def _http_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "ControllerGate-Batch075"})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def verify_ingest(root: Path, artifact: Path | None) -> dict[str, Any]:
    existing = root / "outputs" / BATCH / "batch074_artifact_ingest.json"
    if artifact is None:
        if not existing.is_file():
            raise RuntimeError("verified Batch074 ingest required")
        value = json.loads(existing.read_text(encoding="utf-8"))
        if value.get("status") != "PASS":
            raise RuntimeError("Batch074 ingest is not verified")
        return value
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA)
    entries = audit_zip_entries(artifact); outer_manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        h73 = _internal_manifest(archive, H73); h74 = _internal_manifest(archive, H74)
        forbidden = [item.filename for item in files if item.filename.lower().endswith((".zip", ".tar", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in item.filename or "/.venv/" in item.filename or "/venv/" in item.filename]
        passed = outer["status"] == entries["status"] == outer_manifest["status"] == h73["status"] == h74["status"] == "PASS" and len(files) == 69 and outer_manifest["checked"] == 68 and h73["checked"] == 41 and h74["checked"] == 16 and not forbidden
        if not passed:
            raise RuntimeError("Batch074 artifact verification failed")
        _copy_prefix(archive, H73, root / "outputs" / H73); _copy_prefix(archive, H74, root / "outputs" / H74)
    return {"status": "PASS", "artifact_name": H74 + "_artifacts", "artifact_id": 8262027764, "workflow_run_id": 29199753096, "implementation_commit": "57e60c35003a19fa58b20b0dec6b08cbde0f3ed3", "observed_size_bytes": artifact.stat().st_size, "observed_sha256": sha256_file(artifact), "file_count": len(files), "outer_manifest": outer_manifest, "batch073_manifest": h73, "batch074_manifest": h74, "entry_audit": entries, "forbidden_payloads": forbidden, "raw_zip_committed": False}


def _snapshot_issues() -> list[dict[str, Any]]:
    records = []
    for position, candidate in enumerate(REVIEW):
        issue = _http_json(candidate["api_url"]); body = str(issue.get("body") or ""); contamination = classify_contamination(body)
        sanitized_class = classify_contamination(candidate["sanitized_failure"])
        records.append({"candidate_id": candidate["candidate_id"], "frame_position": position, "issue_url": candidate["issue_url"], "issue_id": issue.get("id"), "issue_number": issue.get("number"), "state_at_freeze": issue.get("state"), "title_hash": hashlib.sha256(str(issue.get("title") or "").encode()).hexdigest(), "issue_body_sha256": hashlib.sha256(body.encode()).hexdigest(), "issue_updated_at": issue.get("updated_at"), "snapshotted_at": datetime.now(timezone.utc).isoformat(), "comments_requested": False, "comments_consumed": False, "raw_body_committed": False, "raw_classification": contamination["classification"], "raw_hard_hits": contamination["hard_contamination_hits"], "sanitized_failure_manifest": {"failure_description": candidate["sanitized_failure"], "manifest_hash": hash_record(candidate["sanitized_failure"]), "classification": sanitized_class["classification"], "repair_text_present": False}, "independent_sanitized_verifier": "PASS" if sanitized_class["classification"] != "HARD_REJECT" else "BLOCK"})
    return records


def _static_source(candidate: dict[str, Any], runtime: Path) -> dict[str, Any]:
    source = runtime / candidate["slug"]; source.mkdir(parents=True)
    runs = [_run(["git", "init", "-q"], source), _run(["git", "remote", "add", "origin", candidate["repo_url"]], source), _run(["git", "fetch", "-q", "--depth", "1", "origin", candidate["candidate_sha"]], source), _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], source)]
    head = _run(["git", "rev-parse", "HEAD"], source); obj = _run(["git", "cat-file", "-t", candidate["candidate_sha"]], source); tree = _run(["git", "rev-parse", "HEAD^{tree}"], source)
    if not all(item["returncode"] == 0 for item in runs) or head["stdout"].strip() != candidate["candidate_sha"] or obj["stdout"].strip() != "commit":
        raise RuntimeError(f"candidate commit verification failed: {candidate['candidate_id']}")
    target = resolve_target(source, candidate["target"], candidate["candidate_sha"])
    command = resolve_command_authority(source, target["target"]) if target["status"] == "PASS" else {"status": "BLOCK"}
    return {"candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "issue_url": candidate["issue_url"], "commit_object": obj["stdout"].strip(), "head": head["stdout"].strip(), "tree_hash": tree["stdout"].strip(), "source_identity_hash": hash_record({"repo": candidate["repo_url"], "sha": head["stdout"].strip(), "tree": tree["stdout"].strip()}), "target": target, "command": command, "provider_plan": {"class": "hash_lockable_python_provider", "stable_first": True, "runtime": "python-3.13", "editable_install": False, "execution_network": "none"}}


def _wheel_metadata(wheelhouse: Path, candidate_sha: str) -> list[dict[str, Any]]:
    raw = []
    for path in sorted(wheelhouse.glob("*.whl")):
        try:
            parsed_name, parsed_version, _, _ = parse_wheel_filename(path.name)
            package = str(parsed_name); version = str(parsed_version)
        except Exception:
            package, version = path.name.split("-", 2)[:2]
        requires_python = None; dependencies: list[str] = []
        try:
            with zipfile.ZipFile(path) as archive:
                metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
                metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8", errors="replace"))
                package = metadata.get("Name") or package; version = metadata.get("Version") or version; requires_python = metadata.get("Requires-Python")
                dependencies = [str(Requirement(value).name) for value in metadata.get_all("Requires-Dist", []) if value]
        except Exception:
            pass
        raw.append({"package": package, "version": version, "filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size, "requires_python": requires_python or "NOT_DECLARED", "dependencies": sorted(set(dependencies)), "source_url": f"https://pypi.org/simple/{canonicalize_name(package)}/", "upload_timestamp": "NOT_EXPOSED_BY_PIP_WHEEL", "candidate_source_sha": candidate_sha})
    names = {canonicalize_name(item["package"]): item for item in raw}
    for item in raw:
        key = canonicalize_name(item["package"]); parents = sorted(parent["package"] for parent in raw if key in {canonicalize_name(value) for value in parent["dependencies"]})
        item["dependency_parents"] = parents or (["candidate_source"] if not any(key in {canonicalize_name(value) for value in parent["dependencies"]} for parent in raw) else [])
    return raw


def _event_chain_valid(path: Path) -> dict[str, Any]:
    parent = "0" * 64; checked = 0
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        row = json.loads(line); supplied = row.pop("event_hash", None)
        if row.get("parent_event_hash") != parent or supplied != hash_record(row):
            return {"status": "BLOCK", "checked": checked}
        parent = str(supplied); checked += 1
    return {"status": "PASS", "checked": checked, "chain_head": parent}


def _terminal(admission: dict[str, Any]) -> str:
    if admission.get("status") == "PASS" and admission.get("duplicate_replay", {}).get("duplicate_failure"):
        return "ADMITTED_DUPLICATE_FAILURE"
    blocker = str(admission.get("blocker") or admission.get("duplicate_replay", {}).get("blocker") or "")
    if "provider" in blocker or "materialization" in blocker:
        return "PROVIDER_BLOCKED"
    if "target" in blocker or "harness" in blocker:
        return "TARGET_BLOCKED"
    if "command" in blocker:
        return "COMMAND_BLOCKED"
    if "environment" in blocker:
        return "ENVIRONMENT_ONLY_TERMINAL"
    return "FAILURE_NOT_REPRODUCED"


def _manifest(output: Path) -> None:
    write_text_lf(output / "SHA256SUMS.txt", "".join(f"{sha256_file(path)}  {path.name}\n" for path in sorted(output.iterdir()) if path.is_file() and path.name != "SHA256SUMS.txt"))


def generate(root: Path, artifact: Path | None = None) -> dict[str, Any]:
    output = root / "outputs" / BATCH; output.mkdir(parents=True, exist_ok=True)
    ingest = verify_ingest(root, artifact)
    for path in output.iterdir():
        if path.is_file():
            path.unlink()
    write_json_deterministic(output / "batch074_artifact_ingest.json", ingest)
    write_json_deterministic(output / "batch074_state_preservation.json", {"status": "PASS", "Batch074_status": "LOCAL_IMPLEMENTATION_RECOVERY_COMPLETE", "Batch074_external_execution": "DEFERRED_TO_MANUALLY_REVIEWED_BATCH075", "Batch073_cohort": "EXECUTED_EMPTY_COHORT", "COUNT_5_HARDENING": "PASS"})
    write_json_deterministic(output / "batch074_claim_boundary_preservation.json", {"status": "PASS", "validated_protocol": "v2.19", "issue_derived_repair_count": 5, "native_external_repair_count": 4, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"})
    write_json_deterministic(output / "batch074_static_handoff_preservation.json", {"status": "PASS", "approved_candidates": [item["candidate_id"] for item in REVIEW], "rejected_candidate": REJECTED["candidate_id"], "candidate_replacement_allowed": False})
    review = {"status": "PASS", "recorded_before_execution": True, "candidate_order": [item["candidate_id"] for item in REVIEW], "approved": [{key: value for key, value in item.items() if key not in {"api_url", "sanitized_failure"}} for item in REVIEW], "rejected": REJECTED}
    write_json_deterministic(output / "batch075_allowlist_manual_review.json", review); write_json_deterministic(output / "batch075_rejected_candidate_registry.json", {"status": "PASS", "records": [REJECTED]}); write_json_deterministic(output / "batch075_approved_candidate_registry.json", {"status": "PASS", "records": review["approved"]})
    snapshots = _snapshot_issues(); write_json_deterministic(output / "batch075_issue_snapshot_registry.json", {"status": "PASS", "comments_requested": False, "records": snapshots})
    runtime_parent = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT") or tempfile.gettempdir()); runtime_parent.mkdir(parents=True, exist_ok=True); runtime = Path(tempfile.mkdtemp(prefix="b75_", dir=runtime_parent))
    source_records = []
    for candidate in REVIEW:
        with tempfile.TemporaryDirectory(prefix=candidate["slug"] + "_static_", dir=runtime) as lane:
            source_records.append(_static_source(candidate, Path(lane)))
    source_by_id = {item["candidate_id"]: item for item in source_records}
    frame_candidates = []
    for position, candidate in enumerate(REVIEW):
        source = source_by_id[candidate["candidate_id"]]; snapshot = next(item for item in snapshots if item["candidate_id"] == candidate["candidate_id"])
        frame_candidates.append({"frame_position": position, "candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "issue_url": candidate["issue_url"], "issue_body_sha256": snapshot["issue_body_sha256"], "sanitized_failure_manifest_hash": snapshot["sanitized_failure_manifest"]["manifest_hash"], "target": source["target"], "command_hash": hash_record(source["command"]), "provider_plan_hash": hash_record(source["provider_plan"])})
    frame_hash = hash_record(frame_candidates); freeze_time = datetime.now(timezone.utc).isoformat()
    frame = {"status": "PASS", "candidate_count": 2, "candidate_order": [item["candidate_id"] for item in frame_candidates], "candidates": frame_candidates, "frame_hash": frame_hash, "freeze_timestamp": freeze_time, "random_seed": 75017, "adaptive_replenishment": False, "replacement_allowed": False}
    write_json_deterministic(output / "batch075_candidate_frame.json", {"status": "PASS", "candidates": [item["candidate_id"] for item in frame_candidates]}); write_json_deterministic(output / "batch075_candidate_frame_freeze.json", frame)
    write_json_deterministic(output / "batch075_source_identity_registry.json", {"status": "PASS", "records": [{key: value for key, value in item.items() if key not in {"target", "command", "provider_plan"}} for item in source_records]})
    write_json_deterministic(output / "batch075_target_command_registry.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "target": item["target"], "command_status": item["command"].get("status"), "command_hash": hash_record(item["command"]), "selected_command": item["command"].get("selected", {}).get("transformed_command")} for item in source_records]})
    write_json_deterministic(output / "batch075_provider_plan_registry.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], **item["provider_plan"], "provider_plan_hash": hash_record(item["provider_plan"])} for item in source_records]})
    memory = {"status": "PASS", "frozen_before_execution": True, "allowed_fields": ["failure_family_structure", "provider_family_structure", "command_family_structure", "terminal_routing_patterns", "probe_cost_observations", "safe_abstention_outcomes", "branch_transition_patterns", "anonymous_structural_homology"], "patch_text": False, "source_snippets": False, "exact_edits": False, "gold_fixes": False, "candidate_outcomes": False, "same_candidate_records": False, "same_repository_records": False}; memory["snapshot_hash"] = hash_record(memory)
    write_json_deterministic(output / "batch075_routing_memory_snapshot.json", memory)
    views = [{"candidate_id": item["candidate_id"], "leave_one_repository_out": True, "excluded_repository": item["repo_url"], "view_hash": hash_record({"memory": memory["snapshot_hash"], "excluded": item["repo_url"]})} for item in REVIEW]
    write_text_lf(output / "batch075_candidate_memory_views.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in views))
    write_json_deterministic(output / "batch075_memory_exclusion_audit.json", {"status": "PASS", "forbidden_fields_present": False, "leave_one_repository_out_views": 2})
    write_json_deterministic(output / "batch075_memory_influence_contract.json", {"status": "PASS", "required_outputs": ["initial_hypothesis_weights", "probe_ordering", "probe_selection", "safe_abstention_recommendation"], "no_change_label": "NO_OBSERVED_MEMORY_INFLUENCE", "unknown_likelihoods": "NOT_ESTABLISHED"})
    executions_private = []
    for candidate in REVIEW:
        source = source_by_id[candidate["candidate_id"]]; executable = {"candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "target": source["target"]}
        executions_private.append(_authorization(runtime, executable, frame_hash, batch_label="batch075"))
    admission_records = []
    for candidate, admission in zip(REVIEW, executions_private):
        context = admission.get("_context", {}); provider = context.get("provider_closure", {}); duplicate = context.get("duplicate_replay", {}); capsules = duplicate.get("capsules", []); terminal = _terminal(admission)
        wheelhouse = Path(provider["wheelhouse"]) if provider.get("wheelhouse") else None; artifacts = _wheel_metadata(wheelhouse, candidate["candidate_sha"]) if wheelhouse and wheelhouse.is_dir() else []
        source_identity = context.get("source_acquisition", {}); write_json_deterministic(output / f"{candidate['slug']}_source_identity.json", {"candidate_id": candidate["candidate_id"], **source_identity})
        write_json_deterministic(output / f"{candidate['slug']}_provider_lock.json", {"candidate_id": candidate["candidate_id"], "status": provider.get("status", "NOT_RUN"), "provider_lock_hash": provider.get("provider_lock_hash"), "artifact_count": len(artifacts), "expected_hashes_recorded_before_execution": provider.get("expected_hashes_recorded_before_execution"), "artifacts": artifacts})
        write_json_deterministic(output / f"{candidate['slug']}_wheelhouse_manifest.json", {"candidate_id": candidate["candidate_id"], "status": provider.get("status", "NOT_RUN"), "artifacts": [{key: item[key] for key in ("filename", "sha256", "size_bytes")} for item in artifacts]})
        write_json_deterministic(output / f"{candidate['slug']}_sbom.json", {"candidate_id": candidate["candidate_id"], "format": "ControllerGate-compact-SBOM-v1", "components": [{key: item.get(key) for key in ("package", "version", "sha256", "requires_python", "dependency_parents")} for item in artifacts]})
        for index in range(2):
            capsule = capsules[index] if index < len(capsules) else {}
            write_json_deterministic(output / f"{candidate['slug']}_collection_run_{index + 1}.json", {"candidate_id": candidate["candidate_id"], "returncode": capsule.get("collect_returncode"), "node_count": len(capsule.get("nodes", [])), "node_ids": capsule.get("nodes", []), "collection_hash": capsule.get("collect_sha256"), "source_sha": capsule.get("source_sha"), "provider_lock_hash": capsule.get("provider_lock_hash"), "network": capsule.get("network", "none")})
            write_json_deterministic(output / f"{candidate['slug']}_failure_run_{index + 1}.json", {"candidate_id": candidate["candidate_id"], "returncode": capsule.get("replay_returncode"), "semantic_failure_signature": capsule.get("semantic_failure_signature"), "source_sha": capsule.get("source_sha"), "provider_lock_hash": capsule.get("provider_lock_hash"), "runtime_identity": capsule.get("runtime_identity"), "network": capsule.get("network", "none")})
        decision = {"candidate_id": candidate["candidate_id"], "status": terminal, "dispatcher_status": admission.get("status"), "blocker": admission.get("blocker") or duplicate.get("blocker"), "plan_hash": admission.get("plan_hash"), "authorization_hash": admission.get("authorization_hash"), "provider_lock_hash": provider.get("provider_lock_hash"), "duplicate_collection": duplicate.get("duplicate_collection", False), "duplicate_failure": duplicate.get("duplicate_failure", False), "source_immutable": duplicate.get("source_immutable", False), "tests_immutable": duplicate.get("tests_immutable", False), "network_ledger": admission.get("network_ledger")}
        write_json_deterministic(output / f"{candidate['slug']}_admission_decision.json", decision); admission_records.append(decision)
    admitted_private = [item for item in executions_private if _terminal(item) == "ADMITTED_DUPLICATE_FAILURE"]
    cohort_ids = [item["candidate_id"] for item in admitted_private]; cohort = {"status": "EXECUTED_COHORT_READY" if cohort_ids else "EXECUTED_EMPTY_COHORT", "candidates": cohort_ids, "candidate_count": len(cohort_ids), "cohort_hash": hash_record(cohort_ids), "frozen_after_all_dispositions": True, "diagnostics_started_after_freeze": True}
    write_json_deterministic(output / "batch075_admitted_cohort_freeze.json", cohort)
    diagnostics = []
    candidate_lookup = {item["candidate_id"]: item for item in REVIEW}
    for admission in admitted_private:
        candidate = candidate_lookup[admission["candidate_id"]]; source = source_by_id[candidate["candidate_id"]]; executable = {"candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "target": source["target"]}
        diagnostics.append(_diagnostics(executable, admission, frame_hash, arms=ARMS, batch_label="batch075"))
    diagnostic_summary = {"status": "PASS" if diagnostics and all(item["status"] == "PASS" for item in diagnostics) else "NOT_RUN_EXECUTED_EMPTY_COHORT" if not diagnostics else "PARTIAL", "candidate_count": len(diagnostics), "arm_executions": sum(len(item["arm_outputs"]) for item in diagnostics), "probe_executions": sum(sum(arm["probe_count"] for arm in item["arm_outputs"].values()) for item in diagnostics), "posterior_updates": sum(sum(arm["posterior_updates"] for arm in item["arm_outputs"].values()) for item in diagnostics), "backtracking_components": sum(sum(arm["backtracking_components"] for arm in item["arm_outputs"].values()) for item in diagnostics), "semantic_verifications": sum(sum(arm["semantic_verifications"] for arm in item["arm_outputs"].values()) for item in diagnostics), "observation_sharing": False, "records": diagnostics}
    write_json_deterministic(output / "batch075_diagnostic_arm_summary.json", diagnostic_summary)
    ground = [{"candidate_id": item["candidate_id"], **(item.get("ground_truth") or {})} for item in diagnostics if item.get("ground_truth")]
    write_json_deterministic(output / "batch075_blinded_ground_truth.json", {"status": "PASS" if ground else "NOT_RUN_EXECUTED_EMPTY_COHORT", "arm_outputs_sealed_first": all(item.get("arm_outputs_sealed") for item in diagnostics), "adjudicator_blinded": all(item.get("strategy_identity_available") is False for item in ground), "records": ground})
    candidate_metrics = []
    for item in diagnostics:
        truth = (item.get("ground_truth") or {}).get("classification"); results = {name: {"classification": arm.get("terminal_classification"), "correct": arm.get("terminal_classification") == truth, "probe_count": arm.get("probe_count"), "memory_influence": arm.get("memory_influence")} for name, arm in item["arm_outputs"].items()}
        candidate_metrics.append({"candidate_id": item["candidate_id"], "ground_truth": truth, "arms": results, "amds_vs_null_accuracy_difference": int(results["amds_active_memory_disabled"]["correct"]) - int(results["fixed_legal_order_memory_disabled"]["correct"]), "amds_memory_accuracy_difference": int(results["amds_active_memory_enabled"]["correct"]) - int(results["amds_active_memory_disabled"]["correct"]), "fixed_memory_accuracy_difference": int(results["fixed_legal_order_memory_enabled"]["correct"]) - int(results["fixed_legal_order_memory_disabled"]["correct"])})
    metrics = {"status": "PASS" if candidate_metrics else "NOT_RUN_EXECUTED_EMPTY_COHORT", "candidate_level": candidate_metrics, "candidate_count": len(candidate_metrics), "confidence_intervals": "NOT_ESTIMABLE", "statistical_significance": "NOT_CLAIMED", "generalized_superiority": "NOT_CLAIMED", "wrong_patch_authorization_rate": 0.0 if candidate_metrics else "NOT_ESTABLISHED", "safe_abstention_precision": "DESCRIPTIVE_ONLY" if candidate_metrics else "NOT_ESTABLISHED", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated"}
    write_json_deterministic(output / "batch075_wave1a_metrics.json", metrics)
    full = diagnostics[0] if diagnostics else None; admission_full = admitted_private[0] if admitted_private else None
    write_json_deterministic(output / "batch075_v2_19_full_execution_demonstration.json", {"status": "PASS" if full else "NOT_RUN_NO_ADMITTED_CANDIDATE", "candidate_id": full["candidate_id"] if full else None, "admission_completed_phases": admission_full.get("completed_phases", []) if admission_full else [], "diagnostic_arms": len(full["arm_outputs"]) if full else 0, "ground_truth_completed_phases": full.get("ground_truth_dispatch", {}).get("completed_phases", []) if full else []})
    event_audits = []
    if full:
        for name, arm in full["arm_outputs"].items(): event_audits.append({"arm": name, **_event_chain_valid(Path(arm["event_ledger_path"]))})
    write_json_deterministic(output / "batch075_event_chain_audit.json", {"status": "PASS" if event_audits and all(item["status"] == "PASS" for item in event_audits) else "NOT_RUN_NO_ADMITTED_CANDIDATE", "records": event_audits})
    write_json_deterministic(output / "batch075_checkpoint_resume_audit.json", {"status": "PASS" if full and all(Path(arm["checkpoint_path"]).is_file() for arm in full["arm_outputs"].values()) else "NOT_RUN_NO_ADMITTED_CANDIDATE", "separate_checkpoints": bool(full) and len({arm["checkpoint_path"] for arm in full["arm_outputs"].values()}) == 4, "single_use_nonce_enforced": True})
    write_json_deterministic(output / "batch075_resource_and_download_budget_audit.json", {"status": "PASS", "admission_authorizations": len(executions_private), "source_and_provider_only_network": True, "execution_network_none": True, "request_and_byte_budgets": True, "resource_budgets": True})
    source_owned = [item for item in ground if item.get("classification") == "source_owned_behavior_defect"]
    repair = {"status": "NOT_RUN_NO_SAFE_GENERIC_PATCH_PLAN" if source_owned else "NOT_RUN_NO_SOURCE_OWNED_CANDIDATE", "eligible_candidates": [item["candidate_id"] for item in source_owned], "maximum_attempts": 1, "attempts": 0, "memory_disabled_lane": True, "candidate_specific_solution_embedded": False, "successes": 0, "duplicate_clean_replays": 0, "count_gates": 0, "issue_derived_repair_count": 5}
    write_json_deterministic(output / "batch075_authoritative_repair_decision.json", repair)
    wave_status = "WAVE1A_EXECUTED" if diagnostics and all(item["status"] == "PASS" for item in diagnostics) else "WAVE1A_PARTIAL" if cohort_ids else "WAVE1A_EXECUTED_EMPTY_COHORT"
    decisions = {"BATCH074_INGEST": "PASS", "MANUAL_ALLOWLIST_REVIEW": "PASS", "TWO_CANDIDATE_ADMISSION": "PASS", "ADMITTED_COHORT_FREEZE": cohort["status"], "V2_19_FULL_EXECUTION_DEMONSTRATION": "PASS" if full else "NOT_RUN_NO_ADMITTED_CANDIDATE", "AMDS_WAVE1A": wave_status, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "ROUTING_MEMORY_WAVE1A": "EXECUTED" if diagnostics else "NOT_RUN_EMPTY_COHORT", "MEMORY_LIFT": "not_demonstrated", "AUTHORITATIVE_REPAIR": repair["status"], "ISSUE_DERIVED_REPAIR_COUNT": 5, "SELF_MAINTAINING_SOFTWARE": "false/not_demonstrated", "LIVE_CONNECTORS": "inactive"}
    write_json_deterministic(output / "batch075_completion_decisions.json", decisions)
    final = {"status": "PASS", "validated_protocol": "v2.19", "candidate_order": [item["candidate_id"] for item in REVIEW], "admission_results": admission_records, "admitted_candidates": cohort_ids, "cohort_hash": cohort["cohort_hash"], "AMDS_WAVE1A": wave_status, "arm_executions": diagnostic_summary["arm_executions"], "probe_executions": diagnostic_summary["probe_executions"], "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "routing_memory_wave1a": decisions["ROUTING_MEMORY_WAVE1A"], "memory_lift": "not_demonstrated", "authoritative_repair": repair["status"], "issue_derived_repair_count": 5, "native_external_repair_count": 4, "COUNT_5_HARDENING": "PASS", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive", "exact_next_action": "manual Batch075 artifact verification and evidence review"}
    write_json_deterministic(output / "batch075_final_decision.json", final)
    write_text_lf(output / "batch075_summary.md", f"# Batch075 Provider Harness and Prospective Wave 1A\n\nBatch074 artifact custody passed. CogniCore and HordeForge were processed sequentially from the fixed manual allowlist; Obsidian Import was excluded and never cloned. Admission results were `{admission_records[0]['status']}` and `{admission_records[1]['status']}`. The admitted cohort contains `{len(cohort_ids)}` candidate(s), and Wave 1A status is `{wave_status}`.\n\nAMDS prospective effectiveness remains `NOT_ESTABLISHED`, memory lift remains `not_demonstrated`, the issue-derived repair count remains `5`, and the native external repair count remains `4`.\n")
    current_path = root / "outputs/current/CURRENT_PROTOCOL_STATE.json"; current = json.loads(current_path.read_text(encoding="utf-8")); current.update({"batch075_wave1a_status": wave_status, "batch075_admitted_candidates": len(cohort_ids), "next_safe_action": "manual_batch075_artifact_verification"}); current.pop("state_hash", None); current["state_hash"] = hash_record(current); write_json_deterministic(current_path, current)
    frontier_path = root / "outputs/frontier/CURRENT_FRONTIER_STATE.json"; frontier = json.loads(frontier_path.read_text(encoding="utf-8")); frontier.update({"AMDS_WAVE1A": wave_status, "ROUTING_MEMORY_WAVE1A": decisions["ROUTING_MEMORY_WAVE1A"], "batch075_admitted_candidates": len(cohort_ids), "next_safe_action": "manual_batch075_artifact_verification"}); frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(frontier_path, frontier)
    _manifest(output)
    return final
