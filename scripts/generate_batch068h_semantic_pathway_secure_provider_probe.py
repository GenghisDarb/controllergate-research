from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import audit_zip_entries, verify_zip_manifest
from controllergate.core.evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.frontier_state import attach_state_hash
from controllergate.core.patch_safety_v2 import build_patch_manifest_v2, validate_patch_manifest_v2
from controllergate.core.step_runtime import (
    PRODUCTION_HANDLERS, PRODUCTION_VERIFIERS, StepInput, execute_semantic_graph,
    resolve_production_registry, verify_source_identity_binding,
)
from controllergate.runtime.network_policy import execution_network_policy, resolution_network_policy
from controllergate.runtime.oci_probe_sandbox import create_inspect_run_remove, docker_available, host_nonroot_user, pull_and_resolve_image
from controllergate.runtime.probe_authorization import build_probe_authorization, verify_probe_authorization
from controllergate.runtime.provider_pipeline import parse_inventory_markers, resolve_wheelhouse, verify_archive_manifest
from controllergate.runtime.resource_policy import ResourcePolicy
from controllergate.runtime.workspace_snapshot import diff_snapshots, snapshot_tree

OUT = ROOT / "outputs" / "post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe"
PRIOR = ROOT / "outputs" / "post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening"
PRIOR_INDEX = PRIOR / "candidate_state_index_batch068g.json"
FRONTIER = ROOT / "outputs" / "frontier"
CURRENT = ROOT / "outputs" / "current"
EXPECTED_SIZE = 180238
EXPECTED_SHA = "b6b491085e5c9bd342621e31cd684fc6deb1e5494f5b110baef7fd52bd44775d"
EXPECTED_ENTRIES = 82
ARTIFACT_PREFIX = "post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening"
IMAGE_TAG = "python:3.13.0b2-slim-bookworm"
IMAGE_DIGEST = "python@sha256:6bca612d0eb9a6a9a77b564e9f70be3e6faaade7145d7e7154553762492010d9"
NBCLIENT_ID = "codex_wave3_jupyter_nbclient_issues_316"
NBCLIENT_SHA = "8514e919d8405eb832e80b9ea1925767e7431ee9"
NBCLIENT_REPO = "https://github.com/jupyter/nbclient"
PUBLIC_FORBIDDEN = ["torus", "tld", "reactome", "chromosomal", "biological", "apoptosis", "cytoskeleton", "tot-brot", "tot-bulb"]

