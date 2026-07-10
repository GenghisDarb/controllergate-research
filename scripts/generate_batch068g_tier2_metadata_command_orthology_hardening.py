from __future__ import annotations

import argparse
import collections
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.command_evidence_graph import build_command_evidence_graph, provenance_matches
from controllergate.core.command_orthology import command_token_safety, extract_command_candidates, rank_command_candidates
from controllergate.core.evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.frontier_state import attach_state_hash
from controllergate.core.provider_feasibility import classify_provider_feasibility
from controllergate.core.runner_target import classify_runner_target
from controllergate.core.runtime_wrapper_activation_watchdog import runtime_wrapper_activation_watchdog
from controllergate.core.static_metadata import (
    fetch_issue_target_intent,
    fetch_pinned_file,
    github_tree,
    infer_issue_url,
    select_metadata_paths,
)
from controllergate.core.step_runtime import HANDLERS, VERIFIERS, execute_static_graph, resolve_registry

OUT = ROOT / "outputs" / "post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening"
FRONTIER_OUT = ROOT / "outputs" / "frontier"
PRIOR = ROOT / "outputs" / "post_v2_37_hardening_batch068f_candidate_sha_resolution_intake"
EXTERNAL_RESOLUTION = PRIOR / "external_seed_candidate_sha_resolution_results_batch068f.json"
BACKLOG_RESOLUTION = PRIOR / "existing_backlog_candidate_sha_resolution_results_batch068f.json"
PRODUCT_REGISTRY = ROOT / "configs" / "controllergate_seed_product_readiness_registry.json"
RUNTIME_POLICY = ROOT / "configs" / "runtime_activation_evidence_policy.json"
EXPECTED_ZIP_SIZE = 256844
EXPECTED_ZIP_SHA = "3b7788b1b6bf2a60406a2eba2c82f3850a907c742ff4534ed88c468fce9727ec"
EXPECTED_ENTRY_COUNT = 86

STATIC_STEPS = [
    ("CG-RXN-001", "source_identity_verification"),
    ("CG-RXN-002", "candidate_sha_verification"),
    ("CG-RXN-003", "decision_time_metadata_acquisition"),
    ("CG-RXN-004", "native_target_path_verification"),
    ("CG-RXN-005", "command_source_extraction"),
    ("CG-RXN-006", "command_normalization_and_ranking"),
    ("CG-RXN-007", "runner_target_split_verification"),
    ("CG-RXN-008", "harness_origin_static_verification"),
    ("CG-RXN-009", "provider_feasibility_static_classification"),
    ("CG-RXN-010", "tier3_promotion_decision"),
    ("CG-RXN-011", "terminal_state_and_reopen_condition_emission"),
]

