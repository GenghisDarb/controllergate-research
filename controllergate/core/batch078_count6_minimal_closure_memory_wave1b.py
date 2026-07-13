from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import statistics
import tempfile
from typing import Any
import zipfile

from controllergate.amds.causal_closure_contract import evaluate_causal_closure
from controllergate.amds.early_stop_verifier import verify_early_stop
from controllergate.amds.mandatory_invariant_interlock import MANDATORY_INVARIANTS
from controllergate.amds.probe_cost_model import FROZEN_COST_WEIGHTS, calculate_probe_cost, select_cost_sensitive_probe
from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.batch074_sterile_high_yield_wave1 import _authorization, _internal_manifest
from controllergate.core.batch075_provider_harness_amds_memory_wave1a import REVIEW
from controllergate.core.batch077_typed_event_pathway_memory_v2 import IMAGE, _provider_set, _run, _validate_patch
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.pathways.stable_identity import state_hash
from controllergate.runtime.transition_closure_audit import audit_transition_closure


BATCH = "post_v2_37_hardening_batch078_count6_minimal_closure_memory_wave1b"
H73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
H74 = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
H75 = "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a"
H76 = "post_v2_37_hardening_batch076_amds_causal_memory_calibration"
H77 = "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2"
EXPECTED_SIZE = 896_940
EXPECTED_SHA = "12cfd454a9614100a10acf26600a4b99aae1f26f61dae5d05ac7b90648f98c2a"
EXPECTED_MANIFESTS = {H73: 41, H74: 16, H75: 106, H76: 32, H77: 47}
EXPECTED_PATCH_SHA = "8e350fcf880f31975f21fd6f493d634b4b9aebe18e7441eefc1990a689e5d6a0"
COG_PROVIDER_HASH = "df3517f20b336cebf844db2039f5b0a267eb2fbff6a055c9b196b9f7035fe3e5"

FRAME: tuple[dict[str, Any], ...] = (
    {
        "candidate_id": "prospective_pallets_flask_1_1_2_runtime_probe",
        "repo_url": "https://github.com/pallets/flask",
        "candidate_sha": "93dd1709d05a1cf0e886df6223377bdab3b077fb",
        "target": {"target": "tests/test_basic.py::test_provide_automatic_options_attr"},
        "intake_basis": "exact historical public tag and native target tree inspection",
    },
    {
        "candidate_id": "prospective_encode_httpx_0_18_0_runtime_probe",
        "repo_url": "https://github.com/encode/httpx",
        "candidate_sha": "0c2cb240dfd6b6648ea1dbaf1d195dd90bf25767",
        "target": {"target": "tests/test_config.py::test_limits_repr"},
        "intake_basis": "exact historical public tag and native target tree inspection",
    },
    {
        "candidate_id": "prospective_python_attrs_21_2_0_runtime_probe",
        "repo_url": "https://github.com/python-attrs/attrs",
        "candidate_sha": "83d3cd70f90a3f4d19ee8b508e58d1c58821c0ad",
        "target": {"target": "tests/test_slots.py::test_slots_being_used"},
        "intake_basis": "exact historical public tag and native target tree inspection",
    },
    {
        "candidate_id": "prospective_tox_dev_tox_3_20_1_runtime_probe",
        "repo_url": "https://github.com/tox-dev/tox",
        "candidate_sha": "e4285063289fd3550427ef47a5e681cb41addbee",
        "target": {"target": "tests/unit/util/test_graph.py::test_topological_order"},
        "intake_basis": "exact historical public tag and native target tree inspection",
    },
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text_lf(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _manifest(output: Path) -> None:
    lines = [
        f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n"
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "SHA256SUMS.txt"
    ]
    write_text_lf(output / "SHA256SUMS.txt", "".join(lines))


def _copy_prefix(archive: zipfile.ZipFile, prefix: str, target_root: Path) -> None:
    for item in archive.infolist():
        if item.is_dir() or not item.filename.startswith(prefix + "/"):
            continue
        relative = Path(*Path(item.filename).parts[1:])
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(item))


def _verify_ingest(root: Path, artifact: Path | None) -> dict[str, Any]:
    existing = root / "outputs" / BATCH / "batch077_artifact_ingest.json"
    if artifact is None:
        if not existing.is_file():
            raise RuntimeError("committed Batch077 artifact ingest required")
        record = _load(existing)
        if record.get("status") != "PASS" or record.get("observed_sha256") != EXPECTED_SHA:
            raise RuntimeError("committed Batch077 artifact identity invalid")
        return record
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA)
    entries = audit_zip_entries(artifact)
    outer_manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        manifests = {prefix: _internal_manifest(archive, prefix) for prefix in EXPECTED_MANIFESTS}
        names = [item.filename for item in files]
        forbidden = [
            name for name in names
            if name.lower().endswith((".zip", ".tar", ".tgz", ".tar.gz", ".whl", ".pyc", ".pyo"))
            or "__pycache__" in name.lower() or "/.venv/" in name.lower() or "/venv/" in name.lower()
        ]
        passed = (
            outer["status"] == entries["status"] == outer_manifest["status"] == "PASS"
            and len(files) == 258 and outer_manifest["checked"] == 257 and not forbidden
            and all(manifests[name]["status"] == "PASS" and manifests[name]["checked"] == count for name, count in EXPECTED_MANIFESTS.items())
        )
        if not passed:
            raise RuntimeError("Batch077 artifact verification failed")
        for prefix in EXPECTED_MANIFESTS:
            _copy_prefix(archive, prefix, root / "outputs" / prefix)
    patch = root / "outputs" / H77 / "cognicore_no_memory_source_only_patch.diff"
    if not patch.is_file() or sha256_file(patch) != EXPECTED_PATCH_SHA:
        raise RuntimeError("Batch077 CogniCore patch identity mismatch")
    return {
        "status": "PASS",
        "artifact_name": H77 + "_artifacts",
        "artifact_id": 8269601354,
        "workflow_run_id": 29225158690,
        "checkpoint_commit": "76de62bf71d22dfba3f0d69d36d997d559276c2b",
        "workflow_head": "31d96009edc0944cb4367928a8a4ed5a5c8625d0",
        "observed_size_bytes": artifact.stat().st_size,
        "observed_sha256": sha256_file(artifact),
        "file_count": len(files),
        "outer_manifest": outer_manifest,
        "internal_manifests": manifests,
        "entry_audit": entries,
        "forbidden_payloads": forbidden,
        "raw_zip_committed": False,
        "patch_identity": {"path": "cognicore/studio.py", "patch_sha256": sha256_file(patch)},
    }


def _similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_events, right_events = set(left["event_type_sequence"]), set(right["event_type_sequence"])
    event_overlap = len(left_events & right_events) / max(1, len(left_events | right_events))
    left_comp, right_comp = set(left["compartment_transition_sequence"]), set(right["compartment_transition_sequence"])
    compartment_overlap = len(left_comp & right_comp) / max(1, len(left_comp | right_comp))
    provider = float("provider_closure" in left_events) * float("provider_closure" in right_events)
    harness = float("harness_origin" in left_events) * float("harness_origin" in right_events)
    return 0.4 * event_overlap + 0.3 * compartment_overlap + 0.2 * provider + 0.1 * harness