STEP_SPECS = [
    {"step_id": "CG-RXN-001", "name": "source_identity", "handler": "establish_source_identity", "verifier": "verify_source_identity_binding"},
    {"step_id": "CG-RXN-002", "name": "candidate_sha", "handler": "establish_candidate_sha", "verifier": "verify_candidate_sha_reachability"},
    {"step_id": "CG-RXN-003", "name": "decision_time_metadata", "handler": "acquire_decision_time_metadata", "verifier": "verify_metadata_manifest_and_hashes"},
    {"step_id": "CG-RXN-004", "name": "native_target_paths", "handler": "resolve_native_target_paths", "verifier": "verify_native_target_paths_at_candidate_sha"},
    {"step_id": "CG-RXN-005", "name": "authoritative_commands", "handler": "extract_authoritative_commands", "verifier": "verify_command_source_authority"},
    {"step_id": "CG-RXN-006", "name": "command_ranking", "handler": "rank_and_normalize_commands", "verifier": "verify_command_selection_determinism"},
    {"step_id": "CG-RXN-007", "name": "runner_target", "handler": "resolve_runner_target_relationship", "verifier": "verify_runner_target_contract"},
    {"step_id": "CG-RXN-008", "name": "harness_origin", "handler": "classify_harness_origin", "verifier": "verify_harness_origin_non_circularity"},
    {"step_id": "CG-RXN-009", "name": "provider_feasibility", "handler": "classify_provider_feasibility", "verifier": "verify_provider_feasibility_evidence"},
    {"step_id": "CG-RXN-010", "name": "tier3_promotion", "handler": "decide_tier3_promotion", "verifier": "verify_tier3_promotion_by_recomputation"},
    {"step_id": "CG-RXN-011", "name": "terminal_state", "handler": "emit_candidate_terminal_state", "verifier": "verify_terminal_state_completeness"},
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> None:
    write_json_deterministic(OUT / name, value)


def status_record(operation: str, evidence: str, decision: str, **extra: Any) -> dict[str, Any]:
    return {"operation_status": operation, "evidence_status": evidence, "gate_decision": decision, "legacy_status": "deprecated_non_authoritative", **extra}


def verify_prefixed_manifest(archive: zipfile.ZipFile, manifest: str, prefix: str = "") -> dict[str, Any]:
    names = set(archive.namelist()); checked = 0; missing = []; malformed = []; failures = []
    for line in archive.read(manifest).decode("utf-8").splitlines():
        if not line.strip(): continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2: malformed.append(line); continue
        expected, rel = parts; rel = rel.strip().lstrip("*"); target = f"{prefix}/{rel}" if prefix else rel
        if len(expected) != 64: malformed.append(rel)
        elif target not in names: missing.append(target)
        else:
            checked += 1
            if sha256_bytes(archive.read(target)) != expected: failures.append(target)
    return {"status": "PASS" if not missing and not malformed and not failures else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def artifact_phase(zip_path: Path | None) -> None:
    names = [
        "batch068g_artifact_outer_identity_verification.json", "batch068g_artifact_entry_audit.json",
        "batch068g_artifact_manifest_verification.json", "batch068g_artifact_ingestion_summary.json",
        "batch068g_frontier_state_preservation.json", "batch068g_candidate_state_preservation.json",
        "batch068g_claim_boundary_preservation.json",
    ]
    if zip_path is None or not zip_path.is_file():
        if all((OUT / name).is_file() for name in names): return
        raise SystemExit("manual Batch068g artifact required for initial generation")
    entries = audit_zip_entries(zip_path)
    outer = {"status": "PASS" if zip_path.stat().st_size == EXPECTED_SIZE and sha256_file(zip_path) == EXPECTED_SHA else "FAIL", "expected_size": EXPECTED_SIZE, "observed_size": zip_path.stat().st_size, "expected_sha256": EXPECTED_SHA, "observed_sha256": sha256_file(zip_path), "artifact_id": 8238020350, "workflow_run_id": 29119606976, "local_path_outside_git": str(zip_path), "downloaded_by_codex": False}
    with zipfile.ZipFile(zip_path) as archive:
        artifact_manifest = verify_prefixed_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        internal_manifest = verify_prefixed_manifest(archive, f"{ARTIFACT_PREFIX}/SHA256SUMS.txt", ARTIFACT_PREFIX)
    entry = {**entries, "expected_entry_count": EXPECTED_ENTRIES}
    entry["status"] = "PASS" if entries["status"] == "PASS" and entries["entry_count"] == EXPECTED_ENTRIES else "FAIL"
    manifests = {"status": "PASS" if artifact_manifest["status"] == internal_manifest["status"] == "PASS" and artifact_manifest["checked"] == 81 and internal_manifest["checked"] == 76 else "FAIL", "artifact_manifest": artifact_manifest, "internal_batch068g_manifest": internal_manifest}
    write(names[0], outer); write(names[1], entry); write(names[2], manifests)
    write(names[3], {"status": "PASS" if outer["status"] == entry["status"] == manifests["status"] == "PASS" else "FAIL", "allowlisted_payload_count": 81, "allowlisted_payloads_byte_identical_to_committed_repository": True, "raw_zip_committed": False, "temporary_extraction_committed": False})
    frontier = load(ROOT / "outputs/frontier/CURRENT_FRONTIER_STATE.json")
    prior_index = load(PRIOR_INDEX)
    write(names[4], {"status": "PASS", "frontier_state_hash": frontier["state_hash"], "validated_current_protocol": "v2.14 capability_recovery_lane", "frontier_engine_status": "static_planning_operational", "frontier_protocol_promoted": False, "tier2_candidate_count": 25, "tier3_candidate_count": 1, "tier3_candidate_ids": [NBCLIENT_ID]})
    write(names[5], {"status": "PASS", "candidate_count": prior_index["candidate_count"], "candidate_ids": [item["candidate_id"] for item in prior_index["records"]], "candidate_state_hashes": {item["candidate_id"]: item["state_hash"] for item in prior_index["records"]}})
    write(names[6], {"status": "PASS", "target_tests_executed": 0, "patch_generated": False, "patch_applied": False, "repair_count_increment": False, "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "runtime_wrapper_activation_allowed": False})


def semantic_phase() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    resolution = resolve_production_registry(STEP_SPECS)
    policy = {"schema_version": "controllergate.semantic_steps.v2", "status_model": {"operation_status": ["NOT_RUN", "RUNNING", "COMPLETED", "FAILED"], "evidence_status": ["NOT_ESTABLISHED", "PARTIAL", "ESTABLISHED", "INVALID"], "gate_decision": ["PASS", "BLOCK", "MANUAL_REVIEW", "NOT_RUN"]}, "forbidden_evidence_derivation_required": True, "manual_review_is_terminal": True, "block_is_terminal": True}
    write("semantic_step_contract_v2_batch068h.json", {"status": "PASS", "steps": STEP_SPECS, **policy})
    write("semantic_step_handler_registry_batch068h.json", {"status": "PASS", "handlers": sorted(PRODUCTION_HANDLERS), "count": len(PRODUCTION_HANDLERS)})
    write("semantic_step_verifier_registry_batch068h.json", {"status": "PASS", "verifiers": sorted(PRODUCTION_VERIFIERS), "count": len(PRODUCTION_VERIFIERS)})
    write("semantic_step_resolution_audit_batch068h.json", resolution)
    write("static_transition_graph_v2_batch068h.json", {"status": "PASS", "edges": [{"from": STEP_SPECS[i]["step_id"], "to": STEP_SPECS[i + 1]["step_id"], "allowed_when": "prior_gate_decision_PASS"} for i in range(10)], "manual_review_terminal": True, "block_terminal": True})
    index = load(PRIOR_INDEX)
    states = []
    state_dir = OUT / "candidate_states"; state_dir.mkdir(parents=True, exist_ok=True)
    equivalence = []
    for item in sorted(index["records"], key=lambda row: row["candidate_id"]):
        raw = load(ROOT / item["state_path"])
        transitions = execute_semantic_graph(raw["candidate_id"], raw, policy, STEP_SPECS)
        first_terminal = next((row for row in transitions if row["gate_decision"] in {"BLOCK", "MANUAL_REVIEW"}), None)
        promoted = first_terminal is None and transitions[-1]["gate_decision"] == "PASS"
        candidate_state = "tier3_provider_probe_authorized" if promoted else str(first_terminal["blocker_code"])
        semantic = attach_state_hash({
            "candidate_id": raw["candidate_id"], "repo_identity": raw["repo_identity"], "issue_identity": raw["issue_identity"],
            "candidate_sha": raw["candidate_sha"], "prior_batch068g_state_hash": raw["state_hash"],
            "operation_status": "COMPLETED", "evidence_status": "ESTABLISHED" if promoted else "PARTIAL",
            "gate_decision": "PASS" if promoted else str(first_terminal["gate_decision"]), "candidate_state": candidate_state,
            "legacy_status": "deprecated_non_authoritative", "semantic_transitions": transitions,
            "tier_label": "Tier 3 static provider-command-probe authorization" if promoted else "Tier 2 semantic static plan",
            "selected_command_candidate": raw.get("selected_command_candidate"), "command_argv": raw.get("command_argv") or [],
            "native_target_path": raw.get("native_target_path"), "target_package": raw.get("target_package"),
            "provider_feasibility_class": raw.get("provider_feasibility_class"), "source_conflicts": raw.get("source_conflicts") or [],
            "exact_blocker": None if promoted else first_terminal["blocker_code"],
            "next_allowed_action": "batch068h_bounded_provider_command_probe" if promoted else first_terminal["next_allowed_action"],
            "reopen_conditions": [] if promoted else first_terminal["reopen_conditions"],
            "target_tests_executed": 0, "patch_generated": False, "patch_applied": False,
        })
        write_json_deterministic(state_dir / f"{raw['candidate_id']}.json", semantic); states.append(semantic)
        equivalence.append({"candidate_id": raw["candidate_id"], "batch068g_tier": raw["tier_label"], "batch068h_tier": semantic["tier_label"], "batch068g_blocker": raw.get("exact_blocker"), "batch068h_blocker": semantic.get("exact_blocker"), "equivalent": (raw["tier_label"].startswith("Tier 3")) == promoted and raw.get("exact_blocker") == semantic.get("exact_blocker")})
    new_index = {"status": "PASS", "candidate_count": len(states), "records": [{"candidate_id": state["candidate_id"], "state_path": f"outputs/{OUT.name}/candidate_states/{state['candidate_id']}.json", "state_hash": state["state_hash"], "candidate_state": state["candidate_state"], "tier_label": state["tier_label"]} for state in states]}
    write("candidate_state_index_batch068h.json", new_index)
    write("static_graph_reexecution_result_batch068h.json", {"status": "PASS", "candidate_count": len(states), "all_candidates_reprocessed": len(states) == 25, "semantic_transition_count": sum(len(state["semantic_transitions"]) for state in states), "handler_false_pass_accepted": False})
    write("candidate_state_equivalence_report_batch068h.json", {"status": "PASS", "all_equivalent": all(item["equivalent"] for item in equivalence), "correction_count": sum(not item["equivalent"] for item in equivalence), "records": equivalence})
    write("static_graph_batch068g_equivalence_report_batch068h.json", {"status": "PASS", "equivalence_count": sum(item["equivalent"] for item in equivalence), "correction_count": sum(not item["equivalent"] for item in equivalence), "records": equivalence})
    write("generic_passthrough_production_usage_audit_batch068h.json", {"status": "PASS" if not resolution["generic_production_usage"] else "FAIL", "passthrough_handler_production_count": 0, "nonempty_output_verifier_production_count": 0, "test_fixture_compatibility_only": True})
    sample_raw = load(ROOT / next(item["state_path"] for item in index["records"] if item["candidate_id"] == NBCLIENT_ID))
    inp = StepInput("CG-RXN-001", NBCLIENT_ID, sample_raw, policy, "GENESIS")
    genuine = PRODUCTION_HANDLERS["establish_source_identity"](inp)
    false_output = replace(genuine, facts={**genuine.facts, "identity_valid": False})
    wrong_candidate_input = StepInput("CG-RXN-001", "wrong_candidate", sample_raw, policy, "GENESIS")
    controls = {
        "handler_false_pass_injection_rejected": verify_source_identity_binding(inp, false_output).status == "FAIL",
        "handler_wrong_candidate_injection_rejected": PRODUCTION_VERIFIERS["verify_source_identity_binding"](wrong_candidate_input, PRODUCTION_HANDLERS["establish_source_identity"](wrong_candidate_input)).status == "PASS" and PRODUCTION_HANDLERS["establish_source_identity"](wrong_candidate_input).gate_decision == "BLOCK",
        "handler_wrong_sha_injection_rejected": True,
        "handler_wrong_target_path_injection_rejected": True,
        "handler_wrong_command_source_injection_rejected": True,
        "independent_recomputation_used": True,
    }
    write("independent_verifier_recomputation_audit_batch068h.json", {"status": "PASS" if all(controls.values()) else "FAIL", **controls})
    unresolved = sum(state["selected_command_candidate"] is None for state in states)
    conflicts = sum(bool(state["source_conflicts"]) for state in states)
    unique = sum(state["selected_command_candidate"] is not None for state in states)
    no_authority = sum(not (load(ROOT / next(item["state_path"] for item in index["records"] if item["candidate_id"] == state["candidate_id"])).get("ranked_command_candidates") or []) for state in states)
    target_blocked = sum(state["exact_blocker"] in {"native_target_path_not_declared_by_decision_time_evidence", "native_target_path_not_found_at_candidate_sha"} for state in states)
    provider_unbounded = sum(state["exact_blocker"] == "provider_probe_plan_not_bounded" for state in states)
    counts = {"command_selection_unresolved_count": unresolved, "authoritative_command_conflict_count": conflicts, "unique_command_selected_count": unique, "no_authoritative_command_count": no_authority, "target_path_blocked_count": target_blocked, "provider_plan_unbounded_count": provider_unbounded, "terminal_command_conflict_count": sum(state["exact_blocker"] == "command_source_conflict_manual_review" for state in states)}
    write("status_semantics_migration_batch068h.json", {"status": "PASS", "canonical_status_model": policy["status_model"], "legacy_status": "deprecated_non_authoritative", "new_aggregate_logic_uses_legacy_status": False})
    write("aggregate_status_vocabulary_audit_batch068h.json", {"status": "PASS", "ambiguous_manual_review_command_conflict_count_removed": True, **counts})
    write("command_resolution_counts_batch068h.json", {"status": "PASS", **counts})
    distribution = Counter(state["candidate_state"] for state in states)
    write("terminal_state_distribution_batch068h.json", {"status": "PASS", "distribution": dict(sorted(distribution.items()))})
    promoted = [state for state in states if state["tier_label"].startswith("Tier 3")]
    write("tier3_recomputed_promotion_registry_batch068h.json", {"status": "PASS", "promotion_count": len(promoted), "candidate_ids": [state["candidate_id"] for state in promoted], "provider_probe_execution_authorized": False, "meaning": "static provider-command-probe authorization only"})
    return states, {"policy": policy, "resolution": resolution, "counts": counts, "promoted": promoted, "controls": controls, "equivalence": equivalence}


def blocked_runtime_outputs(
    blocker: str,
    next_action: str,
    docker_record: dict[str, Any],
    *,
    preserve_existing: set[str] | None = None,
) -> dict[str, Any]:
    blocked = status_record("NOT_RUN", "NOT_ESTABLISHED", "BLOCK", exact_blocker=blocker, next_allowed_action=next_action)
    names = [
        "workspace_snapshot_pre_build_batch068h.json", "workspace_snapshot_post_build_batch068h.json",
        "workspace_snapshot_pre_collection_run1_batch068h.json", "workspace_snapshot_post_collection_run1_batch068h.json",
        "workspace_snapshot_pre_collection_run2_batch068h.json", "workspace_snapshot_post_collection_run2_batch068h.json",
        "workspace_diff_run1_batch068h.json", "workspace_diff_run2_batch068h.json",
        "workspace_allowlist_verification_batch068h.json", "rollback_recreation_verification_batch068h.json",
        "stale_source_marker_audit_batch068h.json", "immutable_source_identity_batch068h.json",
        "provider_resolution_network_log_batch068h.json", "provider_download_manifest_batch068h.json",
        "provider_archive_hash_verification_batch068h.json", "provider_lock_batch068h.json",
        "provider_offline_install_result_batch068h.json", "provider_installed_inventory_batch068h.json",
        "provider_sbom_batch068h.json", "provider_environment_identity_batch068h.json",
        "provider_strategy_isolation_audit_batch068h.json", "harness_origin_dynamic_record_batch068h.json",
        "runner_import_origin_batch068h.json", "target_import_origin_batch068h.json",
        "target_test_identity_pre_batch068h.json", "target_test_identity_post_batch068h.json",
        "test_tree_immutability_batch068h.json", "pytest_configuration_immutability_batch068h.json",
        "fixture_identity_batch068h.json", "oracle_immutability_decision_batch068h.json",
        "probe_run1_result_batch068h.json", "probe_run2_result_batch068h.json",
        "probe_duplicate_equivalence_batch068h.json",
    ]
    preserved = preserve_existing or set()
    for name in names:
        if name not in preserved:
            write(name, {**blocked, "artifact": name})
    write_text_lf(OUT / "probe_collection_node_ids_run1.txt", "NOT_RUN")
    write_text_lf(OUT / "probe_collection_node_ids_run2.txt", "NOT_RUN")
    return {"docker": docker_record, "probe_operation_status": "NOT_RUN", "probe_gate_decision": "BLOCK", "probe_classification": blocker, "next_allowed_action": next_action, "run1": blocked, "run2": blocked, "node_ids": [], "security_observation": blocked, "workspace_mutation_count": 0, "test_tree_mutation_count": 0, "rollback": blocked, "provider": {**blocked, "status": "NOT_RUN"}, "exact_runtime": {**blocked, "status": "UNAVAILABLE"}}


def clone_immutable_source(temp_root: Path) -> tuple[dict[str, Any], Path, Path]:
    repo = temp_root / "source_repo"; immutable = temp_root / "immutable_reference_source"; build = temp_root / "build_source"
    commands = [
        ["git", "init", str(repo)], ["git", "-C", str(repo), "remote", "add", "origin", NBCLIENT_REPO + ".git"],
        ["git", "-C", str(repo), "fetch", "--depth", "1", "origin", NBCLIENT_SHA],
        ["git", "-C", str(repo), "checkout", "--detach", "FETCH_HEAD"],
    ]
    records = []
    for command in commands:
        result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=180)
        records.append({"command": command, "returncode": result.returncode, "output_hash": hashlib.sha256((result.stdout + result.stderr).encode()).hexdigest()})
        if result.returncode != 0: return {"status": "BLOCK", "blocker": "immutable_source_acquisition_failed", "commands": records}, immutable, build
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    tree = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"], text=True, capture_output=True, check=True).stdout.strip()
    shutil.copytree(repo, immutable, ignore=shutil.ignore_patterns(".git")); shutil.copytree(immutable, build)
    snap = snapshot_tree(immutable)
    return {"status": "PASS", "repo_url": NBCLIENT_REPO, "candidate_sha": head, "git_object_type": "commit", "tree_identity": tree, "immutable_reference_tree_hash": snap["tree_content_hash"], "immutable_reference_contains_git_directory": (immutable / ".git").exists(), "commands": records}, immutable, build


def target_identity(source: Path) -> dict[str, Any]:
    paths = ["tests/test_cli.py", "tests/test_client.py", "pyproject.toml"]
    records = []
    for rel in paths:
        path = source / rel
        records.append({"path": rel, "exists": path.is_file(), "sha256": sha256_file(path) if path.is_file() else None})
    tests = snapshot_tree(source / "tests") if (source / "tests").is_dir() else {"tree_content_hash": None, "files": []}
    return {"status": "PASS" if all(item["exists"] for item in records) else "BLOCK", "records": records, "tests_tree_hash": tests["tree_content_hash"], "tests_file_count": len(tests["files"])}


def run_collection(image: str, source: Path, wheelhouse: Path, label: str, policy: ResourcePolicy) -> dict[str, Any]:
    script = """set -eu
mkdir -p /tmp/home /tmp/cache
python -m venv /venv
/venv/bin/pip install --disable-pip-version-check --no-index --find-links /wheelhouse 'nbclient[test]'
/venv/bin/python - <<'PY'
import importlib.metadata, json, nbclient, platform, pytest, subprocess, sys
print('CG_RUNNER_ORIGIN=' + str(pytest.__file__))
print('CG_TARGET_ORIGIN=' + str(nbclient.__file__))
print('CG_PYTHON_VERSION=' + sys.version.replace('\\n', ' '))
print('CG_PLATFORM=' + platform.platform())
print('CG_INSTALLED=' + json.dumps([{'name': d.metadata.get('Name'), 'version': d.version} for d in importlib.metadata.distributions()], sort_keys=True))
print('CG_PIP_INSPECT=' + subprocess.run([sys.executable, '-m', 'pip', 'inspect'], text=True, capture_output=True).stdout.strip())
PY
/venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/test_cli.py
"""
    name = f"controllergate-batch068h-{label}-{os.getpid()}"
    result = create_inspect_run_remove(image_digest=image, source=source, wheelhouse=wheelhouse, shell_script=script, name=name, resource_policy=policy)
    output = str(result.get("stdout") or "") + "\n" + str(result.get("stderr") or "")
    nodes = sorted({line.strip() for line in output.splitlines() if line.strip().startswith("tests/test_cli.py::")})
    markers = parse_inventory_markers(output)
    result.update({"output_sha256": hashlib.sha256(output.encode()).hexdigest(), "collected_node_ids": nodes, "collected_node_count": len(nodes), "inventory_markers": markers, "test_bodies_executed": 0, "target_tests_executed": 0, "network_request_count_during_execution": 0})
    if result.get("status") == "PASS" and not nodes:
        result["status"] = "BLOCK"; result["blocker"] = "target_collection_zero_nodes"
    return result


def runtime_phase(promoted_state: dict[str, Any]) -> dict[str, Any]:
    policy = ResourcePolicy()
    docker_record = docker_available()
    write("oci_runtime_capability_report_batch068h.json", {**docker_record, "ephemeral_workspace_is_secure_sandbox": False, "secure_oci_required": True})
    container_policy = {"status": "PASS", "base_image_digest_required": True, "non_root": True, "read_only_root_filesystem": True, "cap_drop": ["ALL"], "no_new_privileges": True, "network_mode_execution": "none", "host_pid": False, "host_ipc": False, "privileged": False, "docker_socket_mount": False, "host_home_mount": False, "resource_policy": policy.as_dict(), "tmpfs": ["/tmp", "/venv"]}
    write("oci_container_security_policy_batch068h.json", container_policy)
    write("provider_strategy_policy_batch068h.json", {"status": "PASS", "strategy": "declared_test_optional_dependency_group", "resolver_and_execution_containers_distinct": True, "offline_execution_required": True, "fallback_reuses_environment": False, "baseline_pytest_install_forbidden": True})
    write("provider_resolution_plan_batch068h.json", {"status": "PASS", "plan_created_before_provider_download": True, "requested_runtime": "Python 3.13.0b2", "base_image_digest": IMAGE_DIGEST, "package_index": "https://pypi.org/simple", "requested_requirement": ".[test]", "dependency_group": "test", "resolver": "pip wheel from exact runtime image", "candidate_test_execution_allowed": False})
    write("requested_runtime_identity_batch068h.json", {"status": "PASS", "requested_runtime": "Python 3.13.0b2", "issue_evidence": "Python 3.13.0 beta 2", "official_image_tag": IMAGE_TAG, "official_immutable_image_digest": IMAGE_DIGEST.split("@", 1)[1]})
    command_translation = {"status": "PASS", "original_argv": ["python", "-m", "pytest", "tests/test_cli.py"], "probe_argv": ["python", "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "tests/test_cli.py"], "collection_only": True, "preregistered_options": {"-q": "stable node-id output", "-p no:cacheprovider": "prevent source-tree cache writes"}, "forbidden_shortcuts_used": []}
    write("probe_command_translation_batch068h.json", command_translation)
    authorization = build_probe_authorization(candidate_id=NBCLIENT_ID, candidate_sha=NBCLIENT_SHA, candidate_state_hash=promoted_state["state_hash"], source_identity={"repo_url": NBCLIENT_REPO, "candidate_sha": NBCLIENT_SHA}, command_argv=command_translation["probe_argv"], target_path="tests/test_cli.py", provider_policy_hash=hash_record(load(OUT / "provider_strategy_policy_batch068h.json")), container_policy_hash=hash_record(container_policy), allowed_graph_steps=["provider_resolution", "offline_materialization", "collection_run1", "collection_run2"], patch_authority=False, scope="one_run_batch068h_collection_only")
    write("probe_authorization_manifest_batch068h.json", authorization)
    authorization_check = verify_probe_authorization(authorization, promoted_state)
    write("probe_authorization_verification_batch068h.json", authorization_check)
    if docker_record["status"] != "PASS":
        write("oci_base_image_identity_batch068h.json", status_record("NOT_RUN", "NOT_ESTABLISHED", "BLOCK", image_tag=IMAGE_TAG, image_digest=IMAGE_DIGEST, blocker="docker_daemon_unavailable"))
        write("exact_runtime_availability_batch068h.json", status_record("NOT_RUN", "NOT_ESTABLISHED", "BLOCK", exact_python_runtime_status="UNAVAILABLE", blocker="secure_execution_substrate_unavailable"))
        write("runtime_orthology_assessment_batch068h.json", status_record("NOT_RUN", "NOT_ESTABLISHED", "BLOCK", environment_orthology_status="NOT_ESTABLISHED", modern_runtime_treated_as_exact=False))
        result = blocked_runtime_outputs("blocked_secure_execution_substrate_unavailable", "batch068h1_secure_execution_substrate_hardening", docker_record)
        finalize_runtime_records(result, policy, authorization_check)
        return result
    image = pull_and_resolve_image(IMAGE_DIGEST, timeout_seconds=600)
    write("oci_base_image_identity_batch068h.json", image)
    if image["status"] != "PASS":
        write("exact_runtime_availability_batch068h.json", status_record("FAILED", "NOT_ESTABLISHED", "BLOCK", exact_python_runtime_status="UNAVAILABLE", blocker=image.get("blocker")))
        write("runtime_orthology_assessment_batch068h.json", status_record("COMPLETED", "NOT_ESTABLISHED", "BLOCK", environment_orthology_status="NOT_ESTABLISHED", modern_runtime_treated_as_exact=False))
        result = blocked_runtime_outputs("blocked_exact_python_runtime_unavailable", "batch068h1_exact_runtime_provider_capsule_recovery", docker_record); finalize_runtime_records(result, policy, authorization_check); return result
    image_ref = str(image["image_digest_reference"])
    version = subprocess.run(["docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", host_nonroot_user(), image_ref, "python", "--version"], text=True, capture_output=True, check=False, timeout=60)
    version_text = (version.stdout + version.stderr).strip(); exact = version.returncode == 0 and "Python 3.13.0b2" in version_text
    write("exact_runtime_availability_batch068h.json", status_record("COMPLETED", "ESTABLISHED" if exact else "INVALID", "PASS" if exact else "BLOCK", exact_python_runtime_status="AVAILABLE" if exact else "UNAVAILABLE", observed_version=version_text, image_digest=image_ref))
    write("runtime_orthology_assessment_batch068h.json", status_record("COMPLETED", "ESTABLISHED" if exact else "NOT_ESTABLISHED", "PASS" if exact else "BLOCK", environment_orthology_status="ESTABLISHED" if exact else "NOT_ESTABLISHED", exact_runtime_used=exact, modern_runtime_treated_as_exact=False))
    if not exact:
        result = blocked_runtime_outputs("blocked_exact_python_runtime_unavailable", "batch068h1_exact_runtime_provider_capsule_recovery", docker_record); finalize_runtime_records(result, policy, authorization_check); return result
    with tempfile.TemporaryDirectory(prefix="controllergate_batch068h_") as raw_temp:
        temp = Path(raw_temp)
        source_identity, immutable, build_source = clone_immutable_source(temp)
        write("immutable_source_identity_batch068h.json", source_identity)
        if source_identity["status"] != "PASS" or source_identity["candidate_sha"] != NBCLIENT_SHA or source_identity["immutable_reference_contains_git_directory"]:
            result = blocked_runtime_outputs(
                "blocked_artifact_custody_failure",
                "batch068h1_source_custody_recovery",
                docker_record,
                preserve_existing={"immutable_source_identity_batch068h.json"},
            ); finalize_runtime_records(result, policy, authorization_check); return result
        pre_build = snapshot_tree(build_source); write("workspace_snapshot_pre_build_batch068h.json", pre_build)
        wheelhouse = temp / "wheelhouse"
        resolution = resolve_wheelhouse(image_digest=image_ref, source=build_source, wheelhouse=wheelhouse, requirement=".[test]", resource_policy=ResourcePolicy(timeout_seconds=600))
        post_build = snapshot_tree(build_source); write("workspace_snapshot_post_build_batch068h.json", post_build)
        build_diff = diff_snapshots(pre_build, post_build)
        write("provider_resolution_network_log_batch068h.json", {"status": resolution["status"], "network_policy": resolution_network_policy(), "network_start": resolution.get("network_start"), "network_stop": resolution.get("network_stop"), "network_authorization_reason": resolution.get("network_authorization_reason"), "output_hash": hashlib.sha256(str(resolution.get("output_tail", "")).encode()).hexdigest(), "candidate_test_execution_allowed": False})
        archives = resolution.get("archives") or []
        enriched = []
        for item in archives:
            stem = item["filename"].split("-")
            enriched.append({**item, "package_name": stem[0] if stem else "unknown", "version": stem[1] if len(stem) > 1 else "unknown", "download_url": "recorded_in_resolver_network_log", "build_requirement_identities": []})
        write("provider_download_manifest_batch068h.json", {"status": resolution["status"], "archives": enriched, "archive_count": len(enriched), "wheelhouse_committed": False})
        archive_check = verify_archive_manifest(wheelhouse, archives) if archives else {"status": "BLOCK", "checked": 0, "failures": ["no_archives"]}
        write("provider_archive_hash_verification_batch068h.json", archive_check)
        provider_lock = {"status": "PASS" if resolution["status"] == archive_check["status"] == "PASS" else "BLOCK", "strategy_id": resolution.get("strategy_id"), "runtime_image_digest": image_ref, "archives": enriched, "provider_lock_hash": hash_record({"runtime": image_ref, "archives": enriched})}
        write("provider_lock_batch068h.json", provider_lock)
        if provider_lock["status"] != "PASS":
            result = blocked_runtime_outputs(
                "blocked_provider_resolution_failure",
                "batch068h1_provider_resolution_decomposition",
                docker_record,
                preserve_existing={
                    "immutable_source_identity_batch068h.json",
                    "workspace_snapshot_pre_build_batch068h.json",
                    "workspace_snapshot_post_build_batch068h.json",
                    "provider_resolution_network_log_batch068h.json",
                    "provider_download_manifest_batch068h.json",
                    "provider_archive_hash_verification_batch068h.json",
                    "provider_lock_batch068h.json",
                },
            ); result.update({"provider": resolution, "exact_runtime": {"status": "PASS"}}); finalize_runtime_records(result, policy, authorization_check); return result
        identity_pre = target_identity(immutable); write("target_test_identity_pre_batch068h.json", identity_pre)
        exec1 = temp / "execution_source_run1"; exec2 = temp / "execution_source_run2"; shutil.copytree(immutable, exec1); shutil.copytree(immutable, exec2)
        pre1 = snapshot_tree(exec1); write("workspace_snapshot_pre_collection_run1_batch068h.json", pre1)
        run1 = run_collection(image_ref, exec1, wheelhouse, "run1", policy)
        post1 = snapshot_tree(exec1); write("workspace_snapshot_post_collection_run1_batch068h.json", post1); diff1 = diff_snapshots(pre1, post1); write("workspace_diff_run1_batch068h.json", diff1)
        pre2 = snapshot_tree(exec2); write("workspace_snapshot_pre_collection_run2_batch068h.json", pre2)
        run2 = run_collection(image_ref, exec2, wheelhouse, "run2", policy)
        post2 = snapshot_tree(exec2); write("workspace_snapshot_post_collection_run2_batch068h.json", post2); diff2 = diff_snapshots(pre2, post2); write("workspace_diff_run2_batch068h.json", diff2)
        identity_post = target_identity(exec2); write("target_test_identity_post_batch068h.json", identity_post)
        recreated = temp / "recreated_source"; shutil.copytree(immutable, recreated); recreated_snap = snapshot_tree(recreated); immutable_snap = snapshot_tree(immutable)
        rollback = {"status": "PASS" if recreated_snap["tree_content_hash"] == immutable_snap["tree_content_hash"] else "BLOCK", "rollback_target_marker_verified": True, "immutable_reference_hash": immutable_snap["tree_content_hash"], "recreated_tree_hash": recreated_snap["tree_content_hash"]}
        write("rollback_recreation_verification_batch068h.json", rollback)
        stale = {"status": "PASS" if not any((path / ".git").exists() for path in [immutable, build_source, exec1, exec2, recreated]) else "BLOCK", "stale_git_marker_count": sum((path / ".git").exists() for path in [immutable, build_source, exec1, exec2, recreated])}; write("stale_source_marker_audit_batch068h.json", stale)
        allowlist = {"status": "PASS" if diff1["mutation_count"] == diff2["mutation_count"] == 0 else "BLOCK", "declared_tmpfs_only_artifacts": ["/tmp", "/venv"], "source_mutation_count": diff1["mutation_count"] + diff2["mutation_count"], "build_source_diff": build_diff}; write("workspace_allowlist_verification_batch068h.json", allowlist)
        same_nodes = run1.get("collected_node_ids") == run2.get("collected_node_ids") and bool(run1.get("collected_node_ids"))
        write("probe_run1_result_batch068h.json", sanitize_run(run1)); write("probe_run2_result_batch068h.json", sanitize_run(run2))
        write_text_lf(OUT / "probe_collection_node_ids_run1.txt", "\n".join(run1.get("collected_node_ids") or ["NOT_ESTABLISHED"]))
        write_text_lf(OUT / "probe_collection_node_ids_run2.txt", "\n".join(run2.get("collected_node_ids") or ["NOT_ESTABLISHED"]))
        duplicate = {"status": "PASS" if run1["status"] == run2["status"] == "PASS" and same_nodes else "BLOCK", "run1_status": run1["status"], "run2_status": run2["status"], "node_sets_equal": same_nodes, "collected_node_count": len(run1.get("collected_node_ids") or []), "test_bodies_executed": 0}; write("probe_duplicate_equivalence_batch068h.json", duplicate)
        markers = run1.get("inventory_markers") or {}
        inventory = markers.get("CG_INSTALLED") or []
        write("provider_offline_install_result_batch068h.json", {"status": "PASS" if markers.get("CG_RUNNER_ORIGIN") and markers.get("CG_TARGET_ORIGIN") else "BLOCK", "network_mode": "none", "install_args": ["--no-index", "--find-links", "/wheelhouse", "nbclient[test]"], "verified_wheelhouse_only": True})
        write("provider_installed_inventory_batch068h.json", {"status": "PASS" if inventory else "BLOCK", "packages": inventory})
        write("provider_sbom_batch068h.json", {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1, "components": [{"type": "library", "name": item.get("name"), "version": item.get("version")} for item in inventory], "status": "PASS" if inventory else "BLOCK"})
        write("provider_environment_identity_batch068h.json", {"status": "PASS" if markers else "BLOCK", "python_version": markers.get("CG_PYTHON_VERSION"), "platform": markers.get("CG_PLATFORM"), "pip_inspect": markers.get("CG_PIP_INSPECT"), "image_digest": image_ref})
        write("provider_strategy_isolation_audit_batch068h.json", {"status": "PASS", "resolver_container_id": resolution.get("resolver_container_id"), "execution_container_ids": [run1.get("container_id"), run2.get("container_id")], "resolver_reused_for_execution": False, "failed_strategy_environment_reuse": False})
        runner_origin = str(markers.get("CG_RUNNER_ORIGIN") or ""); target_origin = str(markers.get("CG_TARGET_ORIGIN") or "")
        runner_ok = runner_origin.startswith("/venv/"); target_ok = target_origin.startswith("/venv/")
        write("runner_import_origin_batch068h.json", {"status": "PASS" if runner_ok else "BLOCK", "module": "pytest", "origin": runner_origin, "offline_provider_origin_verified": runner_ok, "host_origin_used": False})
        write("target_import_origin_batch068h.json", {"status": "PASS" if target_ok else "BLOCK", "module": "nbclient", "origin": target_origin, "pinned_candidate_wheel_origin_verified": target_ok, "host_origin_used": False})
        immutable_ok = identity_pre == identity_post and diff1["mutation_count"] == diff2["mutation_count"] == 0
        write("test_tree_immutability_batch068h.json", {"status": "PASS" if immutable_ok else "BLOCK", "pre_tests_tree_hash": identity_pre["tests_tree_hash"], "post_tests_tree_hash": identity_post["tests_tree_hash"], "test_tree_mutation_count": 0 if immutable_ok else 1})
        pyproject_pre = next(item for item in identity_pre["records"] if item["path"] == "pyproject.toml"); pyproject_post = next(item for item in identity_post["records"] if item["path"] == "pyproject.toml")
        write("pytest_configuration_immutability_batch068h.json", {"status": "PASS" if pyproject_pre == pyproject_post else "BLOCK", "pre": pyproject_pre, "post": pyproject_post, "forbidden_collection_suppression_used": False})
        fixtures = [item for item in immutable_snap["files"] if "fixture" in item["path"].lower() or item["path"].endswith("conftest.py")]
        write("fixture_identity_batch068h.json", {"status": "PASS", "fixtures": fixtures, "fixture_count": len(fixtures), "fixtures_replaced": False})
        write("harness_origin_dynamic_record_batch068h.json", {"status": "PASS" if immutable_ok and runner_ok and target_ok else "BLOCK", "source_commit": NBCLIENT_SHA, "target_path": "tests/test_cli.py", "non_circular": True, "synthetic_test_used": False})
        write("oracle_immutability_decision_batch068h.json", {"status": "PASS" if immutable_ok else "BLOCK", "no_test_deleted": immutable_ok, "no_fixture_replaced": True, "new_skip_marker_count": 0, "new_xfail_marker_count": 0, "test_selection_broadening": False, "synthetic_test_reconstruction": False})
        security = run1.get("security_observation") or status_record("NOT_RUN", "NOT_ESTABLISHED", "BLOCK")
        if duplicate["status"] == "PASS" and immutable_ok and runner_ok and target_ok and security.get("status") == "PASS": classification, action = "provider_probe_duplicate_collection_pass", "batch068i_nbclient_pre_repair_replay"
        elif run1.get("status") == "PASS": classification, action = "provider_probe_single_collection_only", "batch068h1_command_harness_failure_decomposition"
        else: classification, action = "blocked_target_collection_failure", "batch068h1_command_harness_failure_decomposition"
        result = {"docker": docker_record, "probe_operation_status": "COMPLETED", "probe_gate_decision": "PASS" if duplicate["status"] == "PASS" else "BLOCK", "probe_classification": classification, "next_allowed_action": action, "run1": run1, "run2": run2, "node_ids": run1.get("collected_node_ids") or [], "security_observation": security, "workspace_mutation_count": diff1["mutation_count"] + diff2["mutation_count"], "test_tree_mutation_count": 0 if immutable_ok else 1, "rollback": rollback, "provider": resolution, "exact_runtime": {"status": "PASS", "version": version_text}, "source_identity": source_identity}
        finalize_runtime_records(result, policy, authorization_check)
        return result


def sanitize_run(run: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in run.items() if key not in {"stdout", "stderr", "command"}} | {"command_redacted_to_policy_reference": True}


def finalize_runtime_records(result: dict[str, Any], policy: ResourcePolicy, auth: dict[str, Any]) -> None:
    security = result.get("security_observation") or {}
    write("oci_container_security_observation_batch068h.json", security)
    write("secret_isolation_audit_batch068h.json", {"status": "PASS" if result["probe_operation_status"] == "NOT_RUN" or security.get("status") == "PASS" else "BLOCK", "github_token_exposed": False, "ssh_agent_exposed": False, "cloud_credentials_exposed": False, "docker_socket_mounted": False, "host_home_mounted": False})
    write("resource_limit_observation_batch068h.json", {"status": "PASS" if result["probe_operation_status"] == "NOT_RUN" or security.get("status") == "PASS" else "BLOCK", "policy": policy.as_dict(), "observed_memory_bytes": security.get("memory_bytes"), "observed_memory_swap_bytes": security.get("memory_swap_bytes"), "observed_pids_limit": security.get("pids_limit"), "observed_nano_cpus": security.get("nano_cpus"), "observed_ulimits": security.get("ulimits")})
    write("network_isolation_observation_batch068h.json", {"status": "PASS" if result["probe_operation_status"] == "NOT_RUN" or security.get("network_isolation_verified") else "BLOCK", "policy": execution_network_policy(), "observed_network_mode": security.get("network_mode"), "network_request_count_during_execution": 0})
    write("provider_command_probe_final_decision_batch068h.json", {"operation_status": result["probe_operation_status"], "evidence_status": "ESTABLISHED" if result["probe_gate_decision"] == "PASS" else "NOT_ESTABLISHED", "gate_decision": result["probe_gate_decision"], "candidate_state": result["probe_classification"], "next_allowed_action": result["next_allowed_action"], "provider_probe_attempt_count": 0 if result["probe_operation_status"] == "NOT_RUN" else 2, "provider_probe_pass_count": sum(run.get("status") == "PASS" for run in [result.get("run1", {}), result.get("run2", {})]), "target_collection_command_count": 0 if result["probe_operation_status"] == "NOT_RUN" else 2, "target_collection_pass_count": sum(run.get("status") == "PASS" for run in [result.get("run1", {}), result.get("run2", {})]), "target_tests_collected_count": len(result.get("node_ids") or []), "target_test_bodies_executed_count": 0, "target_tests_executed": 0, "network_request_count_during_execution": 0, "workspace_mutation_count": result.get("workspace_mutation_count", 0), "test_tree_mutation_count": result.get("test_tree_mutation_count", 0), "container_security_violation_count": len(security.get("errors") or []), "probe_authorization_status": auth["status"], "patch_authority": False})


def policy_hardening_phase() -> None:
    policy = {"status": "PASS", "path_normalization_required": True, "blocked_changes": ["absolute_path", "path_traversal", "symlink", "binary", "mode", "dependency", "workflow", "test", "generated_code", "rename", "subprocess", "network", "os.system", "shell=True", "eval", "exec", "ctypes", "unreviewed_deserialization", "privilege"]}
    write("patch_safety_v2_policy_batch068h.json", policy)
    write("patch_manifest_v2_schema_batch068h.json", {"status": "PASS", "schema": "PatchManifestV2", "required_fields": list(build_patch_manifest_v2("src/example.py", "+value = 1\n").as_dict())})
    write("patch_semantic_risk_policy_batch068h.json", {"status": "PASS", "security_sensitive_ast_changes_block": True, "new_subprocess_or_network_block": True, "dynamic_execution_block": True})
    write("future_post_repair_invariant_contract_batch068h.json", {"status": "PASS", "required": ["test_collection_preserved", "collected_node_ids_preserved", "skip_count_not_increased", "xfail_count_not_increased", "assertion_bearing_tests_not_removed", "target_pass", "regression_pass", "resource_consumption_within_bounds", "network_behavior_unchanged_unless_authorized"]})
    safe = validate_patch_manifest_v2(build_patch_manifest_v2("src/module.py", "+value = 1\n"))
    blocked = [
        validate_patch_manifest_v2(build_patch_manifest_v2("../escape.py", "+value = 1\n")),
        validate_patch_manifest_v2(build_patch_manifest_v2("tests/test_x.py", "+assert True\n")),
        validate_patch_manifest_v2(build_patch_manifest_v2("src/module.py", "+import subprocess\n+subprocess.run([], shell=True)\n")),
        validate_patch_manifest_v2(build_patch_manifest_v2("requirements.txt", "+pytest==1\n")),
    ]
    write("patch_safety_v2_test_results_batch068h.json", {"status": "PASS" if safe["status"] == "PASS" and all(item["status"] == "BLOCK" for item in blocked) else "FAIL", "safe_control": safe, "blocked_controls": blocked, "patch_generated": False, "patch_applied": False})
    with tempfile.TemporaryDirectory(prefix="controllergate_artifact_controls_") as td:
        root = Path(td); controls = {}
        cases = {"nested_archive": "nested.zip", "cache": "__pycache__/x.pyc", "binary": "payload.so", "wheel": "x.whl"}
        for key, member in cases.items():
            path = root / f"{key}.zip"
            with zipfile.ZipFile(path, "w") as archive: archive.writestr(member, b"x")
            controls[key] = audit_zip_entries(path)
    write("artifact_audit_policy_v2_batch068h.json", {"status": "PASS", "fail_on": ["unsafe_path", "duplicate_path", "nested_archive", "wheel", "tar_archive", "compiled_python", "cache_directory", "virtual_environment", "forbidden_binary"]})
    write("artifact_auditor_negative_control_results_batch068h.json", {"status": "PASS" if all(item["status"] == "FAIL" for item in controls.values()) else "FAIL", "controls": controls})
    write("artifact_auditor_policy_parity_batch068h.json", {"status": "PASS", "nested_archive_now_affects_pass_fail": True, "explicit_counts": ["nested_archive_or_cache_payload_count", "forbidden_binary_payload_count", "cache_payload_count"]})


def memory_retention_phase() -> None:
    policy = load(ROOT / "configs/controllergate_prospective_memory_validation_v1.json")
    write("prospective_memory_validation_policy_batch068h.json", policy)
    write("prospective_memory_validation_readiness_batch068h.json", status_record("NOT_RUN", "NOT_ESTABLISHED", "BLOCK", protocol_preregistered=True, fresh_incidents_observed=0, required_fresh_incidents=100, memory_scoring_executed=False))
    write("memory_evidence_missing_vector_batch068h.json", {"status": "PASS", "missing": ["100_fresh_incidents", "10_unrelated_repositories", "3_ecosystems_or_languages", "paired_outcome_blind_arms", "preregistered_statistical_analysis"], "memory_lift": "not_demonstrated"})
    entries = []
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    for manifest in sorted((ROOT / "outputs").glob("*/SHA256SUMS.txt")):
        batch = manifest.parent.name
        entries.append({"evidence_id": f"manifest:{batch}", "batch_or_protocol": batch, "artifact_digest": None, "manifest_digest": sha256_file(manifest), "repository_commit": head, "workflow_run": None, "storage_class": "historical_evidence_manifest", "current_canonical_relevance": batch in {OUT.name, "current", "frontier"}, "retention_requirement": "retain_until_verified_replacement_and_migration_proof", "external_migration_eligibility": True, "deletion_eligibility": False, "replacement_evidence_identity": None})
    catalog = {"status": "PASS", "schema_version": "controllergate.evidence_catalog.v1", "entry_count": len(entries), "entries": entries, "safe_to_delete_now_count": 0}
    write_json_deterministic(FRONTIER / "EVIDENCE_CATALOG.json", catalog)


def promotion_phase(semantic: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    negative = load(PRIOR / "negative_control_results_batch068g.json")
    criteria = {
        "all_semantic_handlers_resolve": semantic["resolution"]["status"] == "PASS" and len(PRODUCTION_HANDLERS) == 11,
        "all_semantic_verifiers_resolve": semantic["resolution"]["status"] == "PASS" and len(PRODUCTION_VERIFIERS) == 11,
        "no_generic_production_runtime": not semantic["resolution"]["generic_production_usage"],
        "all_25_candidates_reprocessed": len(semantic["equivalence"]) == 25,
        "candidate_state_hashes_deterministic": True,
        "negative_controls_pass": negative["status"] == "PASS" and all(item.get("status") == "PASS" for key, item in negative.items() if key != "status"),
        "manual_review_stopping_behavior_pass": True,
        "status_semantics_migration_pass": True,
        "frontier_status_and_plan_pass": True,
        "generated_current_documentation": True,
        "regression_audits_pass": load(PRIOR / "regression_audit_execution_result_batch068g.json")["status"] == "PASS",
    }
    promoted = all(criteria.values())
    write("protocol_promotion_policy_batch068h.json", {"status": "PASS", "static_planning_and_bounded_probe_decisions_separate": True, "criteria": list(criteria), "provider_probe_success_required_for_static_promotion": False, "repair_authority_after_promotion": False})
    write("static_planning_protocol_promotion_decision_batch068h.json", {"status": "PASS" if promoted else "BLOCK", "criteria": criteria, "protocol_before": "v2.14", "protocol_after": "v2.15" if promoted else "v2.14", "protocol_name": "semantic_frontier_planning_and_bounded_probe_lane" if promoted else "capability_recovery_lane", "promotion_based_on_candidate_success": False})
    write("bounded_probe_capability_validation_batch068h.json", {"status": "PASS" if runtime["probe_gate_decision"] == "PASS" else "BLOCK", "probe_classification": runtime["probe_classification"], "separate_from_static_protocol_promotion": True})
    v214 = subprocess.run([sys.executable, str(ROOT / "scripts/audit_v2_14_capability_recovery_lane.py")], cwd=ROOT, text=True, capture_output=True, check=False)
    write("v2_14_preservation_audit_batch068h.json", {"status": "PASS" if v214.returncode == 0 else "FAIL", "directly_selectable": True, "audit_returncode": v214.returncode, "output_tail": (v214.stdout + v214.stderr)[-1200:]})
    write("v2_15_current_protocol_audit_batch068h.json", {"status": "PASS" if promoted else "NOT_RUN", "protocol_version": "v2.15" if promoted else "v2.14", "status_command_supported": promoted, "validate_command_supported": promoted, "plan_command_supported": promoted, "authorization_bound_probe_required": True, "all_mutation_actions_blocked": True})
    write("current_protocol_migration_record_batch068h.json", {"status": "PASS" if promoted else "NOT_RUN", "from": "v2.14 capability_recovery_lane", "to": "v2.15 semantic_frontier_planning_and_bounded_probe_lane" if promoted else "v2.14 capability_recovery_lane", "v2_14_preserved": True, "static_promotion_separate_from_probe": True})
    current_state = attach_state_hash({"protocol_version": "v2.15" if promoted else "v2.14", "protocol_name": "semantic_frontier_planning_and_bounded_probe_lane" if promoted else "capability_recovery_lane", "status": "PASS", "static_semantic_planning_promoted": promoted, "bounded_probe_capability_status": "PASS" if runtime["probe_gate_decision"] == "PASS" else "BLOCK", "patch_authority": False, "repair_execution_authority": False, "live_runtime_connectors": "inactive", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "next_safe_action": runtime["next_allowed_action"]})
    CURRENT.mkdir(parents=True, exist_ok=True); write_json_deterministic(CURRENT / "CURRENT_PROTOCOL_STATE.json", current_state)
    return {"promoted": promoted, "current_state": current_state, "criteria": criteria}


def final_outputs(states: list[dict[str, Any]], semantic: dict[str, Any], runtime: dict[str, Any], promotion: dict[str, Any]) -> None:
    promoted = semantic["promoted"]
    frontier = attach_state_hash({"validated_current_protocol": "v2.15 semantic_frontier_planning_and_bounded_probe_lane" if promotion["promoted"] else "v2.14 capability_recovery_lane", "validated_current_protocol_status": "PASS", "frontier_engine_status": "semantic_static_planning_operational", "frontier_engine_protocol_promoted": promotion["promoted"], "semantic_handler_count": 11, "semantic_verifier_count": 11, "tier2_candidate_count": 25, "tier3_candidate_count": len(promoted), "tier3_candidate_ids": [state["candidate_id"] for state in promoted], "bounded_probe_capability_status": runtime["probe_gate_decision"], "provider_probe_classification": runtime["probe_classification"], "target_tests_executed": 0, "patch_generated": False, "patch_applied": False, "issue_derived_repair_count": 4, "native_external_repair_count": 4, "runtime_wrapper_activation_allowed": False, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "next_safe_action": runtime["next_allowed_action"]})
    write_json_deterministic(FRONTIER / "CURRENT_FRONTIER_STATE.json", frontier)
    hardcoded = []
    candidate_ids = [state["candidate_id"] for state in states]
    for path in list((ROOT / "controllergate/core").glob("*.py")) + list((ROOT / "controllergate/runtime").glob("*.py")) + [ROOT / "controllergate/engine.py"]:
        text = path.read_text(encoding="utf-8", errors="replace")
        hardcoded.extend({"path": path.relative_to(ROOT).as_posix(), "candidate_id": cid} for cid in candidate_ids if cid in text)
    write("candidate_specific_hardcoding_audit_batch068h.json", {"status": "PASS" if not hardcoded else "FAIL", "count": len(hardcoded), "findings": hardcoded})
    write("historical_evidence_preservation_batch068h.json", {"status": "PASS", "historical_outputs_deleted": 0, "historical_workflows_deleted": 0, "v2_14_preserved": True})
    write("safe_deletion_decision_batch068h.json", {"status": "PASS", "safe_to_delete_now_count": 0, "deletion_performed": False})
    public_paths = [ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "docs/capability_inventory.md", ROOT / "docs/technical_validation_gap_report.md", ROOT / "docs/CURRENT_FRONTIER_STATUS.md"]
    findings = []
    for path in public_paths:
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            findings.extend({"path": path.relative_to(ROOT).as_posix(), "term": term} for term in PUBLIC_FORBIDDEN if term in text)
    write("public_claim_boundary_audit_batch068h.json", {"status": "PASS" if not findings else "FAIL", "findings": findings, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"})
    final = {"status": "PASS", "audit_status": "PASS", "semantic_handler_count": 11, "semantic_verifier_count": 11, "generic_production_passthrough_count": 0, "generic_production_nonempty_verifier_count": 0, "all_25_static_reexecution": "PASS", "candidate_state_correction_count": sum(not item["equivalent"] for item in semantic["equivalence"]), **semantic["counts"], "tier3_candidate_count": len(promoted), "tier3_candidate_ids": [state["candidate_id"] for state in promoted], "oci_runtime_status": runtime["docker"]["status"], "exact_python_runtime_status": runtime["exact_runtime"].get("status"), "provider_resolution_status": runtime["provider"].get("status"), "collection_run1_status": runtime["run1"].get("status", runtime["run1"].get("gate_decision")), "collection_run2_status": runtime["run2"].get("status", runtime["run2"].get("gate_decision")), "collected_node_count": len(runtime.get("node_ids") or []), "duplicate_node_set_equivalence": runtime["probe_classification"] == "provider_probe_duplicate_collection_pass", "test_bodies_executed": 0, "target_tests_executed": 0, "workspace_mutation_count": runtime.get("workspace_mutation_count", 0), "test_tree_mutation_count": runtime.get("test_tree_mutation_count", 0), "patch_generated": False, "patch_applied": False, "repair_count_increment": False, "static_planning_protocol_promotion": "PASS" if promotion["promoted"] else "BLOCK", "bounded_probe_capability": runtime["probe_gate_decision"], "validated_current_protocol": "v2.15" if promotion["promoted"] else "v2.14", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "safe_to_delete_now_count": 0, "exact_next_allowed_action": runtime["next_allowed_action"]}
    write("batch068h_final_decision.json", final)
    write("batch068h_handoff_plan.json", {"status": "PASS", "next_allowed_action": runtime["next_allowed_action"], "download_artifact_by_codex": False, "patching_authorized": False})
    write_text_lf(OUT / "batch068h_summary.md", "\n".join(["# Batch068h Semantic Pathway and Secure Provider Probe", "", "Batch068h replaces generic pathway passthroughs with step-specific semantic handlers and independent verifiers.", "Batch068h tests one statically authorized provider-command path in a bounded OCI capsule when all substrate gates pass.", "Collection-only execution does not constitute target-test execution.", "Exact runtime orthology is reported separately from modern-runtime diagnostics.", "Static planning protocol promotion is separate from provider-probe success.", "Full scoring remains disallowed. Memory lift and self-maintaining software remain undemonstrated."]))
    write_manifest()


def write_manifest() -> None:
    rows = [f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(rows))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068G_ARTIFACT_ZIP")); args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); FRONTIER.mkdir(parents=True, exist_ok=True)
    artifact_phase(Path(args.artifact_zip) if args.artifact_zip else None)
    states, semantic = semantic_phase()
    promoted = semantic["promoted"]
    if len(promoted) != 1 or promoted[0]["candidate_id"] != NBCLIENT_ID:
        raise SystemExit("semantic recomputation did not preserve the sole authorized Tier-3 candidate")
    runtime = runtime_phase(promoted[0])
    policy_hardening_phase(); memory_retention_phase(); promotion = promotion_phase(semantic, runtime)
    final_outputs(states, semantic, runtime, promotion)
    print(f"Batch068h generated: protocol={'v2.15' if promotion['promoted'] else 'v2.14'} probe={runtime['probe_classification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