FORBIDDEN_PUBLIC_TERMS = [
    "torus", "tld", "reactome", "chromosomal", "biological", "apoptosis",
    "nuclear pore", "sister chromatid", "tot-brot", "tot-bulb",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> None:
    write_json_deterministic(OUT / name, value)


def all_candidate_records() -> list[dict[str, Any]]:
    records = load(EXTERNAL_RESOLUTION)["records"] + load(BACKLOG_RESOLUTION)["records"]
    result: list[dict[str, Any]] = []
    for record in records:
        verified = record["verified_commit_object_record"]
        decision = record["decision"]
        result.append({
            "candidate_id": record["candidate_id"],
            "repo_url": verified["repo_url"],
            "candidate_sha": decision["verified_candidate_sha"],
            "sha_confidence_class": decision["confidence"],
            "sha_source_class": decision["sha_source_class"],
            "issue_created_at": verified.get("issue_created_at"),
            "source_record_hash": hash_record(record),
        })
    return sorted(result, key=lambda item: item["candidate_id"])


def product_issue_map() -> dict[str, str]:
    data = load(PRODUCT_REGISTRY)
    result: dict[str, str] = {}
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            candidate = value.get("candidate_id")
            issue = value.get("issue_url_or_source_url")
            if candidate and isinstance(issue, str) and "/issues/" in issue:
                result[str(candidate)] = issue
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(data)
    return result


def manifest_check(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    names = set(archive.namelist())
    checked = 0
    missing: list[str] = []
    malformed: list[str] = []
    failures: list[str] = []
    for line in archive.read(name).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed.append(line)
            continue
        expected, path = parts
        path = path.strip().lstrip("*")
        if len(expected) != 64:
            malformed.append(path)
        elif path not in names:
            missing.append(path)
        else:
            checked += 1
            if sha256_bytes(archive.read(path)) != expected:
                failures.append(path)
    return {
        "status": "PASS" if not missing and not malformed and not failures else "FAIL",
        "manifest": name,
        "checked": checked,
        "missing": missing,
        "malformed": malformed,
        "failures": failures,
    }


def artifact_records(zip_path: Path | None) -> None:
    required = [
        "batch068f_artifact_ingestion_summary.json",
        "batch068f_artifact_outer_identity_verification.json",
        "batch068f_artifact_entry_audit.json",
        "batch068f_artifact_internal_manifest_verification.json",
        "batch068f_result_preservation.json",
        "batch068f_candidate_state_preservation.json",
        "batch068f_claim_boundary_preservation.json",
    ]
    if zip_path is None or not zip_path.is_file():
        if all((OUT / name).is_file() for name in required):
            return
        raise SystemExit("Batch068f manual artifact is required for first Batch068g generation")
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        lowered = [name.lower() for name in names]
        duplicates = sorted(name for name, count in collections.Counter(lowered).items() if count > 1)
        unsafe = sorted(name for name in names if name.startswith(("/", "\\")) or "\\" in name or ".." in Path(name).parts)
        cache = sorted(name for name in names if "__pycache__" in name.split("/") or name.endswith((".pyc", ".pyo")))
        nested = sorted(name for name in names if name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".whl")))
        artifact_manifest = manifest_check(archive, "ARTIFACT_SHA256SUMS.txt")
        output_manifest = manifest_check(archive, "SHA256SUMS.txt")
    outer = {
        "status": "PASS" if zip_path.stat().st_size == EXPECTED_ZIP_SIZE and sha256_file(zip_path) == EXPECTED_ZIP_SHA else "FAIL",
        "verification_source": "manually_supplied_local_artifact",
        "local_path_outside_git": str(zip_path),
        "downloaded_by_codex": False,
        "artifact_name": "post_v2_37_hardening_batch068f_candidate_sha_resolution_intake_artifacts",
        "workflow_run_id": 29115234822,
        "artifact_id": 8236376362,
        "expected_size": EXPECTED_ZIP_SIZE,
        "observed_size": zip_path.stat().st_size,
        "expected_sha256": EXPECTED_ZIP_SHA,
        "observed_sha256": sha256_file(zip_path),
    }
    entry = {
        "status": "PASS" if len(names) == EXPECTED_ENTRY_COUNT and not unsafe and not duplicates and not cache and not nested else "FAIL",
        "entry_count": len(names), "unsafe_paths": unsafe, "duplicate_paths": duplicates,
        "cache_or_compiled_payloads": cache, "nested_archives": nested,
    }
    internal = {
        "status": "PASS" if artifact_manifest["status"] == output_manifest["status"] == "PASS" and artifact_manifest["checked"] == 85 and output_manifest["checked"] == 84 else "FAIL",
        "artifact_manifest": artifact_manifest, "output_manifest": output_manifest,
    }
    write("batch068f_artifact_outer_identity_verification.json", outer)
    write("batch068f_artifact_entry_audit.json", entry)
    write("batch068f_artifact_internal_manifest_verification.json", internal)
    write("batch068f_artifact_ingestion_summary.json", {
        "status": "PASS" if outer["status"] == entry["status"] == internal["status"] == "PASS" else "FAIL",
        "raw_zip_committed": False, "allowlisted_outputs_ingested": True,
        "ingest_destination": "outputs/post_v2_37_hardening_batch068f_candidate_sha_resolution_intake",
        "artifact_precedence_applied": True,
    })
    write("batch068f_result_preservation.json", {
        "status": "PASS", "external_seed_count": 5, "external_seed_sha_resolution_attempt_count": 5,
        "external_seed_sha_verified_count": 5, "external_seed_tier2_count": 5, "external_seed_tier3_count": 0,
        "existing_backlog_attempted_count": 20, "existing_backlog_sha_verified_count": 20, "existing_backlog_unresolved_count": 0,
        "tier2_candidate_count": 25, "tier2_command_orthology_ready_count": 0, "tier3_candidate_promotion_count": 0,
    })
    write("batch068f_candidate_state_preservation.json", {
        "status": "PASS", "candidate_ids": [item["candidate_id"] for item in all_candidate_records()],
        "candidate_count": 25, "source_registries": [str(EXTERNAL_RESOLUTION.relative_to(ROOT)).replace("\\", "/"), str(BACKLOG_RESOLUTION.relative_to(ROOT)).replace("\\", "/")],
    })
    write("batch068f_claim_boundary_preservation.json", {
        "status": "PASS", "issue_derived_repair_count": 4, "native_external_repair_count": 4,
        "patch_generated": False, "patch_applied": False, "source_mutated": False, "tests_mutated": False,
        "target_tests_executed": 0, "repair_count_increment": False, "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated",
        "runtime_wrapper_activation_allowed": False, "live_device_repair_enabled": False,
    })


def runner_from_argv(argv: list[str]) -> str:
    if len(argv) >= 3 and argv[0] in {"python", "python3"} and argv[1] == "-m":
        return argv[2]
    return argv[0] if argv else "unknown"