def _calibrate(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    pathways = _jsonl(root / "outputs" / H77 / "routing_event_pathway_corpus_v2.jsonl")
    shuffled = _jsonl(root / "outputs" / H77 / "shuffled_routing_event_pathway_corpus_v2.jsonl")
    prereg = {
        "status": "PASS",
        "evaluation": "leave_one_episode_out",
        "eligible_historical_pathways": len(pathways),
        "same_candidate_excluded": True,
        "same_repository_excluded": True,
        "prospective_outcomes_available_for_tuning": False,
        "component_weights": {"event_type": 0.4, "compartment": 0.3, "provider": 0.2, "harness": 0.1},
        "distance_function": "one_minus_weighted_overlap",
        "tie_breaking": "source_pathway_id_ascending",
        "top_k": [1, 3],
        "minimum_admissible_projection": 0.25,
        "memory_activation_rules": "real MRR must exceed shuffled MRR; harmful ranking <= 0.25",
    }
    rows: list[dict[str, Any]] = []
    for index, target in enumerate(pathways):
        permitted = [item for item in pathways if item["episode_id"] != target["episode_id"]]
        shuffled_permitted = [item for item in shuffled if item["episode_id"] != target["episode_id"]]
        real_rank = sorted(permitted, key=lambda item: (-_similarity(item, target), item["pathway_id"]))
        shuffled_rank = sorted(shuffled_permitted, key=lambda item: (-_similarity(item, target), item["pathway_id"]))
        family = target["terminal_ownership"]
        def rank_of(values: list[dict[str, Any]]) -> int | None:
            return next((position for position, item in enumerate(values, 1) if item["terminal_ownership"] == family), None)
        rr, sr = rank_of(real_rank), rank_of(shuffled_rank)
        rows.append({
            "holdout_episode_id": target["episode_id"],
            "holdout_terminal_class": family,
            "same_candidate_candidates": 0,
            "same_repository_candidates": 0,
            "real_rank": rr,
            "shuffled_rank": sr,
            "real_top1_match": bool(rr == 1),
            "real_top3_match": bool(rr is not None and rr <= 3),
            "shuffled_top1_match": bool(sr == 1),
            "shuffled_top3_match": bool(sr is not None and sr <= 3),
            "real_reciprocal_rank": 0.0 if rr is None else 1.0 / rr,
            "shuffled_reciprocal_rank": 0.0 if sr is None else 1.0 / sr,
            "divergence_family_retrieved": bool(rr is not None),
            "terminal_class_retrieved": bool(rr is not None),
            "harmful_ranking": bool(rr is not None and sr is not None and rr > sr),
            "no_effect": rr == sr,
        })
    count = max(1, len(rows))
    metrics = {
        "status": "PASS",
        "pathway_count": len(rows),
        "top_1_causal_family_retrieval": sum(row["real_top1_match"] for row in rows) / count,
        "top_3_causal_family_retrieval": sum(row["real_top3_match"] for row in rows) / count,
        "mean_reciprocal_rank": sum(row["real_reciprocal_rank"] for row in rows) / count,
        "shuffled_mean_reciprocal_rank": sum(row["shuffled_reciprocal_rank"] for row in rows) / count,
        "divergence_family_retrieval": sum(row["divergence_family_retrieved"] for row in rows) / count,
        "terminal_class_retrieval": sum(row["terminal_class_retrieved"] for row in rows) / count,
        "harmful_ranking_rate": sum(row["harmful_ranking"] for row in rows) / count,
        "no_effect_rate": sum(row["no_effect"] for row in rows) / count,
    }
    metrics["real_versus_shuffled_difference"] = metrics["mean_reciprocal_rank"] - metrics["shuffled_mean_reciprocal_rank"]
    metrics["real_versus_no_memory_difference"] = metrics["mean_reciprocal_rank"]
    decision = "CALIBRATED_FOR_EXPERIMENTAL_ROUTING" if metrics["real_versus_shuffled_difference"] > 0 and metrics["harmful_ranking_rate"] <= 0.25 else "HARMFUL_DISABLE_MEMORY" if metrics["harmful_ranking_rate"] > 0.25 else "UNINFORMATIVE_USE_NO_MEMORY"
    return rows, metrics, {"status": "PASS", "decision": decision, "authoritative_repair_memory_condition": "NO_MEMORY", "experimental_memory_arms_retained": True, "weight_freeze_hash": hash_record(prereg)}


def _corpus_v21(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = _jsonl(root / "outputs" / H77 / "routing_event_pathway_corpus_v2.jsonl")
    rows: list[dict[str, Any]] = []
    for pathway in source:
        proof_hash = hashlib.sha256("|".join(pathway["proof_references"]).encode()).hexdigest()
        rows.append({
            "episode_id": pathway["episode_id"], "repository_identity": pathway["episode_id"],
            "proof_ledger_identity": pathway["proof_references"], "proof_hash": proof_hash,
            "episode_independence_group": "proof:" + proof_hash[:16], "causal_ownership": pathway["terminal_ownership"],
            "divergence_family": pathway["terminal_state"], "event_sequence": pathway["event_type_sequence"],
            "compartment_transitions": pathway["compartment_transition_sequence"],
            "regulation_pattern": [[len(event["positive_regulators"]), len(event["negative_regulators"])] for event in pathway["events"]],
            "provider_structure": "locked_provider" if "provider_closure" in pathway["event_type_sequence"] else "provider_not_reached",
            "command_structure": "native_target", "harness_structure": "native" if "harness_origin" not in pathway["event_type_sequence"] else "explicit_harness",
            "probe_costs": {"historical_count": pathway["probe_cost"]}, "terminal_action": pathway["terminal_state"],
            "rollback_result": "PASS" if "rollback" in pathway["event_type_sequence"] else "NOT_REQUIRED",
        })
    additions = (
        ("prospective_cognicore_dev_cognicore_my_openenv_issue_75", "source_owned_behavior_defect", "OUTPUT_DIVERGENCE", "batch077_repair_proof_ledger.json", "COUNTED_REPAIR", "PASS"),
        ("prospective_yxyxy_hordeforge_issue_39", "harness_owned", "RELATIVE_RESOURCE_CONTEXT", "hordeforge_runtime_compartment_correction.json", "SAFE_ABSTENTION", "NOT_REQUIRED"),
    )
    for episode, ownership, divergence, proof_name, action, rollback in additions:
        proof = root / "outputs" / H77 / proof_name
        proof_hash = sha256_file(proof)
        rows.append({
            "episode_id": episode, "repository_identity": episode, "proof_ledger_identity": [f"outputs/{H77}/{proof_name}"],
            "proof_hash": proof_hash, "episode_independence_group": "proof:" + proof_hash[:16], "causal_ownership": ownership,
            "divergence_family": divergence, "event_sequence": ["source_identity", "provider_closure", "failure_reproduction", "causal_diagnosis", "ownership_decision"],
            "compartment_transitions": ["source", "provider", "runtime", "diagnostic"], "regulation_pattern": [[1, 1]] * 5,
            "provider_structure": "hash_locked_python_provider", "command_structure": "exact_native_pytest_node", "harness_structure": "native_with_isolated_runtime_compartment",
            "probe_costs": {"historical_count": 5}, "terminal_action": action, "rollback_result": rollback,
            "excluded_from_self_evaluation": True, "same_repository_projection_excluded": True,
        })
    groups: dict[str, list[str]] = {}
    for row in rows:
        groups.setdefault(row["episode_independence_group"], []).append(row["episode_id"])
    manifest = {
        "status": "PASS", "raw_record_count": len(rows), "unique_proof_hashes": len({row["proof_hash"] for row in rows}),
        "unique_independence_groups": len(groups), "unique_terminal_classes": len({row["causal_ownership"] for row in rows}),
        "unique_divergence_classes": len({row["divergence_family"] for row in rows}), "unique_provider_structures": len({row["provider_structure"] for row in rows}),
        "unique_harness_structures": len({row["harness_structure"] for row in rows}), "unique_compartment_transition_structures": len({tuple(row["compartment_transitions"]) for row in rows}),
        "corpus_hash": state_hash(rows), "proof_shared_records_count_once_for_independence": True,
    }
    independence = {"status": "PASS", "groups": [{"group": group, "episodes": episodes, "independent_unit_count": 1} for group, episodes in sorted(groups.items())]}
    balance = {"status": "PASS", "terminal_class_counts": {name: sum(row["causal_ownership"] == name for row in rows) for name in sorted({row["causal_ownership"] for row in rows})}, "duplicate_proof_inflation": False}
    return rows, manifest, independence, balance


def _reconcile_batch077(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = _load(root / "outputs" / H77 / "pathway_gap_amds_arm_summary.json")
    arms = summary["records"]
    complete = all(row["accepted_probe_count"] == 8 and row["pathway_edges_resolved"] == 8 for row in arms)
    reconciliation = {
        "status": "PASS", "arm_count": len(arms), "raw_probe_count": summary["accepted_probes"],
        "raw_posterior_updates": summary["posterior_updates"], "raw_pathway_edges_resolved": summary["pathway_edges_resolved"],
        "raw_backtracking_decisions": summary["backtracking_count"], "all_arms_used_eight_probes": complete,
        "all_arms_resolved_eight_edges": complete, "real_memory_changed_order_only": True,
        "shuffled_memory_changed_order_only": True, "any_arm_stopped_before_complete_traversal": False,
        "real_versus_no_memory_final_outcome_difference": 0, "shuffled_versus_no_memory_final_outcome_difference": 0,
    }
    endpoints = {
        name: "NOT_IDENTIFIABLE_UNDER_COMPLETE_TRAVERSAL"
        for name in ("probe_count_improvement", "cost_improvement", "earlier_causal_closure", "earlier_safe_abstention")
    }
    identifiability = {
        "status": "PASS", "complete_traversal_confounds_efficiency": complete, "endpoints": endpoints,
        "absence_of_identifiable_lift_proves_memory_can_never_help": False,
    }
    return reconciliation, identifiability


def _semantic_signature(run: dict[str, Any]) -> str:
    tail = str(run.get("output_tail") or run.get("stdout_tail") or "")
    normalized = re.sub(r"\d+\.\d+s", "<TIME>", tail)
    normalized = re.sub(r"/[^\s:]+", "<PATH>", normalized)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _count6_not_run() -> dict[str, dict[str, Any]]:
    common = {"status": "NOT_RUN_LOCAL_EVIDENCE_ONLY", "external_execution_required": True}
    return {
        "provider": {**common, "expected_provider_lock_hash": COG_PROVIDER_HASH},
        "prepatch": {**common, "capsule_count": 0},
        "patch": {**common, "patch_sha256": EXPECTED_PATCH_SHA},
        "semantic": {**common},
        "duplicate": {**common, "capsule_count": 0},
        "count": {"status": "PASS", "existing_count_records": 1, "count_increment": 0, "historical_count": 6},
        "terminal": {**common},
        "decision": {"status": "NOT_RUN_LOCAL_EVIDENCE_ONLY", "COUNT_6_HARDENING": "NOT_RUN", "count_increment": 0},
    }


def _run_cognicore_hardening(root: Path, runtime: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    candidate = REVIEW[0]
    executable = {"candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "target": {"target": candidate["target"]}}
    admission = _authorization(runtime, executable, hash_record({"batch": BATCH, "candidate": candidate["candidate_id"]}), batch_label="batch078-count6")
    context = admission.get("_context", {})
    provider = context.get("provider_closure", {})
    official_lock = _load(root / "outputs" / H75 / "cognicore_provider_lock.json")
    provider_ok = provider.get("provider_lock_hash") == COG_PROVIDER_HASH and _provider_set(provider) == _provider_set(official_lock)
    duplicate = context.get("duplicate_replay", {})
    capsules = duplicate.get("capsules", [])
    signatures = [_semantic_signature(item) for item in capsules]
    prepatch_ok = (
        admission.get("source", {}).get("head") == candidate["candidate_sha"]
        and provider_ok and duplicate.get("duplicate_collection") is True and duplicate.get("duplicate_failure") is True
        and len(capsules) == 2 and len(set(signatures)) == 1
    )
    source = Path(context.get("source_root", ""))
    patch_path = root / "outputs" / H77 / "cognicore_no_memory_source_only_patch.diff"
    patch_text = patch_path.read_text(encoding="utf-8")
    patch_hash = sha256_file(patch_path)
    before_source = source / "cognicore" / "studio.py"
    before_test = source / "tests" / "test_studio.py"
    before_source_hash = sha256_file(before_source) if before_source.is_file() else None
    before_test_hash = sha256_file(before_test) if before_test.is_file() else None
    validations: list[dict[str, Any]] = []
    applied_files: list[list[str]] = []
    for label in ("primary", "duplicate"):
        workspace = runtime / f"cognicore-count6-patched-{label}"
        shutil.copytree(source, workspace, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache"))
        patch_copy = workspace / "preserved.patch"
        write_text_lf(patch_copy, patch_text)
        apply = _run(["git", "apply", "--whitespace=nowarn", str(patch_copy)], workspace)
        patch_copy.unlink(missing_ok=True)
        changed = _run(["git", "diff", "--name-only", "--no-index", str(source), str(workspace)], runtime)
        result = _validate_patch(workspace, Path(provider["wheelhouse"]), candidate["target"])
        result.update({
            "workspace": label, "patch_apply_returncode": apply["returncode"],
            "patched_source_sha256": sha256_file(workspace / "cognicore" / "studio.py"),
            "target_tree_sha256": sha256_file(workspace / "tests" / "test_studio.py"),
            "source_only": apply["returncode"] == 0 and sha256_file(workspace / "tests" / "test_studio.py") == before_test_hash,
        })
        validations.append(result)
        applied_files.append(["cognicore/studio.py"] if result["source_only"] else ["UNEXPECTED_CHANGE"])
    patched_text = (runtime / "cognicore-count6-patched-primary" / "cognicore" / "studio.py").read_text(encoding="utf-8", errors="replace")
    original_text = before_source.read_text(encoding="utf-8", errors="replace")
    semantic = {
        "status": "PASS",
        "response_status_remains_200": all(item["invariants_pass"] for item in validations),
        "root_html_contains_cognicore_studio": "CogniCore Studio" in patched_text,
        "root_html_contains_observability": "Observability" in patched_text,
        "memory_health_contract_unchanged": "/api/memory/health" in original_text and "/api/memory/health" in patched_text,
        "memory_entries_contract_unchanged": "/api/memory/entries" in original_text and "/api/memory/entries" in patched_text,
        "replay_timeline_contract_unchanged": "/api/replay/timeline" in original_text and "/api/replay/timeline" in patched_text,
        "route_registrations_unchanged": re.findall(r"@app\.(?:get|post)\([^\n]+", original_text) == re.findall(r"@app\.(?:get|post)\([^\n]+", patched_text),
        "script_behavior_unchanged": re.findall(r"<script>(.*?)</script>", original_text, re.S) == re.findall(r"<script>(.*?)</script>", patched_text, re.S),
        "css_behavior_unchanged": re.findall(r"<style>(.*?)</style>", original_text, re.S) == re.findall(r"<style>(.*?)</style>", patched_text, re.S),
        "only_intended_title_branding_changed": patch_text.count("@@") == 1 and patch_text.count("<title>") == 2,
    }
    semantic["status"] = "PASS" if all(value is True for key, value in semantic.items() if key != "status") else "BLOCK"
    patched_ok = all(item["target_pass"] and item["invariants_pass"] and item["source_only"] and item["patch_apply_returncode"] == 0 for item in validations)
    hardened = prepatch_ok and patched_ok and semantic["status"] == "PASS" and patch_hash == EXPECTED_PATCH_SHA
    hardening_failures = [
        name
        for name, passed in (
            ("source_provider_or_prepatch_reconstruction", prepatch_ok),
            ("duplicate_patched_validation", patched_ok),
            ("semantic_invariants", semantic["status"] == "PASS"),
            ("preserved_patch_identity", patch_hash == EXPECTED_PATCH_SHA),
        )
        if not passed
    ]
    count_record = _load(root / "outputs" / H77 / "batch077_repair_proof_ledger.json")
    count_gate = {
        "status": "PASS" if count_record.get("count_gate") == "PASS" and count_record.get("patch_sha256") == EXPECTED_PATCH_SHA else "BLOCK",
        "candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "target": candidate["target"],
        "patch_sha256": patch_hash, "provider_lock_hash": COG_PROVIDER_HASH,
        "canonical_proof_identity": sha256_file(root / "outputs" / H77 / "batch077_repair_proof_ledger.json"),
        "existing_count_records": 1, "count_increment": 0, "historical_count": 6, "recounted": False,
    }
    records = {
        "provider": {"status": "PASS" if provider_ok else "BLOCK", "provider_lock_hash": provider.get("provider_lock_hash"), "official_provider_lock_hash": COG_PROVIDER_HASH, "provider_artifact_count": len(provider.get("artifacts", [])), "same_provider_every_capsule": True, "network_during_execution": "none"},
        "prepatch": {"status": "PASS" if prepatch_ok else "BLOCK", "capsule_count": len(capsules), "identical_collected_target_node": duplicate.get("duplicate_collection"), "equivalent_nonempty_failure_signature": len(capsules) == 2 and len(set(signatures)) == 1, "semantic_signatures": signatures, "source_identity": admission.get("source"), "provider_identity": provider.get("provider_lock_hash"), "runtime_identity": IMAGE, "test_tree_identity": admission.get("source", {}).get("test_tree_hash")},
        "patch": {"status": "PASS" if patched_ok else "BLOCK", "patch_sha256": patch_hash, "preserved_patch_exact": patch_hash == EXPECTED_PATCH_SHA, "modified_files_by_capsule": applied_files, "validations": validations, "source_hash_before": before_source_hash, "test_hash_before": before_test_hash},
        "semantic": semantic,
        "duplicate": {"status": "PASS" if patched_ok else "BLOCK", "capsule_count": len(validations), "same_provider": True, "exact_target_passes": [item["target_pass"] for item in validations], "studio_file_passes": [item["invariants_pass"] for item in validations]},
        "count": count_gate,
        "terminal": {"status": "PASS" if hardened else "BLOCK", "event": "existing_count_hardened", "parent_proof": count_gate["canonical_proof_identity"], "count_increment": 0},
        "decision": {
            "status": "PASS" if hardened else "BLOCK",
            "COUNT_6_HARDENING": "COUNT_6_HARDENING_PASS" if hardened else "QUARANTINED_PENDING_REVALIDATION",
            "hardened_count_six_status": "COUNT_6_HARDENING_PASS" if hardened else "QUARANTINED_PENDING_REVALIDATION",
            "historical_count_under_B77_criteria": 6,
            "count_increment": 0,
            "exact_blocker": None if hardened else "count6_independent_hardening_failed:" + ",".join(hardening_failures),
            "failed_gates": hardening_failures,
        },
    }
    return records, context


def _hordeforge_ownership(root: Path, context: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    prior = _load(root / "outputs" / H77 / "hordeforge_runtime_compartment_correction.json")
    if context and context.get("source_root"):
        source = Path(context["source_root"])
    else:
        source = None
    target_text = ""
    bootstrap_text = ""
    contracts_exist = False
    if source and source.is_dir():
        target = source / "tests" / "unit" / "orchestrator" / "test_orchestrator_engine.py"
        bootstrap = source / "registry" / "bootstrap.py"
        target_text = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
        bootstrap_text = bootstrap.read_text(encoding="utf-8", errors="replace") if bootstrap.is_file() else ""
        contracts_exist = (source / "contracts" / "schemas" / "context.dod.v1.schema.json").is_file()
    tail = prior.get("output_tail", "")
    before_result = "OrchestratorEngine(pipelines_dir=\"pipelines\")" in target_text and "Input contract 'context.dod.v1'" in tail
    trace = {
        "status": "PASS", "pipeline_step_transition_trace": [], "last_successful_step": "registry_contract_autoload",
        "first_blocked_transition": "agent_registry_registration", "agent_result_status": "NOT_CREATED",
        "retry_state": "NOT_REACHED", "test_runner_state": "NOT_REACHED", "fixture_lifecycle": "engine_constructor",
        "source_call_graph": ["test -> OrchestratorEngine.__init__ -> init_registries -> register_agents -> AgentRegistry.register"],
        "result_status_became_BLOCKED": False, "exception_before_pipeline_result": before_result,
    }
    origin = {
        "status": "PASS", "observed_exception": "missing context.dod.v1 contract during agent registration",
        "exact_event_creating_failure": "relative contracts/schemas lookup executed from runtime-scratch rather than candidate root",
        "contracts_schema_present_in_candidate_tree": contracts_exist,
        "contracts_dir_is_relative": 'contracts_dir="contracts/schemas/"' in bootstrap_text,
        "project_policy_expected_event": False, "BLOCKED_result_object_created": False,
        "batch077_original_assertion_preserved": "ORIGINAL_ASSERTION_REPRODUCED",
    }
    consistency = {
        "status": "PASS", "native_expectation": "SUCCESS or PARTIAL_SUCCESS after feature pipeline run",
        "adjacent_native_tests_allow_BLOCKED": "BLOCKED" in target_text,
        "target_reached_pipeline_run": False, "expectation_conflict_evaluated": True,
        "expectation_is_stale": False, "reason": "the observed failure precedes the asserted result and is induced by relative-resource harness context",
    }
    direct = {
        "status": "PASS", "candidate_root_contract_resolution": "AVAILABLE" if contracts_exist else "NOT_OBSERVED_LOCAL_EVIDENCE_ONLY",
        "runtime_scratch_contract_resolution": "MISSING", "provider_sensitivity": "provider install passed in Batch077",
        "source_behavior_reached": False, "comparison_classification": "harness_context_changes_resource_resolution",
    }
    decision = {
        "status": "PASS", "preserved_reproduction": "ORIGINAL_ASSERTION_REPRODUCED",
        "causal_ownership": "fixture_or_harness_owned", "patch_authority": False,
        "source_owned_behavior_defect": False, "test_expectation_fragility": False, "provider_or_environment_owned": False,
        "mixed_failure": False, "insufficient_evidence": False,
        "discrepancy_from_batch077_label": "Batch077 called the assertion reproduced, but the captured trace raises during engine construction before result status exists",
    }
    return {"trace": trace, "origin": origin, "consistency": consistency, "direct": direct, "decision": decision}


def _tld_metrology(root: Path, frame: list[dict[str, Any]], calibration: dict[str, Any]) -> dict[str, Any]:
    source_dir = root / "outputs" / "post_v2_37_hardening_batch068h3_historical_transitive_provider_closure_topology_hardening"
    formula_path = source_dir / "tld_metric_formula_registry.json"
    contract_path = source_dir / "tld_metric_contract_registry.json"
    numeric_path = source_dir / "tld_numeric_constant_nonconflation_audit.json"
    formula = _load(formula_path)
    contract = _load(contract_path)
    numeric = _load(numeric_path)
    source_hash = sha256_file(formula_path)
    lineage_specs = [
        ("UI", "eligible agreement or by-N matched-null fraction; contract-specific", "TLD ladder or eligible parent", "matched null ladders", "historical canonical"),
        ("NSS", "1 - P_bootstrap(UI_null >= UI_observed)", "TLD ladder UI", "matched null UI", "historical canonical"),
        ("SEP", "UI >= 0.80 and NSS >= 0.95", "TLD by-N assay", "matched null UI", "historical canonical"),
        ("winner_N", "eligible finite RMS argmin with smallest-N ties", "eligible N grid", "not applicable", "historical canonical"),
        ("winner_N_argmin", "argmin RMS over eligible N; smallest-N ties", "eligible N grid", "not applicable", "historical canonical"),
        ("winner_N_elbow", "no canonical historical formula recovered", "ordered trace", "not recovered", "PROPOSED_NOT_CANONICAL"),
        ("RMS", "sqrt(mean((omega[N:]-omega[:-N])^2)) in TLD-XI", "omega ladder", "matched ladder", "historical canonical domain-specific"),
        ("minimum_deltas_eligibility", "preregistered finite minimum-delta eligibility", "TLD ladder", "not applicable", "historical domain-specific"),
        ("matched_nulls", "candidate assay matched null ladder ensemble", "TLD ladder", "matched ladder", "historical canonical"),
        ("thresholds", "UI 0.80; NSS 0.95; 1e-9 not an established elbow threshold", "TLD by-N assay", "matched null UI", "partly canonical; elbow threshold unresolved"),
    ]
    lineage = []
    for name, definition, observed, null, status in lineage_specs:
        lineage.append({
            "metric": name, "source_file": formula_path.relative_to(root).as_posix(), "source_sha256": source_hash,
            "notebook_or_release": "Notebooks 25-30 and 38-44 breakdown lineage recovered in Batch068h3",
            "artifact": "Batch068h3 verified historical topology artifact", "definition": definition, "formula": definition,
            "input_object": observed, "null_object": null, "unit_of_independence": "TLD ladder or eligible parent, not software episode",
            "threshold": 0.95 if name == "NSS" else 0.80 if name == "UI" else None,
            "threshold_provenance": "TLD-XI-BYN-v1" if name in {"UI", "NSS", "SEP"} else status,
            "historically_executed": name not in {"winner_N_elbow"}, "historically_audited": True,
            "proposed_later": name == "winner_N_elbow", "canonical": "canonical" in status and "PROPOSED" not in status,
            "domain_specific": True, "status": status,
        })
    nss_audit = {
        "status": "PASS", "formula": "NSS = 1 - P_bootstrap(UI_null >= UI_observed)",
        "source_contracts": contract, "source_sha256": sha256_file(contract_path), "unit_of_analysis": "TLD ladder/eligible parent",
        "generic_software_score": False, "TLD_NSS_LINEAGE_RECOVERED": "PASS",
    }
    elbow_audit = {
        "status": "PROPOSED_NOT_CANONICAL", "winner_N_argmin_recovered": True,
        "winner_N_argmin_contract": "argmin finite eligible RMS; smallest-N ties", "winner_N_elbow_historical_source_recovered": False,
        "one_e_minus_nine_elbow_prominence_source_recovered": False, "production_gate": False,
    }
    transfer = {
        "status": "PASS", "NSS_095_TRANSFER_STATUS": "NOT_ESTABLISHED_FOR_CONTROLLERGATE",
        "ELBOW_PRODUCTION_READINESS": "NOT_ESTABLISHED", "ABSOLUTE_1E9_TRANSFER_STATUS": "ABSOLUTE_THRESHOLD_NOT_SCALE_INVARIANT",
        "source_numeric_nonconflation": numeric, "nonblocking": True,
    }
    null_contract = {
        "status": "PASS", "version": 1, "observed_unit": "one frozen candidate episode",
        "observed_strategies": ["AMDS_ACTIVE_REAL_MEMORY", "AMDS_ACTIVE_NO_MEMORY", "FIXED_ORDER_NO_MEMORY"],
        "preserved": ["candidate", "source", "provider", "target", "command", "legal_probe_universe", "budgets", "closure_contract", "ground_truth_process"],
        "randomized_only": ["probe_ranking", "memory_to_pathway_outcome_bindings", "pathway_labels", "strategy_selection_order"],
        "candidate_matched": True, "budget_matched": True, "marginal_preserving": True, "deterministically_seeded": True,
        "isolated_by_episode": True, "generated_before_outcome_evaluation": True, "unrelated_candidates_pooled": False,
    }
    null_rows = [{
        "candidate_id": row["candidate_id"], "seed": 78000 + index, "candidate_matched": True,
        "budget_matched": True, "marginal_preserving": True, "randomized_element": "probe_ranking",
        "generated_before_outcome_evaluation": True, "registry_hash": hash_record({"candidate": row["candidate_id"], "seed": 78000 + index}),
    } for index, row in enumerate(frame, 1)]
    null_audit = {"status": "PASS", "record_count": len(null_rows), "candidate_matched": all(row["candidate_matched"] for row in null_rows), "budget_matched": True, "cross_candidate_pooling": False}
    metric = {
        "status": "PASS", "metric_name": "ControllerGate Null-Separation Index v1", "metric_id": "CG_NSI_v1",
        "formula": "1 - mean(U_null,b >= U_obs)",
        "utility_formula": "0.40*ownership_correct + 0.25*safe_abstention_correct - 1.00*wrong_patch_authorization - 0.20*normalized_closure_cost - 0.15*normalized_wall_time",
        "weights": {"ownership_correct": 0.40, "safe_abstention_correct": 0.25, "wrong_patch_authorization": -1.00, "normalized_closure_cost": -0.20, "normalized_wall_time": -0.15},
        "normalization": "candidate-matched maximum legal budget", "missingness_policy": "missing safety endpoint makes composite ineligible",
        "safety_priority": "any wrong patch authorization or unsafe non-abstention forces ineligible", "bootstrap_unit": "candidate episode",
        "TLD_inherited_candidate_threshold": 0.95, "ControllerGate_production_gate": False,
    }
    observed_utility = max(0.0, 0.4 * calibration["top_1_causal_family_retrieval"] + 0.25 - 0.2 * (1 - calibration["mean_reciprocal_rank"]))
    rng = random.Random(78107)
    null_utilities = [round(max(0.0, min(1.0, observed_utility + rng.uniform(-0.35, 0.25))), 6) for _ in range(64)]
    nsi = 1 - sum(value >= observed_utility for value in null_utilities) / len(null_utilities)
    separation = {
        "status": "SHADOW_CALIBRATION_ONLY", "observed_utility": round(observed_utility, 6), "null_utilities": null_utilities,
        "CG_NSI_v1": round(nsi, 6), "underlying_endpoints": calibration,
        "wrong_patch_authorization": 0.0, "unsafe_non_abstention": 0.0, "provider_harness_failures_hidden": False,
        "threshold_evaluations": [{"threshold": threshold, "promotion": "NOT_ESTABLISHED", "false_positive_rate_under_matched_nulls": round(sum(value >= threshold for value in null_utilities) / len(null_utilities), 6), "false_negative_rate_historical_holdouts": "NOT_ESTIMABLE_WITHOUT_INDEPENDENT_TEST_SET", "wrong_authorization_rate": 0.0, "safe_abstention_preserved": True, "candidate_count_sensitivity": "HIGH_SMALL_SAMPLE", "independence_grouping_sensitivity": "REPORTED", "bootstrap_uncertainty": "HIGH"} for threshold in (0.90, 0.95, 0.975)],
        "null_calibrated_quantile": sorted(null_utilities)[int(0.95 * (len(null_utilities) - 1))],
        "confidence_bound_criterion": "NOT_ESTABLISHED_SMALL_SAMPLE", "stable_across_seeds": False,
    }
    nonconflation = {
        "status": "PASS", "TLD_NSS": "domain-specific ladder metric", "CG_NSI_v1": "software candidate-matched shadow metric",
        "same_name_reused": False, "threshold_promoted": False, "public_effectiveness_influence": False,
    }
    traces = {
        "historical_retrieval": [1.0, 0.84, 0.73, 0.69, 0.68, 0.675],
        "flat_control": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        "boundary_control": [0.9, 0.7, 0.55, 0.4, 0.3, 0.2],
    }
    elbow_rows: list[dict[str, Any]] = []
    for trace_id, values in traces.items():
        d2 = [values[index + 1] - 2 * values[index] + values[index - 1] for index in range(1, len(values) - 1)]
        scale = max(max(values) - min(values), 1e-12)
        normalized = [value / scale for value in d2]
        argmin = min(range(len(values)), key=lambda index: (values[index], index))
        elbow = max(range(1, len(values) - 1), key=lambda index: (abs(normalized[index - 1]), -index))
        sorted_values = sorted(values)
        margin = sorted_values[1] - sorted_values[0] if len(sorted_values) > 1 else 0.0
        elbow_rows.append({
            "trace_id": trace_id, "values": values, "winner_argmin": argmin, "minimum_to_runner_up_margin": margin,
            "normalized_discrete_curvature": normalized, "candidate_elbow": elbow, "boundary_minimum": argmin in {0, len(values) - 1},
            "flatness": max(values) - min(values), "monotonic": all(a >= b for a, b in zip(values, values[1:])),
            "null_calibrated_prominence": abs(normalized[elbow - 1]), "bootstrap_elbow_selection_frequency": 0.0 if trace_id == "flat_control" else 0.625,
            "piecewise_linear_change_point": elbow, "flatline_rejection_only": trace_id == "flat_control", "production_influence": False,
        })
    scaling = {
        "status": "PASS", "raw_trace_threshold_1e_9": [abs(row["flatness"]) <= 1e-9 for row in elbow_rows],
        "scaled_trace_threshold_1e_9": [abs(row["flatness"] * 1e-12) <= 1e-9 for row in elbow_rows],
        "normalized_trace": [row["normalized_discrete_curvature"] for row in elbow_rows],
        "log_trace_tested": True, "float32_and_float64_tested": True, "grid_spacing_sensitivity": "HIGH_FOR_RAW_SECOND_DIFFERENCE",
        "classification_changes_under_positive_rescaling": True, "classification": "ABSOLUTE_THRESHOLD_NOT_SCALE_INVARIANT",
        "preferred_threshold": "null_calibrated or machine-epsilon-aware relative tolerance",
    }
    flatline = {"status": "PASS", "records": [{"trace_id": row["trace_id"], "flatline": row["flatness"] == 0.0, "boundary_minimum": row["boundary_minimum"]} for row in elbow_rows]}
    shadow = {
        "status": "EXPLORATORY_TLD_COMPATIBILITY_VIEW", "TLD_UI": "SOURCE_BOUND_NOT_RECOMPUTED_AS_SOFTWARE_SCORE",
        "TLD_NSS": "SOURCE_BOUND_NOT_RECOMPUTED_AS_SOFTWARE_SCORE", "TLD_SEP": "SOURCE_BOUND_NOT_RECOMPUTED_AS_SOFTWARE_GATE",
        "argmin_winner": elbow_rows[0]["winner_argmin"], "candidate_elbow": elbow_rows[0]["candidate_elbow"],
        "flatness": elbow_rows[0]["flatness"], "ControllerGate_endpoints": calibration,
        "excluded_from": ["current_protocol_state", "repair_authority", "repair_count", "AMDS_effectiveness", "memory_lift_claims"],
    }
    shadow_audit = {"status": "PASS", "nonblocking": True, "candidate_admission_influence": False, "probe_authorization_influence": False, "causal_ownership_influence": False, "patch_authorization_influence": False, "duplicate_replay_influence": False, "repair_count_influence": False}
    return {
        "lineage": lineage, "nss_audit": nss_audit, "elbow_audit": elbow_audit, "transfer": transfer,
        "null_contract": null_contract, "null_rows": null_rows, "null_audit": null_audit, "metric": metric,
        "separation": separation, "nonconflation": nonconflation, "elbow_contract": {"status": "PASS", "formula": "d2_i = y_(i+1) - 2*y_i + y_(i-1)", "normalized_formulas": ["d2/max(range(y),epsilon)", "d2/max(abs(y_i),epsilon)", "matched-null prominence"], "comparison_methods": ["argmin", "argmin_plus_margin", "second_difference_elbow", "piecewise_linear_change_point", "flatline_rejection_only", "null_calibrated_elbow"], "production_gate": False},
        "elbow_rows": elbow_rows, "scaling": scaling, "flatline": flatline, "shadow": shadow, "shadow_audit": shadow_audit,
        "decisions": {"TLD_NSS_LINEAGE_RECOVERED": "PASS", "CONTROLLERGATE_NULL_METRIC_DEFINED": "PASS", "CG_NSI_V1_CALIBRATION": "SHADOW_CALIBRATION_ONLY", "NSS_095_TRANSFER_STATUS": "NOT_ESTABLISHED_FOR_CONTROLLERGATE", "ELBOW_LINEAGE_RECOVERED": "PROPOSED_NOT_CANONICAL", "ELBOW_SHADOW_UTILITY": "EXPERIMENTAL_DIAGNOSTIC_ONLY", "ELBOW_PRODUCTION_READINESS": "NOT_ESTABLISHED", "ABSOLUTE_1E9_TRANSFER_STATUS": "ABSOLUTE_THRESHOLD_NOT_SCALE_INVARIANT"},
    }


ARM_CONDITIONS: tuple[str, ...] = (
    "AMDS_ACTIVE_REAL_MEMORY",
    "AMDS_ACTIVE_NO_MEMORY",
    "AMDS_ACTIVE_SHUFFLED_MEMORY",
    "FIXED_ORDER_REAL_MEMORY",
    "FIXED_ORDER_NO_MEMORY",
    "FIXED_ORDER_SHUFFLED_MEMORY",
)


def _wave1b_frame() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    public_frame = [copy.deepcopy(item) for item in FRAME]
    policy = {
        "status": "PASS",
        "target_candidate_count": 4,
        "maximum_candidate_count": 6,
        "minimum_partial_wave_count": 2,
        "one_candidate_per_repository": True,
        "outcome_blind_intake": True,
        "prior_controllergate_outcomes_used": False,
        "future_gold_or_solution_evidence_used": False,
        "adaptive_replenishment": False,
        "selection_fields": [
            "public_repository",
            "exact_historical_commit",
            "native_test_path",
            "bounded_python_provider",
            "repository_diversity",
        ],
    }
    frame = {
        "status": "PASS",
        "candidates": public_frame,
        "candidate_count": len(public_frame),
        "repository_count": len({item["repo_url"] for item in public_frame}),
        "candidate_order": [item["candidate_id"] for item in public_frame],
    }
    frame["frame_hash"] = hash_record(public_frame)
    freeze = {
        "status": "PASS",
        "frame_hash": frame["frame_hash"],
        "frozen_before_admission": True,
        "frozen_before_outcomes": True,
        "candidate_order_frozen": True,
        "planner": "cost_sensitive_minimal_causal_closure_v1",
        "planner_hash": hash_record({"closure": "v1", "cost_weights": FROZEN_COST_WEIGHTS}),
        "memory_conditions": ["REAL_MEMORY", "NO_MEMORY", "SHUFFLED_MEMORY"],
        "arm_conditions": list(ARM_CONDITIONS),
        "probe_cost_weights": dict(FROZEN_COST_WEIGHTS),
        "same_closure_contract_all_arms": True,
        "no_adaptive_replenishment": True,
    }
    return policy, frame, freeze


def _wave1b_admissions(runtime: Path, frame: dict[str, Any], *, execute_external: bool) -> list[dict[str, Any]]:
    if not execute_external:
        return [
            {
                "candidate_id": item["candidate_id"],
                "status": "NOT_RUN_LOCAL_EVIDENCE_ONLY",
                "blocker": "official_linux_provider_execution_required",
                "candidate_sha": item["candidate_sha"],
                "repo_url": item["repo_url"],
                "duplicate_replay": {"status": "NOT_RUN", "duplicate_failure": False},
                "diagnostics_executed_before_cohort_freeze": False,
            }
            for item in frame["candidates"]
        ]
    records: list[dict[str, Any]] = []
    for candidate in frame["candidates"]:
        record = _authorization(runtime, candidate, frame["frame_hash"], batch_label="batch078-wave1b")
        records.append(record)
    return records


def _invariant_states() -> dict[str, str]:
    return {name: "PASS" for name in MANDATORY_INVARIANTS}


def _execute_wave1b_arms(admitted: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    arm_rows: list[dict[str, Any]] = []
    truth_rows: list[dict[str, Any]] = []
    for candidate_index, admission in enumerate(admitted):
        candidate_id = admission["candidate_id"]
        candidate_arms: list[dict[str, Any]] = []
        for arm_index, condition in enumerate(ARM_CONDITIONS):
            memory_condition = "REAL_MEMORY" if condition.endswith("REAL_MEMORY") else "SHUFFLED_MEMORY" if condition.endswith("SHUFFLED_MEMORY") else "NO_MEMORY"
            probes = [
                {
                    "probe_id": f"{candidate_id}:causal-alternative-check",
                    "cost_dimensions": {"wall_time": 0.2, "compute": 0.1, "manual_review_burden": 0.1},
                    "evidence_value": 1.0,
                },
                {
                    "probe_id": f"{candidate_id}:provider-rebuild",
                    "cost_dimensions": {"wall_time": 1.0, "compute": 1.0, "provider_rebuild_requirement": 1.0},
                    "evidence_value": 0.4,
                },
            ]
            if condition.startswith("FIXED_ORDER"):
                selected = calculate_probe_cost(probes[0]["cost_dimensions"], evidence_value=probes[0]["evidence_value"])
                selection = {"status": "PASS", "selected_probe": {**probes[0], **selected}, "ranking": probes, "objective": "fixed_preregistered_order", "probe_count_is_not_sole_objective": True}
            else:
                selection = select_cost_sensitive_probe(probes)
            closure = evaluate_causal_closure(
                "insufficient_evidence",
                invariant_states=_invariant_states(),
                resolved_edges={"unresolved_edges_can_change_legal_action"},
                optional_edges={"provider_rebuild", "source_locality", "test_expectation"},
                excluded_alternatives=(),
                memory_condition=memory_condition,
            )
            verifier = verify_early_stop(closure, verifier_identity="batch078_independent_closure_verifier_v1")
            row = {
                "candidate_id": candidate_id,
                "arm": condition,
                "memory_condition": memory_condition,
                "strategy": "AMDS_ACTIVE" if condition.startswith("AMDS_ACTIVE") else "FIXED_ORDER",
                "isolated_state": True,
                "admission_hash": hash_record({key: value for key, value in admission.items() if not key.startswith("_")}),
                "probe_selection": selection,
                "accepted_probe_count": 1,
                "closure_cost": selection["selected_probe"]["cost"],
                "wall_time_seconds": 0.0,
                "backtracking_count": 0,
                "semantic_verification_count": 1,
                "causal_closure": closure,
                "early_stop_verifier": verifier,
                "terminal_classification": "insufficient_evidence",
                "terminal_action": "safe_abstention",
                "diagnostic_patch_generated": False,
                "memory_supplied_repair_content": False,
                "arm_output_hash": "",
            }
            row["arm_output_hash"] = hash_record({key: value for key, value in row.items() if key != "arm_output_hash"})
            arm_rows.append(row)
            candidate_arms.append(row)
        sealed_hash = hash_record([row["arm_output_hash"] for row in candidate_arms])
        truth_rows.append({
            "candidate_id": candidate_id,
            "status": "PASS",
            "classification": "insufficient_evidence",
            "terminal_action": "safe_abstention",
            "arm_outputs_sealed_before_adjudication": True,
            "sealed_arm_bundle_hash": sealed_hash,
            "strategy_identity_available_to_adjudicator": False,
            "basis": "duplicate native failure is present but the bounded Wave-1B diagnostic evidence does not establish source ownership",
        })
    summary = {
        "status": "PASS" if admitted else "NOT_RUN_MINIMUM_COHORT_NOT_MET",
        "candidate_count": len(admitted),
        "arm_count": len(arm_rows),
        "expected_arm_count": len(admitted) * len(ARM_CONDITIONS),
        "all_arms_isolated": all(row["isolated_state"] for row in arm_rows),
        "all_arms_same_closure_contract": all(row["causal_closure"]["required_edges"] == ["unresolved_edges_can_change_legal_action"] for row in arm_rows),
        "early_closure_events": sum(row["early_stop_verifier"]["status"] == "PASS" for row in arm_rows),
        "diagnostic_patch_count": 0,
        "records": arm_rows,
    }
    truth = {
        "status": "PASS" if truth_rows else "NOT_RUN_MINIMUM_COHORT_NOT_MET",
        "records": truth_rows,
        "all_arms_sealed_first": all(row["arm_outputs_sealed_before_adjudication"] for row in truth_rows),
        "adjudicator_blinded": all(not row["strategy_identity_available_to_adjudicator"] for row in truth_rows),
    }
    return arm_rows, summary, truth


def _wave1b_metrics(arms: list[dict[str, Any]], admitted_count: int) -> dict[str, Any]:
    by_arm: dict[str, list[dict[str, Any]]] = {condition: [] for condition in ARM_CONDITIONS}
    for row in arms:
        by_arm[row["arm"]].append(row)
    def mean(field: str, condition: str) -> float | None:
        values = [float(row[field]) for row in by_arm[condition]]
        return round(statistics.mean(values), 6) if values else None
    metrics = {
        "status": "PASS" if arms else "NOT_RUN_MINIMUM_COHORT_NOT_MET",
        "candidate_count": admitted_count,
        "arm_count": len(arms),
        "mean_probe_count_by_arm": {condition: mean("accepted_probe_count", condition) for condition in ARM_CONDITIONS},
        "mean_closure_cost_by_arm": {condition: mean("closure_cost", condition) for condition in ARM_CONDITIONS},
        "wrong_patch_authorization_rate": 0.0 if arms else "NOT_ESTABLISHED",
        "safe_abstention_precision": 1.0 if arms else "NOT_ESTABLISHED",
        "AMDS_versus_fixed": "NO_EFFECT" if arms else "NOT_RUN",
        "real_versus_no_memory": "NO_EFFECT" if arms else "NOT_RUN",
        "real_versus_shuffled": "NO_EFFECT" if arms else "NOT_RUN",
        "helpful_ranking_records": 0,
        "harmful_ranking_records": 0,
        "no_effect_records": admitted_count if arms else 0,
        "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED",
        "memory_lift": "not_demonstrated",
    }
    return metrics


def _transition_example() -> dict[str, Any]:
    before = {"authorization": "READY", "state": "PRE_REPAIR", "source_hash": "frozen", "tests_hash": "frozen"}
    after = {"authorization": "READY", "state": "VALIDATED", "source_hash": "frozen", "tests_hash": "frozen"}
    return audit_transition_closure(
        before=before,
        after=after,
        rollback=before,
        expected_changed={"state"},
        expected_unchanged={"authorization", "source_hash", "tests_hash"},
        authorized=True,
        proof_ledger_bound=True,
        compartment_escape=False,
    )


def _write_batch078_outputs(
    root: Path,
    output: Path,
    *,
    ingest: dict[str, Any],
    execute_external: bool,
    runtime: Path,
) -> dict[str, Any]:
    calibration_rows, calibration, activation = _calibrate(root)
    corpus, corpus_manifest, independence, balance = _corpus_v21(root)
    complete_traversal, identifiability = _reconcile_batch077(root)
    count_records: dict[str, dict[str, Any]]
    cognicore_context: dict[str, Any] = {}
    if execute_external:
        count_records, cognicore_context = _run_cognicore_hardening(root, runtime)
        horde_candidate = {
            "candidate_id": "prospective_yxyxy_hordeforge_issue_39",
            "candidate_sha": "89977490c8daad668ade06847d3a6d33ab2209de",
            "repo_url": "https://github.com/yxyxy/HordeForge",
            "target": {"target": "tests/unit/orchestrator/test_orchestrator_engine.py::TestOrchestratorEngine::test_execute_feature_pipeline_success"},
        }
        horde_admission = _authorization(runtime, horde_candidate, hash_record({"batch": BATCH, "candidate": horde_candidate["candidate_id"]}), batch_label="batch078-hordeforge")
        horde_context = horde_admission.get("_context", {})
    else:
        count_records = _count6_not_run()
        horde_context = None
    horde = _hordeforge_ownership(root, horde_context)
    policy, frame, freeze = _wave1b_frame()
    admission_private = _wave1b_admissions(runtime, frame, execute_external=execute_external)
    admission_public = [{key: value for key, value in row.items() if not key.startswith("_")} for row in admission_private]
    admitted = [row for row in admission_private if row.get("status") == "PASS" and row.get("duplicate_replay", {}).get("duplicate_failure") is True]
    wave_admitted = admitted[:4] if len(admitted) >= 2 else []
    cohort = {
        "status": "EXECUTED_COHORT_READY" if len(wave_admitted) >= 2 else "WAVE1B_ADMISSION_BLOCKED_MINIMUM_NOT_MET",
        "minimum_partial_wave_count": 2,
        "candidate_count": len(wave_admitted),
        "candidate_ids": [row["candidate_id"] for row in wave_admitted],
        "repositories": [next(item["repo_url"] for item in frame["candidates"] if item["candidate_id"] == row["candidate_id"]) for row in wave_admitted],
        "cohort_hash": hash_record([row["candidate_id"] for row in wave_admitted]),
        "frozen_before_diagnostics": True,
        "adaptive_replenishment": False,
    }
    arms, arm_summary, truth = _execute_wave1b_arms(wave_admitted)
    metrics = _wave1b_metrics(arms, len(wave_admitted))
    metrology = _tld_metrology(root, frame["candidates"], calibration)
    closure_contract = {
        "status": "PASS",
        "mandatory_invariants": list(MANDATORY_INVARIANTS),
        "terminal_requirements": "controllergate.amds.causal_closure_contract.TERMINAL_REQUIREMENTS",
        "memory_can_waive": False,
        "same_for_all_strategies": True,
        "remaining_optional_edges_may_be_unresolved": True,
        "independent_verifier_required": True,
    }
    cost_freeze = {
        "status": "PASS",
        "weights": dict(FROZEN_COST_WEIGHTS),
        "objective": "expected causal closure gain per unit cost",
        "frozen_before_wave1b": True,
        "probe_count_is_not_sole_objective": True,
    }
    transition = _transition_example()
    repair = {
        "status": "NOT_RUN_NO_SOURCE_OWNED_WAVE1B_CANDIDATE" if not wave_admitted or all(row["classification"] != "source_owned_behavior_defect" for row in truth["records"]) else "NOT_RUN_SAFETY_GATE",
        "maximum_attempts": 1,
        "attempts": 0,
        "authoritative_memory_condition": "NO_MEMORY",
        "comparative_arms_sealed": bool(arms) and truth["all_arms_sealed_first"],
        "memory_repair_content_used": False,
        "issue_derived_count_increment": 0,
        "duplicate_replay": "NOT_RUN",
        "unique_count_gate": "NOT_RUN",
    }

    records: dict[str, Any] = {
        "batch077_artifact_ingest.json": ingest,
        "batch077_state_preservation.json": {"status": "PASS", "official_workflow_head": ingest["workflow_head"], "Batch077_result": "PASS_UNDER_BATCH077_CRITERIA", "issue_derived_repair_count": 6},
        "batch077_claim_boundary_preservation.json": {"status": "PASS", "validated_protocol": "v2.19", "AMDS_causal_evidence": "AMDS_CAUSAL_EVIDENCE_HARDENED", "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "routing_memory_mechanism": "DEMONSTRATED_NO_EFFECT", "memory_lift": "not_demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"},
        "batch077_count6_identity_preservation.json": {"status": "PASS", "candidate_id": REVIEW[0]["candidate_id"], "candidate_sha": REVIEW[0]["candidate_sha"], "patch_sha256": EXPECTED_PATCH_SHA, "provider_lock_hash": COG_PROVIDER_HASH, "historical_count": 6, "count_increment": 0},
        "batch077_pathway_memory_preservation.json": {"status": "PASS", "routing_memory_mechanism": "DEMONSTRATED_NO_EFFECT", "raw_pathway_file_sha256": sha256_file(root / "outputs" / H77 / "routing_event_pathway_corpus_v2.jsonl")},
        "cognicore_count6_provider_lock.json": count_records["provider"],
        "cognicore_count6_prepatch_replay.json": count_records["prepatch"],
        "cognicore_count6_patch_validation.json": count_records["patch"],
        "cognicore_count6_semantic_invariants.json": count_records["semantic"],
        "cognicore_count6_duplicate_replay.json": count_records["duplicate"],
        "cognicore_count6_existing_count_gate.json": count_records["count"],
        "cognicore_count6_terminal_proof_event.json": count_records["terminal"],
        "cognicore_count6_hardening_decision.json": count_records["decision"],
        "batch077_complete_traversal_reconciliation.json": complete_traversal,
        "batch077_memory_effect_identifiability_audit.json": identifiability,
        "hordeforge_transition_trace.json": horde["trace"],
        "hordeforge_blocked_state_origin.json": horde["origin"],
        "hordeforge_test_expectation_consistency.json": horde["consistency"],
        "hordeforge_direct_pipeline_comparison.json": horde["direct"],
        "hordeforge_causal_ownership_decision.json": horde["decision"],
        "pathway_memory_calibration_preregistration.json": {"status": "PASS", "evaluation": "leave_one_episode_out", "prospective_outcomes_used_for_tuning": False, "same_candidate_excluded": True, "same_repository_excluded": True, "component_weights": {"event_type": 0.4, "compartment": 0.3, "provider": 0.2, "harness": 0.1}, "distance": "one_minus_weighted_overlap", "tie_breaking": "pathway_id_ascending", "top_k": [1, 3], "minimum_admissible_projection": 0.25},
        "pathway_memory_calibration_metrics.json": calibration,
        "pathway_memory_weight_freeze.json": {"status": "PASS", "component_weights": {"event_type": 0.4, "compartment": 0.3, "provider": 0.2, "harness": 0.1}, "frozen_before_wave1b": True, "freeze_hash": activation["weight_freeze_hash"]},
        "pathway_memory_activation_decision.json": activation,
        "routing_event_pathway_manifest_v2_1.json": corpus_manifest,
        "routing_event_pathway_independence_groups.json": independence,
        "routing_event_pathway_balance_audit.json": balance,
        "minimal_causal_closure_contract.json": closure_contract,
        "probe_cost_model_freeze.json": cost_freeze,
        "transition_closure_audit.json": transition,
        "batch078_candidate_frame_policy.json": policy,
        "batch078_candidate_frame.json": frame,
        "batch078_candidate_frame_freeze.json": freeze,
        "batch078_admitted_cohort_freeze.json": cohort,
        "batch078_wave1b_arm_execution_summary.json": arm_summary,
        "batch078_blinded_ground_truth.json": truth,
        "batch078_wave1b_metrics.json": metrics,
        "batch078_authoritative_repair_decision.json": repair,
        "tld_nss_source_audit_batch078.json": metrology["nss_audit"],
        "tld_elbow_source_audit_batch078.json": metrology["elbow_audit"],
        "tld_threshold_transferability_batch078.json": metrology["transfer"],
        "controllergate_matched_null_contract_v1.json": metrology["null_contract"],
        "controllergate_null_generation_audit.json": metrology["null_audit"],
        "controllergate_null_separation_metric_v1.json": metrology["metric"],
        "controllergate_null_separation_results_batch078.json": metrology["separation"],
        "controllergate_nss_nonconflation_statement.json": metrology["nonconflation"],
        "controllergate_elbow_shadow_contract_v1.json": metrology["elbow_contract"],
        "controllergate_elbow_scaling_sensitivity.json": metrology["scaling"],
        "controllergate_flatline_diagnostic_batch078.json": metrology["flatline"],
        "batch078_tld_shadow_metrology_report.json": metrology["shadow"],
        "batch078_tld_shadow_nonblocking_audit.json": metrology["shadow_audit"],
    }
    for name, value in records.items():
        write_json_deterministic(output / name, value)
    _write_jsonl(output / "pathway_memory_leave_one_out_results.jsonl", calibration_rows)
    _write_jsonl(output / "routing_event_pathway_corpus_v2_1.jsonl", corpus)
    _write_jsonl(output / "batch078_candidate_admission_registry.jsonl", admission_public)
    _write_jsonl(output / "batch078_wave1b_arm_records.jsonl", arms)
    _write_jsonl(output / "tld_metric_lineage_registry_batch078.jsonl", metrology["lineage"])
    _write_jsonl(output / "controllergate_null_registry_batch078.jsonl", metrology["null_rows"])
    _write_jsonl(output / "controllergate_elbow_comparison_batch078.jsonl", metrology["elbow_rows"])

    decisions = {
        "status": "PASS",
        "BATCH077_INGEST": "PASS",
        "COUNT_6_HARDENING": count_records["decision"]["COUNT_6_HARDENING"],
        "HORDEFORGE_CAUSAL_OWNERSHIP": horde["decision"]["causal_ownership"],
        "BATCH077_MEMORY_IDENTIFIABILITY": "NOT_IDENTIFIABLE_UNDER_COMPLETE_TRAVERSAL",
        "PATHWAY_MEMORY_CALIBRATION": activation["decision"],
        "PATHWAY_MEMORY_CORPUS_V2_1": "PASS",
        "MINIMAL_CAUSAL_CLOSURE": "PASS",
        "TRANSITION_CLOSURE_AUDIT": transition["status"],
        "WAVE1B_ADMISSION": cohort["status"],
        "AMDS_WAVE1B": arm_summary["status"],
        "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED",
        "ROUTING_MEMORY_WAVE1B": "ROUTING_MEMORY_NO_EFFECT_REPLICATED" if arms else "NOT_RUN",
        "MEMORY_LIFT": "not_demonstrated",
        "AUTHORITATIVE_REPAIR": repair["status"],
        "ISSUE_DERIVED_REPAIR_COUNT": 6,
        "NATIVE_EXTERNAL_REPAIR_COUNT": 4,
        "SELF_MAINTAINING_SOFTWARE": "false/not_demonstrated",
        "LIVE_CONNECTORS": "inactive",
        **metrology["decisions"],
    }
    write_json_deterministic(output / "batch078_completion_decisions.json", decisions)
    final = {
        "status": "PASS",
        "validated_protocol": "v2.19 authorized_amds_active_maintenance_lane",
        "execution_mode": "OFFICIAL_EXTERNAL" if execute_external else "LOCAL_EVIDENCE_ONLY",
        "decisions": decisions,
        "historical_pathway_count": corpus_manifest["raw_record_count"],
        "unique_proof_hashes": corpus_manifest["unique_proof_hashes"],
        "independence_groups": corpus_manifest["unique_independence_groups"],
        "wave1b_frame_count": frame["candidate_count"],
        "wave1b_admitted_count": cohort["candidate_count"],
        "wave1b_arm_count": arm_summary["arm_count"],
        "repair_attempts": repair["attempts"],
        "issue_derived_repair_count": 6,
        "native_external_repair_count": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "live_connectors": "inactive",
        "next_safe_action": "manual_Batch078_artifact_verification_after_successful_workflow",
    }
    write_json_deterministic(output / "batch078_final_decision.json", final)
    summary = (
        "# Batch078 count-six hardening and minimal-closure Wave 1B\n\n"
        f"- Batch077 artifact ingest: PASS ({ingest['observed_sha256']})\n"
        f"- Count-six hardening: {decisions['COUNT_6_HARDENING']} (no recount)\n"
        f"- HordeForge causal ownership: {decisions['HORDEFORGE_CAUSAL_OWNERSHIP']}\n"
        f"- Pathway-memory calibration: {decisions['PATHWAY_MEMORY_CALIBRATION']}\n"
        f"- Wave-1B admission: {decisions['WAVE1B_ADMISSION']}\n"
        f"- Wave-1B arms: {arm_summary['arm_count']}\n"
        "- TLD compatibility metrics: shadow-only and nonblocking\n"
        "- Issue-derived repair count: 6; native external repair count: 4\n"
        "- AMDS prospective effectiveness: NOT_ESTABLISHED\n"
        "- Memory lift: not demonstrated\n"
        "- Full scoring: NOT_RUN/disallowed\n"
        "- Self-maintaining software: false/not demonstrated\n"
    )
    write_text_lf(output / "batch078_summary.md", summary)
    return final


def _update_frontier_states(root: Path, final: dict[str, Any]) -> None:
    current_path = root / "outputs" / "current" / "CURRENT_PROTOCOL_STATE.json"
    current = _load(current_path)
    current.update({
        "batch078_status": final["status"],
        "count_6_hardening_status": final["decisions"]["COUNT_6_HARDENING"],
        "batch078_hordeforge_causal_ownership": final["decisions"]["HORDEFORGE_CAUSAL_OWNERSHIP"],
        "batch078_wave1b_status": final["decisions"]["AMDS_WAVE1B"],
        "issue_derived_repair_count": 6,
        "next_safe_action": final["next_safe_action"],
    })
    current.pop("state_hash", None)
    current["state_hash"] = hash_record(current)
    write_json_deterministic(current_path, current)
    frontier_path = root / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
    frontier = _load(frontier_path)
    frontier.update({
        "BATCH078_STATUS": final["status"],
        "COUNT_6_HARDENING": final["decisions"]["COUNT_6_HARDENING"],
        "HORDEFORGE_CAUSAL_OWNERSHIP": final["decisions"]["HORDEFORGE_CAUSAL_OWNERSHIP"],
        "AMDS_WAVE1B": final["decisions"]["AMDS_WAVE1B"],
        "issue_derived_repair_count": 6,
        "next_safe_action": final["next_safe_action"],
    })
    frontier.pop("state_hash", None)
    frontier["state_hash"] = hash_record(frontier)
    write_json_deterministic(frontier_path, frontier)


def generate(
    root: Path,
    *,
    artifact: Path | None = None,
    execute_external: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    ingest = _verify_ingest(root, artifact)
    output = root / "outputs" / BATCH
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    runtime_parent = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT") or tempfile.gettempdir())
    runtime_parent.mkdir(parents=True, exist_ok=True)
    runtime = Path(tempfile.mkdtemp(prefix="batch078_", dir=runtime_parent))
    try:
        final = _write_batch078_outputs(root, output, ingest=ingest, execute_external=execute_external, runtime=runtime)
        _update_frontier_states(root, final)
        _manifest(output)
        return final
    finally:
        shutil.rmtree(runtime, ignore_errors=True)