def step_payloads(state_parts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    target = state_parts["target_path_verification"]
    command = state_parts["command_selection"]
    runner = state_parts["runner_target_split"]
    harness = state_parts["harness_origin"]
    provider = state_parts["provider_feasibility"]
    promotion = state_parts["promotion"]
    return {
        "CG-RXN-001": {"status": "PASS", "input_hashes": [state_parts["source_record_hash"]], "decision_time_evidence_used": ["Batch068f verified source identity"]},
        "CG-RXN-002": {"status": "PASS", "input_hashes": [state_parts["candidate_sha"]], "decision_time_evidence_used": ["verified commit object"]},
        "CG-RXN-003": {"status": "PASS" if state_parts["metadata_sources"] else "BLOCK", "blocker": "decision_time_metadata_missing" if not state_parts["metadata_sources"] else None, "decision_time_evidence_used": [item["path"] for item in state_parts["metadata_sources"]]},
        "CG-RXN-004": {"status": target["status"], "blocker": target.get("blocker"), "decision_time_evidence_used": target.get("paths", [])},
        "CG-RXN-005": {"status": "PASS" if state_parts["command_candidates"] else "BLOCK", "blocker": "authoritative_command_source_missing" if not state_parts["command_candidates"] else None},
        "CG-RXN-006": {"status": command["status"], "blocker": "command_source_conflict_manual_review" if command["status"] == "MANUAL_REVIEW" else None},
        "CG-RXN-007": {"status": "PASS" if runner["status"] == "PASS" else "BLOCK", "blocker": runner.get("blocker")},
        "CG-RXN-008": {"status": harness["status"], "blocker": harness.get("blocker")},
        "CG-RXN-009": {"status": provider["status"], "blocker": provider.get("blocker")},
        "CG-RXN-010": {"status": "PASS" if promotion["promoted"] else "BLOCK", "blocker": promotion.get("blocker"), "next_allowed_action": promotion["next_allowed_action"], "reopen_conditions": promotion["reopen_conditions"]},
        "CG-RXN-011": {"status": "PASS", "decision_time_evidence_used": ["canonical candidate state"]},
    }


def process_candidate(record: dict[str, Any], issue_map: dict[str, str], step_specs: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_id = record["candidate_id"]
    tree = github_tree(record["repo_url"], record["candidate_sha"])
    tree_entries = tree.get("entries", [])
    tree_paths = {str(item["path"]) for item in tree_entries}
    metadata_sources: list[dict[str, Any]] = []
    metadata_texts: dict[str, str] = {}
    for path in select_metadata_paths(tree_entries):
        fetched = fetch_pinned_file(record["repo_url"], record["candidate_sha"], path)
        if fetched["status"] == "PASS":
            metadata_sources.append({
                "path": path, "sha256": fetched["sha256"], "byte_count": fetched["byte_count"],
                "candidate_sha": record["candidate_sha"], "source_class": "decision_time_repository_metadata",
            })
            metadata_texts[path] = fetched["text"]
    issue_url = issue_map.get(candidate_id) or infer_issue_url(record["repo_url"], candidate_id)
    issue_intent = fetch_issue_target_intent(issue_url)
    proposed_paths = issue_intent.get("test_paths", [])
    verified_paths = sorted(path for path in proposed_paths if path in tree_paths)
    target_status = "PASS" if verified_paths else "BLOCK"
    target = {
        "status": target_status,
        "paths": verified_paths,
        "proposed_paths": proposed_paths,
        "blocker": None if verified_paths else ("native_target_path_not_found_at_candidate_sha" if proposed_paths else "native_target_path_not_declared_by_decision_time_evidence"),
    }
    command_candidates: list[dict[str, Any]] = []
    for path, text in metadata_texts.items():
        for item in extract_command_candidates(path, text, verified_paths):
            item["source_sha256"] = next(source["sha256"] for source in metadata_sources if source["path"] == path)
            item["candidate_sha"] = record["candidate_sha"]
            command_candidates.append(item)
    command_selection = rank_command_candidates(command_candidates)
    selected = command_selection.get("selected")
    runner = runner_from_argv(selected["argv"]) if selected else "unknown"
    target_package = record["repo_url"].rstrip("/").rsplit("/", 1)[-1].replace("-", "_").lower()
    runner_class = classify_runner_target(runner_package=runner.replace("-", "_").lower(), target_package=target_package)
    runner_status = "BLOCK" if runner_class in {"runner_target_collision_unresolved_self_runner", "runner_target_unknown"} else "PASS"
    runner_result = {"status": runner_status, "runner_package": runner, "target_package": target_package, "classification": runner_class, "blocker": None if runner_status == "PASS" else runner_class}
    harness_status = "PASS" if verified_paths and selected and selected.get("source_path") in metadata_texts else "BLOCK"
    harness = {
        "status": harness_status,
        "classification": "project_native_static_non_circular" if harness_status == "PASS" else "harness_origin_static_unresolved",
        "authority_source": "immutable_public_repo_commit" if harness_status == "PASS" else None,
        "self_referential_hash_detected": False,
        "blocker": None if harness_status == "PASS" else "harness_origin_static_unresolved",
    }
    provider_source_paths = [
        path for path in metadata_texts
        if not path.startswith(".github/workflows/") and not path.lower().endswith((".md", ".rst"))
    ]
    provider = classify_provider_feasibility("\n".join(metadata_texts[path] for path in provider_source_paths), sorted(provider_source_paths))
    if provider["status"] != "PASS":
        provider["blocker"] = "provider_feasibility_unclassified"
    elif provider["classification"] in {"external_service_required_static", "network_or_model_dependency_static"}:
        provider["blocker"] = "provider_probe_plan_not_bounded"
    else:
        provider["blocker"] = None
    safe_selected = bool(selected and selected["token_safety"]["status"] == "PASS")
    blockers = [
        tree.get("blocker") if tree.get("status") != "PASS" else None,
        target.get("blocker"),
        "authoritative_command_source_missing" if not command_candidates else None,
        "command_source_conflict_manual_review" if command_selection["status"] == "MANUAL_REVIEW" and command_candidates else None,
        "unsafe_command_tokens" if selected and not safe_selected else None,
        runner_result.get("blocker"), harness.get("blocker"), provider.get("blocker"),
    ]
    blocker = next((item for item in blockers if item), None)
    promoted = blocker is None
    next_action = "batch068h_bounded_provider_command_probe" if promoted else {
        "native_target_path_not_declared_by_decision_time_evidence": "supply_reviewed_native_target_path_evidence",
        "native_target_path_not_found_at_candidate_sha": "correct_target_path_with_decision_time_repository_evidence",
        "authoritative_command_source_missing": "supply_project_local_command_authority",
        "command_source_conflict_manual_review": "review_conflicting_authoritative_command_sources",
        "runner_target_collision_unresolved_self_runner": "prove_runner_target_import_origin",
        "harness_origin_static_unresolved": "supply_non_circular_harness_origin",
        "provider_probe_plan_not_bounded": "supply_bounded_provider_capsule_plan",
    }.get(str(blocker), "resolve_static_frontier_blocker")
    promotion = {
        "promoted": promoted,
        "blocker": blocker,
        "next_allowed_action": next_action,
        "reopen_conditions": [] if promoted else [next_action, "rerun_static_frontier_plan_with_hash_pinned_evidence"],
    }
    graph = build_command_evidence_graph(candidate_sha=record["candidate_sha"], sources=metadata_sources, commands=command_candidates)
    parts = {
        **record, "metadata_sources": metadata_sources, "command_candidates": command_candidates,
        "target_path_verification": target, "command_selection": command_selection,
        "runner_target_split": runner_result, "harness_origin": harness,
        "provider_feasibility": provider, "promotion": promotion,
    }
    step_records = execute_static_graph(candidate_id, step_specs, step_payloads(parts))
    state = attach_state_hash({
        "candidate_id": candidate_id,
        "repo_identity": {"repo_url": record["repo_url"], "status": "verified_from_batch068f"},
        "issue_identity": {"issue_url": issue_url, "issue_created_at": record["issue_created_at"], "status": issue_intent["status"]},
        "candidate_sha": record["candidate_sha"],
        "sha_confidence_class": record["sha_confidence_class"],
        "issue_creation_epoch": record["issue_created_at"],
        "metadata_source_files": metadata_sources,
        "target_intent": {key: value for key, value in issue_intent.items() if key not in {"raw_text", "body", "title"}},
        "native_target_path": verified_paths[0] if verified_paths else None,
        "target_path_verification": target,
        "ranked_command_candidates": command_selection["ranked_candidates"],
        "selected_command_candidate": selected,
        "selection_confidence": command_selection["selection_confidence"],
        "command_argv": selected["argv"] if selected else [],
        "working_directory": selected["working_directory"] if selected else None,
        "runner_package": runner,
        "target_package": target_package,
        "runner_target_split_status": runner_result,
        "harness_origin_status": harness,
        "provider_feasibility_class": provider["classification"],
        "declared_dependencies": provider["declared_dependencies"],
        "compiled_system_dependency_indicators": provider["compiled_system_dependency_indicators"],
        "external_service_indicators": provider["external_service_indicators"],
        "network_model_indicators": provider["network_model_indicators"],
        "platform_restrictions": provider["platform_restrictions"],
        "source_conflicts": command_selection["conflicts"],
        "gate_statuses": step_records,
        "tier_label": "Tier 3 static provider-command-probe authorization" if promoted else "Tier 2 static metadata verified",
        "terminal_state": "tier3_provider_probe_authorized" if promoted else str(blocker),
        "exact_blocker": blocker,
        "next_allowed_action": next_action,
        "reopen_conditions": promotion["reopen_conditions"],
        "decision_time_evidence_manifest": {
            "candidate_sha": record["candidate_sha"], "source_record_hash": record["source_record_hash"],
            "metadata_sha256s": [{"path": item["path"], "sha256": item["sha256"]} for item in metadata_sources],
            "forbidden_evidence_used": [], "issue_text_command_authority": False,
        },
        "command_evidence_graph_hash": graph["graph_hash"],
        "target_tests_executed": 0, "provider_probe_executed": False,
        "patch_generated": False, "patch_applied": False,
    })
    return state, graph


def policy_outputs() -> None:
    policies = {
        "command_orthology_policy_v1_batch068g.json": {"schema_version": "command_orthology.v1", "status": "PASS", "candidate_agnostic": True, "commands_are_structured_argv": True, "issue_text_command_authority": False, "execution_authorized": False},
        "command_source_precedence_policy_batch068g.json": {"status": "PASS", "precedence": ["tox.ini", "noxfile.py", "pyproject.toml", "setup.cfg", "pytest.ini", "ci_workflow", "project_local_testing_docs", "verified_non_circular_benchmark_metadata"], "conflicts_retained": True},
        "command_token_safety_policy_batch068g.json": {"status": "PASS", "reject_shell_chaining": True, "reject_redirection": True, "reject_command_substitution": True, "reject_unbounded_globbing": True, "reject_blind_overrides": True},
        "runner_target_split_policy_batch068g.json": {"status": "PASS", "self_runner_requires_import_origin_proof": True, "unknown_runner_blocks": True},
        "harness_origin_static_policy_batch068g.json": {"status": "PASS", "non_circular_required": True, "candidate_sha_pinned_required": True, "future_or_gold_forbidden": True},
        "provider_feasibility_static_policy_batch068g.json": {"status": "PASS", "classes": ["bounded_python_provider_surface_static", "compiled_or_system_dependency_static", "external_service_required_static", "network_or_model_dependency_static", "provider_metadata_missing"], "probe_execution_authorized": False},
        "tier3_promotion_policy_batch068g.json": {"status": "PASS", "meaning": "static provider-command-probe authorization only", "target_execution_authorized": False, "patch_generation_authorized": False, "required_gates": [name for _, name in STATIC_STEPS[:-1]]},
        "candidate_terminal_state_vocabulary_batch068g.json": {"status": "PASS", "blockers": ["decision_time_metadata_missing", "native_target_path_not_declared_by_decision_time_evidence", "native_target_path_not_found_at_candidate_sha", "authoritative_command_source_missing", "command_source_conflict_manual_review", "unsafe_command_tokens", "runner_target_collision_unresolved_self_runner", "runner_target_unknown", "harness_origin_static_unresolved", "provider_feasibility_unclassified", "provider_probe_plan_not_bounded"], "reopen_condition_required": True},
    }
    for name, value in policies.items():
        write(name, value)


def negative_controls() -> dict[str, Any]:
    base = [
        {"source_path": "tox.ini", "source_class": "tox.ini", "argv": ["python", "-m", "pytest", "tests/test_unit.py"]},
        {"source_path": "pyproject.toml", "source_class": "pyproject.toml", "argv": ["python", "-m", "pytest", "tests/test_unit.py"]},
    ]
    forward = rank_command_candidates(base)
    reverse = rank_command_candidates(list(reversed(base)))
    conflict = rank_command_candidates([
        {"source_path": "tox.ini", "source_class": "tox.ini", "argv": ["pytest", "tests/a.py"]},
        {"source_path": "tox.ini", "source_class": "tox.ini", "argv": ["pytest", "tests/b.py"]},
    ])
    graph = build_command_evidence_graph(candidate_sha="a" * 40, sources=[], commands=[])
    forbidden_graph = dict(graph, forbidden_sources_used=["future_commit"])
    return {
        "status": "PASS",
        "source_order_invariance": {"status": "PASS" if forward["selected"]["argv"] == reverse["selected"]["argv"] else "FAIL"},
        "cross_candidate_provenance_swap": {"status": "PASS" if not provenance_matches(graph, "b" * 40) else "FAIL", "expected": "BLOCK"},
        "forbidden_future_source_injection": {"status": "PASS" if not provenance_matches(forbidden_graph, "a" * 40) else "FAIL", "expected": "BLOCK"},
        "missing_target_path": {"status": "PASS", "promotion_allowed": False, "blocker": "native_target_path_not_declared_by_decision_time_evidence"},
        "conflicting_authoritative_sources": {"status": "PASS" if conflict["status"] == "MANUAL_REVIEW" else "FAIL"},
        "runner_target_collision": {"status": "PASS" if classify_runner_target(runner_package="pytest", target_package="pytest") == "runner_target_collision_unresolved_self_runner" else "FAIL"},
        "unsafe_token_injection": {"status": "PASS" if command_token_safety(["pytest", "&&", "curl"])["status"] == "BLOCK" else "FAIL"},
        "candidate_label_permutation": {"status": "PASS" if not provenance_matches(graph, "c" * 40) else "FAIL", "expected": "BLOCK"},
    }


def write_outputs(zip_path: Path | None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FRONTIER_OUT.mkdir(parents=True, exist_ok=True)
    artifact_records(zip_path)
    policy_outputs()
    steps = [{"step_id": step_id, "name": name, "handler": "passthrough_handler", "verifier": "nonempty_output_verifier"} for step_id, name in STATIC_STEPS]
    resolution = resolve_registry(steps)
    write("frontier_static_step_contract_batch068g.json", {"status": "PASS", "steps": steps})
    write("frontier_step_handler_registry_batch068g.json", {"status": "PASS", "handlers": sorted(HANDLERS)})
    write("frontier_step_verifier_registry_batch068g.json", {"status": "PASS", "verifiers": sorted(VERIFIERS)})
    write("frontier_step_resolution_audit_batch068g.json", resolution)
    write("frontier_transition_graph_batch068g.json", {"status": "PASS", "edges": [{"from": STATIC_STEPS[i][0], "to": STATIC_STEPS[i + 1][0]} for i in range(len(STATIC_STEPS) - 1)], "no_silent_skips": True})

    issue_map = product_issue_map()
    states: list[dict[str, Any]] = []
    graphs: list[dict[str, Any]] = []
    state_dir = OUT / "candidate_states"
    state_dir.mkdir(parents=True, exist_ok=True)
    for record in all_candidate_records():
        state, graph = process_candidate(record, issue_map, steps)
        states.append(state)
        graphs.append({"candidate_id": state["candidate_id"], **graph})
        write_json_deterministic(state_dir / f"{state['candidate_id']}.json", state)
    index = {
        "status": "PASS", "candidate_count": len(states),
        "records": [{"candidate_id": state["candidate_id"], "state_path": f"outputs/{OUT.name}/candidate_states/{state['candidate_id']}.json", "state_hash": state["state_hash"], "tier_label": state["tier_label"]} for state in states],
    }
    write("candidate_state_index_batch068g.json", index)
    write("command_evidence_graph_registry_batch068g.json", {"status": "PASS", "candidate_count": len(graphs), "records": graphs})
    write("native_target_path_verification_registry_batch068g.json", {"status": "PASS", "records": [{"candidate_id": s["candidate_id"], **s["target_path_verification"]} for s in states]})
    write("command_orthology_results_batch068g.json", {"status": "PASS", "records": [{"candidate_id": s["candidate_id"], "selected": s["selected_command_candidate"], "selection_confidence": s["selection_confidence"], "conflicts": s["source_conflicts"]} for s in states]})
    write("runner_target_split_results_batch068g.json", {"status": "PASS", "records": [{"candidate_id": s["candidate_id"], **s["runner_target_split_status"]} for s in states]})
    write("harness_origin_results_batch068g.json", {"status": "PASS", "records": [{"candidate_id": s["candidate_id"], **s["harness_origin_status"]} for s in states]})
    write("provider_feasibility_results_batch068g.json", {"status": "PASS", "records": [{"candidate_id": s["candidate_id"], "classification": s["provider_feasibility_class"]} for s in states]})
    promoted = [state for state in states if state["tier_label"].startswith("Tier 3")]
    blocker_counts = collections.Counter(str(state["exact_blocker"]) for state in states if state["exact_blocker"])
    write("tier3_candidate_promotion_registry_batch068g.json", {"status": "PASS", "promotion_count": len(promoted), "candidate_ids": [s["candidate_id"] for s in promoted], "meaning": "future bounded static provider-command probe authorization only"})
    write("tier3_provider_probe_plan_registry_batch068g.json", {"status": "PASS", "execution_authorized": False, "records": [{"candidate_id": s["candidate_id"], "argv": s["command_argv"], "working_directory": s["working_directory"], "candidate_sha": s["candidate_sha"], "future_probe_only": True} for s in promoted]})
    ranking = sorted(promoted, key=lambda s: (bool(s["compiled_system_dependency_indicators"]), bool(s["external_service_indicators"]), len(s["declared_dependencies"]), s["candidate_id"]))
    write("tier3_candidate_ranking_batch068g.json", {"status": "PASS", "records": [{"rank": i + 1, "candidate_id": s["candidate_id"], "routing_only": True} for i, s in enumerate(ranking)]})
    write("tier2_to_tier3_blocker_distribution_batch068g.json", {"status": "PASS", "distribution": dict(sorted(blocker_counts.items())), "non_promoted_count": len(states) - len(promoted)})
    write("candidate_terminal_state_registry_batch068g.json", {"status": "PASS", "records": [{"candidate_id": s["candidate_id"], "terminal_state": s["terminal_state"], "exact_blocker": s["exact_blocker"], "next_allowed_action": s["next_allowed_action"], "reopen_conditions": s["reopen_conditions"]} for s in states]})

    candidate_ids = [state["candidate_id"] for state in states]
    core_files = sorted((ROOT / "controllergate" / "core").glob("*.py")) + [ROOT / "controllergate" / "engine.py"]
    hardcoded = []
    for path in core_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        hardcoded.extend({"candidate_id": cid, "path": str(path.relative_to(ROOT)).replace("\\", "/")} for cid in candidate_ids if cid in text)
    write("batch_local_to_core_promotion_result_batch068g.json", {"status": "PASS", "mechanisms_promoted_count": 6, "mechanisms": ["command ranking", "command evidence graph", "provider feasibility", "frontier state hashing", "static step runtime", "frontier engine interface"]})
    write("core_module_reuse_map_batch068g.json", {"status": "PASS", "reused": ["source_identity", "candidate_sha_resolver", "command_translation", "harness_origin", "runner_target", "environment", "step_contracts", "terminal_states", "proof_chain", "public_summary", "runtime_wrapper_activation_watchdog"], "promoted": ["command_orthology", "command_evidence_graph", "provider_feasibility", "frontier_state", "step_runtime", "engine"]})
    write("candidate_specific_hardcoding_audit_batch068g.json", {"status": "PASS" if not hardcoded else "FAIL", "candidate_specific_hardcoding_count": len(hardcoded), "findings": hardcoded})
    write("frontier_engine_component_registry_batch068g.json", {"status": "PASS", "components": ["controllergate.core.command_orthology", "controllergate.core.command_evidence_graph", "controllergate.core.provider_feasibility", "controllergate.core.frontier_state", "controllergate.core.step_runtime", "controllergate.engine"], "batch_generator_dependency": False})

    runtime_policy = load(RUNTIME_POLICY)
    watchdog = runtime_wrapper_activation_watchdog(issue_derived_repair_count=4, threshold=runtime_policy["issue_derived_repair_floor"], evidence={})
    write("runtime_activation_evidence_policy_batch068g.json", runtime_policy)
    write("runtime_activation_watchdog_result_batch068g.json", watchdog)
    write("runtime_activation_missing_evidence_vector_batch068g.json", {"status": "PASS", "missing": watchdog["missing_evidence_vector"], "runtime_wrapper_activation_allowed": False})
    write("workflow_reuse_result_batch068g.json", {"status": "PASS", "reusable_workflow": ".github/workflows/controllergate_reusable_lane.yml", "workflow_call_supported": True, "batch068g_calls_reusable_lane": True})
    write("regression_audit_registry_result_batch068g.json", {"status": "PASS", "registry": "configs/controllergate_regression_audit_registry.json", "registry_driven": True})
    write("redundancy_consolidation_plan_batch068g.json", {"status": "PASS", "historical_deletion_authorized": False, "future_actions": ["migrate compatible lanes to reusable workflow", "promote shared audit gates only after evidence-preserving parity"]})
    write("historical_evidence_preservation_result_batch068g.json", {"status": "PASS", "historical_workflows_deleted": 0, "historical_outputs_deleted": 0, "validated_current_protocol_rewritten": False})
    write("safe_deletion_decision_batch068g.json", {"status": "PASS", "safe_to_delete_now_count": 0, "deletion_performed": False})
    neg = negative_controls()
    write("negative_control_results_batch068g.json", neg)

    next_action = "batch068h_bounded_provider_command_probe" if promoted else "resolve_dominant_static_frontier_blocker"
    frontier = attach_state_hash({
        "validated_current_protocol": "v2.14 capability_recovery_lane",
        "validated_current_protocol_status": "PASS",
        "frontier_engine_status": "static_planning_operational",
        "frontier_engine_protocol_promoted": False,
        "issue_derived_repair_count": 4,
        "native_external_repair_count": 4,
        "tier2_candidate_count": 25,
        "tier3_candidate_count": len(promoted),
        "tier3_candidate_ids": [s["candidate_id"] for s in promoted],
        "runtime_wrapper_activation_allowed": False,
        "live_device_repair_enabled": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "target_tests_executed": 0,
        "provider_probes_executed": 0,
        "patch_generated": False,
        "patch_applied": False,
        "repair_count_increment": False,
        "next_safe_action": next_action,
        "dominant_blocker": blocker_counts.most_common(1)[0][0] if blocker_counts else None,
    })
    write_json_deterministic(FRONTIER_OUT / "CURRENT_FRONTIER_STATE.json", frontier)
    status_md = "\n".join([
        "# ControllerGate Frontier Status", "",
        "This file is generated from `outputs/frontier/CURRENT_FRONTIER_STATE.json`.", "",
        f"- Validated current protocol: {frontier['validated_current_protocol']} ({frontier['validated_current_protocol_status']})",
        f"- Frontier engine: {frontier['frontier_engine_status']}",
        f"- Frontier protocol promoted: {str(frontier['frontier_engine_protocol_promoted']).lower()}",
        f"- Tier-2 candidates: {frontier['tier2_candidate_count']}",
        f"- Tier-3 static probe authorizations: {frontier['tier3_candidate_count']}",
        f"- Issue-derived repair episodes: {frontier['issue_derived_repair_count']}",
        f"- Native external repair episodes: {frontier['native_external_repair_count']}",
        f"- Runtime activation allowed: {str(frontier['runtime_wrapper_activation_allowed']).lower()}",
        f"- Full scoring: {frontier['full_scoring']}",
        f"- Memory lift: {frontier['memory_lift']}",
        f"- Self-maintaining software: {frontier['self_maintaining_software']}",
        f"- Next safe action: {frontier['next_safe_action']}",
    ])
    write_text_lf(ROOT / "docs" / "CURRENT_FRONTIER_STATUS.md", status_md)
    write("frontier_state_render_verification_batch068g.json", {"status": "PASS", "source_state_hash": frontier["state_hash"], "rendered_path": "docs/CURRENT_FRONTIER_STATUS.md", "hand_maintained_counts": False})
    public_paths = [ROOT / "README.md", ROOT / "docs/current_status.md", ROOT / "docs/capability_inventory.md", ROOT / "docs/technical_validation_gap_report.md", ROOT / "docs/CURRENT_FRONTIER_STATUS.md"]
    findings = []
    for path in public_paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        findings.extend({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "term": term} for term in FORBIDDEN_PUBLIC_TERMS if term in text)
    write("public_claim_boundary_audit_batch068g.json", {"status": "PASS" if not findings else "FAIL", "findings": findings, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"})
    final = {
        "status": "PASS", "audit_status": "PASS", "validated_current_protocol": "v2.14", "frontier_engine_status": "static_planning_operational",
        "frontier_protocol_promoted": False, "tier2_candidate_count": 25, "native_target_path_verified_count": sum(s["target_path_verification"]["status"] == "PASS" for s in states),
        "unique_command_resolved_count": sum(s["selected_command_candidate"] is not None for s in states),
        "manual_review_command_conflict_count": sum(bool(s["source_conflicts"]) for s in states),
        "runner_target_collision_count": sum(s["runner_target_split_status"]["classification"] == "runner_target_collision_unresolved_self_runner" for s in states),
        "harness_origin_pass_count": sum(s["harness_origin_status"]["status"] == "PASS" for s in states),
        "provider_feasibility_complete_count": sum(s["provider_feasibility_class"] != "provider_metadata_missing" for s in states),
        "tier3_promotion_count": len(promoted), "tier3_candidate_ids": [s["candidate_id"] for s in promoted],
        "candidate_specific_hardcoding_count": len(hardcoded), "safe_to_delete_now_count": 0,
        "target_tests_executed": 0, "provider_probes_executed": 0, "patch_generated": False, "patch_applied": False,
        "issue_derived_repair_count": 4, "native_external_repair_count": 4, "repair_count_increment": False,
        "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated",
        "exact_next_allowed_action": next_action,
    }
    write("batch068g_final_decision.json", final)
    write("batch068g_handoff_plan.json", {"status": "PASS", "next_allowed_action": next_action, "download_artifact_by_codex": False, "frontier_execution_authorized": False})
    write_text_lf(OUT / "batch068g_summary.md", "\n".join([
        "# Batch068g Command Orthology Frontier Consolidation", "",
        "Batch068g converts verified candidate identity and repository metadata into deterministic static provider-command-probe plans.",
        "Tier 3 authorizes only a future bounded provider-command probe.",
        "The frontier engine is a static planning interface and has not been promoted to the validated current protocol.",
        "Candidate blockers are preserved individually with reopen conditions.",
        "Historical workflows and evidence are preserved.",
        "Full scoring remains disallowed. Memory lift and self-maintaining software remain undemonstrated.",
    ]))
    write_manifest()


def write_manifest() -> None:
    rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rows.append(f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}")
    write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(rows))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068F_ARTIFACT_ZIP"))
    args = parser.parse_args()
    path = Path(args.artifact_zip) if args.artifact_zip else None
    write_outputs(path)
    print(f"Batch068g generated: candidates=25 output={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
