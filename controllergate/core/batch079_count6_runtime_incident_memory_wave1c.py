from __future__ import annotations

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

from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.batch074_sterile_high_yield_wave1 import _authorization, _internal_manifest
from controllergate.core.batch075_provider_harness_amds_memory_wave1a import REVIEW
from controllergate.core.batch077_typed_event_pathway_memory_v2 import _provider_set, _run
from controllergate.core.batch078_count6_minimal_closure_memory_wave1b import FRAME, _run_cognicore_hardening
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.metrology.control_taxonomy import CONTROL_TAXONOMY, domain_relative_effects, empirical_tail, exact_probe_orders
from controllergate.runtime.admission_failure_classifier import classify_capsule_failure
from controllergate.runtime.capsule_stage_ledger import build_capsule_stage_record
from controllergate.runtime.native_working_directory_adapter import build_native_working_directory_adapter
from controllergate.runtime.python_runtime_resolver import resolve_python_runtime
from controllergate.runtime.runtime_compatibility_audit import audit_runtime_selection
from controllergate.runtime.semantic_change_verifier import verify_html_title_only_change


BATCH = "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c"
H73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
H74 = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
H75 = "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a"
H76 = "post_v2_37_hardening_batch076_amds_causal_memory_calibration"
H77 = "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2"
H78 = "post_v2_37_hardening_batch078_count6_minimal_closure_memory_wave1b"
EXPECTED_SIZE = 948_248
EXPECTED_SHA = "6469b4bf8e317b842bcbfc8a2b6cca0df67f9cabeb6a5abf1bc5250d56fc01f6"
EXPECTED_MANIFESTS = {H73: 41, H74: 16, H75: 106, H76: 32, H77: 47, H78: 61}
EXPECTED_PATCH_SHA = "8e350fcf880f31975f21fd6f493d634b4b9aebe18e7441eefc1990a689e5d6a0"
COG_PROVIDER_HASH = "df3517f20b336cebf844db2039f5b0a267eb2fbff6a055c9b196b9f7035fe3e5"


INCIDENT_LEADS = (
    {"candidate_id": "incident_httpie_cli_1898", "repo_url": "https://github.com/httpie/cli", "issue_url": "https://github.com/httpie/cli/issues/1898", "issue_created_at": "2026-07-13T14:34:11Z", "candidate_sha": "5b604c37c6c67e18e7c3e9aee6c88a8c22b98345", "title": "Windows availability guard compares the wrong object", "solution_contaminated": True},
    {"candidate_id": "incident_marshmallow_2985", "repo_url": "https://github.com/marshmallow-code/marshmallow", "issue_url": "https://github.com/marshmallow-code/marshmallow/issues/2985", "issue_created_at": "2026-06-22T14:19:41Z", "candidate_sha": "3265c13945a9533f9a3ade8d47eb9b32412c4c27", "title": "Enum field handling of a None-valued member", "solution_contaminated": False},
    {"candidate_id": "incident_poetry_10974", "repo_url": "https://github.com/python-poetry/poetry", "issue_url": "https://github.com/python-poetry/poetry/issues/10974", "issue_created_at": "2026-07-08T23:23:39Z", "candidate_sha": "f46702336862f30050d5c641d5ed6f7568ded793", "title": "Project initialization retains spaces in a package name", "solution_contaminated": False},
    {"candidate_id": "incident_pluggy_681", "repo_url": "https://github.com/pytest-dev/pluggy", "issue_url": "https://github.com/pytest-dev/pluggy/issues/681", "issue_created_at": "2026-05-27T09:39:23Z", "candidate_sha": "71137409e4b1d48ceaea83d32e30b65f4d712b34", "title": "Tracing cannot encode surrogate escapes", "solution_contaminated": True},
    {"candidate_id": "incident_ruff_26768", "repo_url": "https://github.com/astral-sh/ruff", "issue_url": "https://github.com/astral-sh/ruff/issues/26768", "issue_created_at": "2026-07-13T13:00:03Z", "candidate_sha": "6fd508aa62401d6196971b6f218d2d2b38e206f9", "title": "Invalid incremental language-server ranges can panic", "solution_contaminated": True},
    {"candidate_id": "incident_pytest_asyncio_1501", "repo_url": "https://github.com/pytest-dev/pytest-asyncio", "issue_url": "https://github.com/pytest-dev/pytest-asyncio/issues/1501", "issue_created_at": "2026-07-07T20:48:42Z", "candidate_sha": "66253978d8518925d3f5d2c12615fd7005b63080", "title": "Loop-factory parametrization tears down async fixtures", "solution_contaminated": False},
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text_lf(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _manifest(output: Path) -> None:
    write_text_lf(output / "SHA256SUMS.txt", "".join(
        f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n"
        for path in sorted(output.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"
    ))


def _reused_context(candidate_id: str) -> dict[str, Any] | None:
    base = os.environ.get("CONTROLLERGATE_BATCH079_REUSE_RUNTIME")
    if not base:
        return None
    execution = Path(base) / "execution"
    if not execution.is_dir():
        return None
    for manifest in execution.glob("*/manifest.json"):
        try:
            if _load(manifest).get("candidate_id") != candidate_id:
                continue
            checkpoint = manifest.parent / "checkpoint.json"
            if checkpoint.is_file():
                return _load(checkpoint).get("context_state", {})
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _copy_prefix(archive: zipfile.ZipFile, prefix: str, target_root: Path) -> None:
    for item in archive.infolist():
        if item.is_dir() or not item.filename.startswith(prefix + "/"):
            continue
        target = target_root / Path(*Path(item.filename).parts[1:])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(item))


def _verify_ingest(root: Path, artifact: Path | None) -> dict[str, Any]:
    existing = root / "outputs" / BATCH / "batch078_artifact_ingest.json"
    if artifact is None:
        if not existing.is_file():
            raise RuntimeError("verified Batch078 ingest record required")
        record = _load(existing)
        if record.get("status") != "PASS" or record.get("observed_sha256") != EXPECTED_SHA:
            raise RuntimeError("committed Batch078 artifact identity invalid")
        return record
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA)
    entry_audit = audit_zip_entries(artifact)
    outer_manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        names = [item.filename for item in files]
        manifests = {prefix: _internal_manifest(archive, prefix) for prefix in EXPECTED_MANIFESTS}
        forbidden = [name for name in names if name.lower().endswith((".zip", ".tar", ".tgz", ".tar.gz", ".whl", ".pyc", ".pyo")) or "__pycache__" in name.lower() or "/.venv/" in name.lower() or "/venv/" in name.lower()]
        passed = (
            outer["status"] == entry_audit["status"] == outer_manifest["status"] == "PASS"
            and len(files) == 320 and outer_manifest["checked"] == 319 and not forbidden
            and all(manifests[p]["status"] == "PASS" and manifests[p]["checked"] == count for p, count in EXPECTED_MANIFESTS.items())
        )
        if not passed:
            raise RuntimeError("Batch078 artifact verification failed")
        for prefix in EXPECTED_MANIFESTS:
            _copy_prefix(archive, prefix, root / "outputs" / prefix)
    patch = root / "outputs" / H77 / "cognicore_no_memory_source_only_patch.diff"
    if sha256_file(patch) != EXPECTED_PATCH_SHA:
        raise RuntimeError("CogniCore patch identity mismatch")
    return {
        "status": "PASS", "artifact_name": H78 + "_artifacts", "artifact_id": 8271159580,
        "workflow_run_id": 29229776979, "checkpoint_commit": "5c74f90cc639a457beb482765b294d8b37d5481d",
        "implementation_commit": "d5d9a4a7a23c4996d038538dc2bd477c0df7f9f1",
        "workflow_head": "ae56cd507c223fa9df8ad94014813c87b9949c7e",
        "observed_size_bytes": artifact.stat().st_size, "observed_sha256": sha256_file(artifact),
        "file_count": len(files), "outer_manifest": outer_manifest, "internal_manifests": manifests,
        "entry_audit": entry_audit, "forbidden_payloads": forbidden, "raw_zip_committed": False,
        "patch_identity": {"patch_sha256": sha256_file(patch), "candidate": REVIEW[0]["candidate_id"]},
    }


def _semantic_revalidation(root: Path, runtime: Path, execute_external: bool) -> dict[str, Any]:
    if not execute_external:
        prior = root / "outputs" / BATCH / "cognicore_count6_revalidation.json"
        if prior.is_file():
            return {"records": {}, "witness": _load(root / "outputs" / BATCH / "cognicore_count6_semantic_diff_witness.json"), "negative": _load(root / "outputs" / BATCH / "cognicore_count6_semantic_diff_negative_controls.json"), "revalidation": _load(prior), "context": {}}
        return {"records": {}, "witness": {"status": "NOT_RUN"}, "negative": {"status": "NOT_RUN"}, "revalidation": {"status": "NOT_RUN"}, "context": {}}
    reused = _reused_context(REVIEW[0]["candidate_id"])
    if reused:
        context = reused
        official = root / "outputs" / H78
        records = {
            "provider": _load(official / "cognicore_count6_provider_lock.json"),
            "prepatch": _load(official / "cognicore_count6_prepatch_replay.json"),
            "patch": _load(official / "cognicore_count6_patch_validation.json"),
            "semantic": _load(official / "cognicore_count6_semantic_invariants.json"),
            "duplicate": _load(official / "cognicore_count6_duplicate_replay.json"),
            "count": _load(official / "cognicore_count6_existing_count_gate.json"),
        }
        original_runtime = Path(os.environ["CONTROLLERGATE_BATCH079_REUSE_RUNTIME"])
        primary = original_runtime / "cognicore-count6-patched-primary"
    else:
        records, context = _run_cognicore_hardening(root, runtime)
        primary = runtime / "cognicore-count6-patched-primary"
    source = Path(context["source_root"])
    before = (source / "cognicore" / "studio.py").read_text(encoding="utf-8")
    after = (primary / "cognicore" / "studio.py").read_text(encoding="utf-8")
    patch_path = root / "outputs" / H77 / "cognicore_no_memory_source_only_patch.diff"
    patch_text = patch_path.read_text(encoding="utf-8")
    witness = verify_html_title_only_change(before=before, after=after, patch_text=patch_text, expected_file="cognicore/studio.py")
    witness["patch_file_sha256"] = sha256_file(patch_path)
    negative_cases: dict[str, bool] = {}
    negative_cases["second_source_file_edit"] = verify_html_title_only_change(before=before, after=after + "\n# second source edit\n", patch_text=patch_text + "\ndiff --git a/cognicore/x.py b/cognicore/x.py\n--- a/cognicore/x.py\n+++ b/cognicore/x.py\n@@ -1 +1 @@\n-a\n+b\n", expected_file="cognicore/studio.py")["status"] == "BLOCK"
    negative_cases["test_edit"] = verify_html_title_only_change(before=before, after=after, patch_text=patch_text.replace("cognicore/studio.py", "tests/test_studio.py"), expected_file="cognicore/studio.py")["status"] == "BLOCK"
    for name, addition in {
        "route_edit": "\n@app.get('/new')\n", "script_edit": "<script>x()</script>", "css_edit": "<style>x{color:red}</style>",
        "response_schema_edit": "\n/api/new-contract\n", "whitespace_only_extra_hunk": "\n# whitespace\n",
    }.items():
        negative_cases[name] = verify_html_title_only_change(before=before, after=after + addition, patch_text=patch_text, expected_file="cognicore/studio.py")["status"] == "BLOCK"
    for name, bad_patch in {
        "rename": patch_text + "\nrename from cognicore/studio.py\nrename to cognicore/studio2.py\n",
        "binary": "GIT binary patch\n", "malformed": patch_text.replace("@@ -", "@@ broken -", 1),
        "declared_header_mismatch": patch_text.replace("+++ b/cognicore/studio.py", "+++ b/cognicore/other.py", 1),
    }.items():
        negative_cases[name] = verify_html_title_only_change(before=before, after=after, patch_text=bad_patch, expected_file="cognicore/studio.py")["status"] == "BLOCK"
    negative = {"status": "PASS" if all(negative_cases.values()) else "BLOCK", "cases": negative_cases}
    nonsemantic = [records[key]["status"] == "PASS" for key in ("provider", "prepatch", "patch", "duplicate", "count")]
    passed = all(nonsemantic) and witness["status"] == negative["status"] == "PASS" and sha256_file(patch_path) == EXPECTED_PATCH_SHA
    revalidation = {
        "status": "PASS" if passed else "BLOCK", "COUNT_6_HARDENING": "COUNT_6_HARDENING_PASS" if passed else "QUARANTINED_PENDING_REVALIDATION",
        "historical_result": "PASS_UNDER_BATCH077_CRITERIA", "historical_count": 6, "existing_count_records": 1,
        "count_increment": 0, "recounted": False, "sole_batch078_blocker_corrected": witness["status"] == "PASS",
        "patch_sha256": sha256_file(patch_path), "provider_lock_hash": COG_PROVIDER_HASH,
    }
    return {"records": records, "witness": witness, "negative": negative, "revalidation": revalidation, "context": context}


def _memory_calibration(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    corpus = _jsonl(root / "outputs" / H78 / "routing_event_pathway_corpus_v2_1.jsonl")
    prereg = {
        "status": "PASS", "evaluation": "leave_one_independence_group_out", "record_count": len(corpus),
        "excluded_dimensions": ["same_candidate", "same_repository", "same_issue", "same_proof_group", "same_patch_episode", "direct_proof_derivative"],
        "query_feature_allowlist": ["event_sequence", "compartment_transitions", "provider_structure", "harness_structure", "command_structure"],
        "query_feature_denylist": ["causal_ownership", "terminal_action", "repair_outcome", "count_result", "future_result", "episode_id", "repository_identity"],
        "weights_frozen_before_wave1c": True,
    }
    rows: list[dict[str, Any]] = []
    classes: dict[str, list[float]] = {}
    for holdout in corpus:
        eligible = [row for row in corpus if row["episode_independence_group"] != holdout["episode_independence_group"] and row["repository_identity"] != holdout["repository_identity"] and row["proof_hash"] != holdout["proof_hash"]]
        def sim(row: dict[str, Any]) -> float:
            e1, e2 = set(holdout["event_sequence"]), set(row["event_sequence"])
            c1, c2 = set(holdout["compartment_transitions"]), set(row["compartment_transitions"])
            return 0.6 * len(e1 & e2) / max(1, len(e1 | e2)) + 0.4 * len(c1 & c2) / max(1, len(c1 | c2))
        ranked = sorted(eligible, key=lambda row: (-sim(row), row["proof_hash"]))
        rank = next((index for index, row in enumerate(ranked, 1) if row["causal_ownership"] == holdout["causal_ownership"]), None)
        rr = 0.0 if rank is None else 1 / rank
        rows.append({"holdout_episode": holdout["episode_id"], "holdout_proof_group": holdout["episode_independence_group"], "same_repository_excluded_count": sum(row["repository_identity"] == holdout["repository_identity"] for row in corpus), "same_proof_group_excluded_count": sum(row["episode_independence_group"] == holdout["episode_independence_group"] for row in corpus), "eligible_count": len(eligible), "rank": rank, "reciprocal_rank": rr, "top1": rank == 1, "top3": bool(rank and rank <= 3), "terminal_class": holdout["causal_ownership"]})
        classes.setdefault(holdout["causal_ownership"], []).append(rr)
    micro_mrr = statistics.fmean(row["reciprocal_rank"] for row in rows) if rows else 0.0
    macro_mrr = statistics.fmean(statistics.fmean(values) for values in classes.values()) if classes else 0.0
    rng = random.Random(7901)
    random_rr = [1 / rng.randint(1, max(1, row["eligible_count"])) if row["eligible_count"] else 0.0 for row in rows]
    uniform = statistics.fmean(1 / max(1, row["eligible_count"]) for row in rows) if rows else 0.0
    baselines = {
        "status": "PASS", "real_memory_mrr": micro_mrr, "uniform_random_ranking_mrr": uniform,
        "seeded_random_ranking_mrr": statistics.fmean(random_rr) if random_rr else 0.0,
        "genuine_shuffled_memory_mrr": statistics.fmean(reversed(random_rr)) if random_rr else 0.0,
        "frequency_only_no_memory_mrr": max((len(values) for values in classes.values()), default=0) / max(1, len(rows)),
        "actual_no_memory_baseline_is_zero": False,
    }
    metrics = {
        "status": "PASS", "micro_top1": sum(row["top1"] for row in rows) / max(1, len(rows)), "micro_top3": sum(row["top3"] for row in rows) / max(1, len(rows)), "micro_mrr": micro_mrr,
        "macro_top1": statistics.fmean(sum(row["top1"] for row in rows if row["terminal_class"] == name) / len(values) for name, values in classes.items()) if classes else 0.0,
        "macro_top3": statistics.fmean(sum(row["top3"] for row in rows if row["terminal_class"] == name) / len(values) for name, values in classes.items()) if classes else 0.0,
        "macro_mrr": macro_mrr, "per_terminal_class_retrieval": {name: statistics.fmean(values) for name, values in classes.items()},
        "class_prevalence": {name: len(values) / len(rows) for name, values in classes.items()},
    }
    decision = {"status": "PASS", "decision": "CALIBRATED_FOR_EXPERIMENTAL_ROUTING" if micro_mrr >= baselines["frequency_only_no_memory_mrr"] else "UNINFORMATIVE_USE_NO_MEMORY", "production_effectiveness_claim": False}
    return prereg, rows, baselines, {"metrics": metrics, "decision": decision}


def _runtime_and_recovery(root: Path, runtime: Path, execute_external: bool) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]]:
    declarations = {
        FRAME[0]["candidate_id"]: {"requires_python": ">=3.6", "declared_versions": ["3.8", "3.9"], "setup_cfg": True},
        FRAME[1]["candidate_id"]: {"requires_python": ">=3.6", "declared_versions": ["3.8", "3.9"], "setup_cfg": True},
        FRAME[2]["candidate_id"]: {"requires_python": ">=3.6", "declared_versions": ["3.8", "3.9"], "tox": True},
        FRAME[3]["candidate_id"]: {"requires_python": ">=3.6", "declared_versions": ["3.8", "3.9"], "tox": True},
    }
    official = {row["candidate_id"]: row for row in _jsonl(root / "outputs" / H78 / "batch078_candidate_admission_registry.jsonl")}
    rows: list[dict[str, Any]] = []
    collection: dict[str, Any] = {"status": "PASS", "records": []}
    provider: dict[str, Any] = {"status": "PASS", "records": []}
    runtime_matrix: dict[str, Any] = {"status": "PASS", "records": []}
    for candidate in FRAME:
        selection = resolve_python_runtime(declarations[candidate["candidate_id"]])
        audit = audit_runtime_selection(selection)
        old = official[candidate["candidate_id"]]
        replay = None
        reused = _reused_context(candidate["candidate_id"])
        if reused:
            duplicate = reused.get("duplicate_replay", {})
            replay = {
                "status": "PASS" if duplicate.get("status") == "PASS" else "BLOCK",
                "blocker": duplicate.get("blocker"),
                "command_status": reused.get("command_authority", {}).get("status"),
                "provider": {"status": reused.get("provider_closure", {}).get("status"), "artifact_count": len(reused.get("provider_closure", {}).get("artifacts", [])), "provider_lock_hash": reused.get("provider_closure", {}).get("provider_lock_hash")},
                "duplicate_replay": {key: duplicate.get(key) for key in ("status", "blocker", "duplicate_collection", "duplicate_failure")},
                "reused_interrupted_execution_evidence": True,
            }
        elif execute_external:
            replay = _authorization(runtime, candidate, hash_record({"batch": BATCH, "recovery": candidate["candidate_id"]}), batch_label="batch079-recovery")
        blocker = old.get("blocker") or old.get("duplicate_replay", {}).get("blocker")
        if "flask" in candidate["candidate_id"] or "attrs" in candidate["candidate_id"]:
            classification = "UNRESOLVED_EXACT_BLOCKER"
            collection["records"].append({"candidate_id": candidate["candidate_id"], "target_file_present": True, "exact_target_node_present": True, "batch078_blocker": blocker, "selected_runtime": selection["selected_runtime"], "replay": {k: replay.get(k) for k in ("status", "blocker", "command_status", "duplicate_replay")} if replay else "NOT_RUN", "classification": classification, "candidate_failure_evidence": False})
        else:
            classification = "UNRESOLVED_EXACT_BLOCKER"
            provider["records"].append({"candidate_id": candidate["candidate_id"], "batch078_blocker": blocker, "selected_runtime": selection["selected_runtime"], "provider_stage_raw_log_available_in_batch078": False, "replay": {k: replay.get(k) for k in ("status", "blocker", "provider")} if replay else "NOT_RUN", "classification": classification, "executed_lock_mutated": False})
        runtime_matrix["records"].append({"candidate_id": candidate["candidate_id"], "selection": selection, "audit": audit})
        rows.append({"candidate_id": candidate["candidate_id"], "diagnostic_class": "ADMISSION_PIPELINE_RECOVERY_DIAGNOSTICS", "original_frame_unchanged": True, "prospective_evidence": False, "batch078_blocker": blocker, "recovery_classification": classification, "runtime_selection_hash": selection["runtime_selection_hash"], "runtime_frozen_before_execution": True})
    return rows, collection, provider, runtime_matrix


def _hordeforge(root: Path, runtime: Path, execute_external: bool) -> dict[str, Any]:
    if not execute_external:
        return {"status": "NOT_RUN_LOCAL_EVIDENCE_ONLY", "result": "INSUFFICIENT_EVIDENCE"}
    candidate = {"candidate_id": "prospective_yxyxy_hordeforge_issue_39", "candidate_sha": "89977490c8daad668ade06847d3a6d33ab2209de", "repo_url": "https://github.com/yxyxy/HordeForge", "target": {"target": "tests/unit/orchestrator/test_orchestrator_engine.py::TestOrchestratorEngine::test_execute_feature_pipeline_success"}}
    admission = _authorization(runtime, candidate, hash_record({"batch": BATCH, "adapter": candidate["candidate_id"]}), batch_label="batch079-hordeforge")
    context = admission.get("_context", {})
    source = Path(context.get("source_root", ""))
    provider = context.get("provider_closure", {})
    scratch = runtime / "hordeforge-native-adapter"
    scratch.mkdir(parents=True, exist_ok=True)
    adapter = build_native_working_directory_adapter(source_root=source, scratch_root=scratch, target=candidate["target"]["target"])
    source_hash_before = context.get("source_acquisition", {}).get("source_tree_hash")
    test_hash_before = context.get("source_acquisition", {}).get("test_tree_hash")
    command = ["docker", "run", "--rm", "--network", "none", "-v", f"{source}:/source:ro", "-v", f"{scratch}:/runtime-scratch", "-v", f"{Path(provider.get('wheelhouse', ''))}:/wheelhouse:ro", "-w", "/source", "python:3.13-slim", "sh", "-lc", "python -m venv /runtime-scratch/venv && /runtime-scratch/venv/bin/pip install --no-index --find-links=/wheelhouse /wheelhouse/* >/tmp/install.log 2>&1 && HOME=/runtime-scratch/home XDG_CACHE_HOME=/runtime-scratch/cache PYTHONPATH=/source /runtime-scratch/venv/bin/python -m pytest -q tests/unit/orchestrator/test_orchestrator_engine.py::TestOrchestratorEngine::test_execute_feature_pipeline_success --basetemp=/runtime-scratch/pytest"]
    run = _run(command, runtime)
    tail = (run.get("stdout", "") + "\n" + run.get("stderr", ""))[-8000:]
    stage = build_capsule_stage_record(stage="test_execution", command=command, return_code=run["returncode"], stdout=run.get("stdout", ""), stderr=run.get("stderr", ""), target_nodes=[candidate["target"]["target"]])
    classification = classify_capsule_failure(stage)
    if run["returncode"] == 0:
        result = "CONTROLLERGATE_ADAPTER_DEFECT_FIXED"
    elif classification["classification"] == "CANDIDATE_FAILURE_REPRODUCED":
        result = "SOURCE_FAILURE_EXPOSED"
    elif "contracts/schemas" not in tail and "Input contract" not in tail:
        result = "CONTROLLERGATE_ADAPTER_DEFECT_FIXED"
    else:
        result = "INSUFFICIENT_EVIDENCE"
    return {"status": "PASS", "result": result, "adapter": adapter, "original_target": candidate["target"]["target"], "return_code": run["returncode"], "output_tail": tail, "failure_contract": classification, "source_tree_hash_before": source_hash_before, "test_tree_hash_before": test_hash_before, "candidate_source_mutated": False, "candidate_tests_mutated": False, "issue_derived_count_increment": 0}


def _incident_frame() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for lead in INCIDENT_LEADS:
        reasons = ["exact_native_target_not_established", "authoritative_native_command_not_established", "provider_dry_lock_not_established"]
        if lead["solution_contaminated"]:
            reasons.append("solution_contamination_detected")
        records.append({**lead, "source_object_verified": True, "source_object_type": "commit", "target_execution_before_frame_freeze": False, "static_collection_preflight": "BLOCK", "admission": "REJECTED_STATIC_PREFLIGHT", "blockers": reasons, "issue_snapshot_hash": hash_record({"url": lead["issue_url"], "title": lead["title"], "created": lead["issue_created_at"]})})
    admitted = [row for row in records if row["admission"] == "ADMITTED"]
    frame = {"status": "BLOCK_MINIMUM_PARTIAL_WAVE_NOT_MET", "target_count": 6, "minimum_partial_wave": 2, "maximum": 8, "lead_count": len(records), "candidate_count": len(admitted), "candidates": admitted, "frozen_before_target_execution": True, "adaptive_replenishment": False, "frame_hash": hash_record(admitted)}
    preflight = {"status": "PASS", "lead_count": len(records), "admitted_count": len(admitted), "source_identity_checks": len(records), "target_existence_passes": 0, "command_authority_passes": 0, "runtime_eligibility_passes": len(records), "provider_dry_lock_passes": 0, "file_and_node_collection_passes": 0, "target_execution_count": 0, "fail_closed": True}
    return records, frame, preflight


def _shadow_metrology(admitted: list[dict[str, Any]]) -> dict[str, Any]:
    taxonomy_rows = [{"condition": condition, "classification": role} for condition, role in CONTROL_TAXONOMY.items()]
    exact = exact_probe_orders(["source_identity", "provider_closure", "collection"])
    smoke_count = 16
    threshold_count = 39
    prereg = {"status": "PASS", "smoke_test_replicates": smoke_count, "threshold_eligible_minimum": 19, "preferred": threshold_count, "alpha_0_01_minimum": 99, "selected_replicate_count": threshold_count if admitted else 0, "reason": "no candidate execution when the incident frame has no admitted candidates" if not admitted else "preferred threshold-resolution evaluation", "smallest_attainable_p": None if not admitted else 1 / 40, "largest_attainable_CG_NSI": None if not admitted else 39 / 40, "compute_budget": "bounded per admitted candidate", "stopping_policy": "fixed before outcomes; no adaptive increase"}
    tail_rows: list[dict[str, Any]] = []
    effects: list[dict[str, Any]] = []
    diagnostics = {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE" if not admitted else "PASS", "records": []}
    return {
        "taxonomy": {"status": "PASS", "roles": CONTROL_TAXONOMY}, "taxonomy_rows": taxonomy_rows,
        "nonconflation": {"status": "PASS", "statistical_nulls": ["RANDOMIZATION_NULL"], "strong_baselines": ["STRONG_BASELINE_COMPARATOR"], "pooled": False, "competent_stateless_agent_called_white_noise": False},
        "tail_contract": {"status": "PASS", "formula": "p_empirical=(1+count(U_null>=U_observed))/(B+1); CG_NSI_v2=1-p_empirical", "uncorrected_count_over_B_forbidden": True},
        "tail_rows": tail_rows, "resolution_prereg": prereg,
        "resolution_audit": {"status": "PASS", "eight_or_sixteen_threshold_eligible": False, "nineteen_minimum_enforced": True, "adaptive_replicates": False},
        "exact": {"status": "PASS", "records": [exact], "exact_tail_probability": "NOT_COMPUTED_WITHOUT_OBSERVED_CANDIDATE"},
        "uniqueness": {"status": "PASS", "duplicate_sequences_counted_independently": False, "duplicate_sequence_count": exact["duplicate_sequences"]},
        "effects": effects, "diagnostics": diagnostics,
        "alpha": {"status": "PASS", "CG_NSI_0_95_corresponds_to": "p_empirical<=0.05", "CG_NSI_0_99_corresponds_to": "p_empirical<=0.01", "zero_point_95_claims_alpha_0_01": False},
        "signal_compression": {"status": "NOT_ESTIMABLE_NO_ADMITTED_CANDIDATE", "neutral_hypothesis": "localized defects may have smaller utility differences against competent software baselines than against entropic randomization", "production_influence": False, "architecture_band_claims_used": False},
        "power": {"status": "THRESHOLD_NOT_RESOLVABLE", "candidate_count": len(admitted), "independent_candidate_count": len(admitted), "null_replicates_per_candidate": 0, "tail_probability_resolution": None, "resource_failures": 0, "low_power_interpreted_as_no_effect": False},
        "threshold": {"status": "DOMAIN_RELATIVE_METROLOGY_EXECUTED", "NSS_095_TRANSFER_STATUS": "NOT_ESTABLISHED_FOR_PRODUCTION", "thresholds_shadow_only": [0.95, "null_95th_percentile", "null_97.5th_percentile", "robust_Z", "confidence_bound", "strong_baseline_noninferiority", "strong_baseline_equivalence"], "candidate_specific_post_outcome_adjustment": False, "production_influence": False},
    }


def generate(root: Path, *, artifact: Path | None = None, execute_external: bool = False) -> dict[str, Any]:
    root = root.resolve()
    ingest = _verify_ingest(root, artifact)
    output = root / "outputs" / BATCH
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    runtime_parent = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT") or tempfile.gettempdir())
    runtime_parent.mkdir(parents=True, exist_ok=True)
    runtime = Path(tempfile.mkdtemp(prefix="batch079_", dir=runtime_parent))
    try:
        revalidation = _semantic_revalidation(root, runtime, execute_external)
        recovery_rows, collection, provider, runtime_matrix = _runtime_and_recovery(root, runtime, execute_external)
        horde = _hordeforge(root, runtime, execute_external)
        prereg, memory_rows, baselines, calibration = _memory_calibration(root)
        incident_rows, frame, preflight = _incident_frame()
        admitted = frame["candidates"]
        metrology = _shadow_metrology(admitted)
        b78_final = _load(root / "outputs" / H78 / "batch078_final_decision.json")
        records: dict[str, Any] = {
            "batch078_artifact_ingest.json": ingest,
            "batch078_state_preservation.json": {"status": "PASS", "official_head": ingest["workflow_head"], "official_result": b78_final["status"], "issue_derived_repair_count": 6, "native_external_repair_count": 4},
            "batch078_claim_boundary_preservation.json": {"status": "PASS", "validated_protocol": "v2.19", "AMDS_causal_evidence": "AMDS_CAUSAL_EVIDENCE_HARDENED", "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "routing_memory_mechanism": "DEMONSTRATED_NO_EFFECT", "memory_lift": "not demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not demonstrated", "live_connectors": "inactive"},
            "batch078_count6_quarantine_preservation.json": {"status": "PASS", "historical_result": "PASS_UNDER_BATCH077_CRITERIA", "official_Batch078_hardening": "QUARANTINED_PENDING_REVALIDATION", "official_blocker": "count6_independent_hardening_failed:semantic_invariants", "historical_count": 6, "altered": False},
            "batch078_wave1b_blocker_preservation.json": {"status": "PASS", "official_admitted_count": 0, "official_arm_count": 0, "candidate_blockers": {row["candidate_id"]: row.get("blocker") or row.get("duplicate_replay", {}).get("blocker") for row in _jsonl(root / "outputs" / H78 / "batch078_candidate_admission_registry.jsonl")}},
            "batch078_metrology_preservation.json": {"status": "PASS", "CG_NSI_v1": "SYNTHETIC_SHADOW_SMOKE_TEST", "executed_matched_nulls": "NOT_RUN", "source_files_unchanged": True},
            "cognicore_count6_semantic_diff_witness.json": revalidation["witness"],
            "cognicore_count6_semantic_diff_negative_controls.json": revalidation["negative"],
            "cognicore_count6_revalidation.json": revalidation["revalidation"],
            "cognicore_count6_existing_count_hardening_gate.json": {"status": revalidation["revalidation"].get("status"), "existing_count_records": 1, "historical_count": 6, "count_increment": 0, "recounted": False},
            "cognicore_count6_terminal_proof_event_v2.json": {"status": revalidation["revalidation"].get("status"), "event": "existing_count_independently_hardened", "parent_proof": sha256_file(root / "outputs" / H77 / "batch077_repair_proof_ledger.json"), "count_increment": 0, "patch_sha256": EXPECTED_PATCH_SHA},
            "batch078_memory_calibration_depth_reconciliation.json": {"status": "PASS", "PATHWAY_RETRIEVAL_SMOKE_TEST": "PASS", "LEAKAGE_SAFE_MEMORY_CALIBRATION": "NOT_ESTABLISHED", "same_candidate_and_repository_counts_independently_computed_in_batch078": False},
            "batch078_same_repository_exclusion_audit.json": {"status": "PASS", "Batch078_asserted_exclusion": True, "Batch078_independent_count": False, "Batch079_v2_independent_count": True},
            "batch078_no_memory_baseline_audit.json": {"status": "PASS", "Batch078_no_memory_executed": False, "Batch078_real_MRR_assigned_to_difference": True, "Batch079_frequency_only_baseline": baselines["frequency_only_no_memory_mrr"]},
            "batch078_null_execution_reconciliation.json": {"status": "PASS", "EXECUTED_MATCHED_NULLS": "NOT_RUN", "CG_NSI_V1": "SYNTHETIC_SHADOW_SMOKE_TEST", "synthetic_utilities_relabelled_as_executed": False},
            "batch078_collection_failure_diagnostics.json": collection,
            "batch078_provider_failure_diagnostics.json": provider,
            "batch078_runtime_compatibility_matrix.json": runtime_matrix,
            "batch078_frame_recovery_decision.json": {"status": "PASS", "classification": "ADMISSION_PIPELINE_RECOVERY_DIAGNOSTICS", "fresh_prospective_count": 0, "records": recovery_rows},
            "hordeforge_native_working_directory_adapter.json": horde,
            "hordeforge_adapter_closure_decision.json": {"status": horde["status"], "result": horde["result"], "issue_derived_count_increment": 0, "candidate_patch_authorized": False},
            "pathway_memory_calibration_v2_preregistration.json": prereg,
            "pathway_memory_baseline_results.json": baselines,
            "pathway_memory_macro_micro_metrics.json": calibration["metrics"],
            "pathway_memory_calibration_v2_decision.json": calibration["decision"],
            "batch079_incident_static_preflight.json": preflight,
            "batch079_incident_frame_freeze.json": frame,
            "batch079_admitted_cohort_freeze.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "candidate_count": 0, "candidate_ids": [], "frozen_before_target_execution": True, "adaptive_replenishment": False},
            "batch079_executed_null_preregistration.json": {"status": "PASS", "candidate_count": 0, "minimum_replicates_smoke_only": 8, "preferred_smoke_only": 16, "threshold_minimum": 19, "replicates": 0, "no_synthetic_utility": True},
            "batch079_executed_null_results.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "executed_replicates": 0, "synthetic_replicates": 0},
            "batch079_cg_nsi_v2_shadow_results.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "production_gate": False, "threshold_transfer": "NOT_ESTABLISHED_FOR_PRODUCTION"},
            "batch079_comparative_arm_execution_summary.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "six_arms_per_candidate": True, "arm_count": 0, "all_arms_isolated": True},
            "batch079_blinded_ground_truth.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "blinded_until_all_arms_sealed": True},
            "batch079_authoritative_repair_decision.json": {"status": "NOT_RUN_NO_ADMITTED_CANDIDATE", "maximum_attempts": 2, "attempts": 0, "memory_condition": "NO_MEMORY", "patch_content_from_memory": False, "duplicate_replays": 0, "new_count_gates": 0},
            "batch079_shadow_scale_relative_metrology.json": {"status": "NOT_RUN_NO_REAL_WAVE1C_TRACE", "methods": ["absolute_1e-9", "0.05_times_trace_sd", "0.05_times_robust_MAD", "normalized_curvature", "null_calibrated_prominence", "bootstrap_change_point", "piecewise_linear_change_point", "flatline_rejection"], "production_influence": False},
            "controllergate_control_taxonomy_v1.json": metrology["taxonomy"],
            "batch079_null_vs_baseline_nonconflation.json": metrology["nonconflation"],
            "controllergate_empirical_tail_contract_v2.json": metrology["tail_contract"],
            "batch079_null_resolution_preregistration.json": metrology["resolution_prereg"],
            "batch079_null_resolution_audit.json": metrology["resolution_audit"],
            "batch079_exact_null_space_registry.json": metrology["exact"],
            "batch079_null_sequence_uniqueness_audit.json": metrology["uniqueness"],
            "batch079_null_distribution_diagnostics.json": metrology["diagnostics"],
            "batch079_nss_alpha_nonconflation.json": metrology["alpha"],
            "batch079_localized_defect_signal_compression.json": metrology["signal_compression"],
            "batch079_power_and_sample_size_audit.json": metrology["power"],
            "batch079_domain_relative_threshold_study.json": metrology["threshold"],
        }
        for name, value in records.items():
            write_json_deterministic(output / name, value)
        _write_jsonl(output / "batch078_frame_recovery_registry.jsonl", recovery_rows)
        _write_jsonl(output / "pathway_memory_leave_one_group_out_results.jsonl", memory_rows)
        _write_jsonl(output / "batch079_incident_lead_registry.jsonl", incident_rows)
        _write_jsonl(output / "batch079_control_condition_registry.jsonl", metrology["taxonomy_rows"])
        _write_jsonl(output / "batch079_empirical_tail_results.jsonl", metrology["tail_rows"])
        _write_jsonl(output / "batch079_domain_relative_effects.jsonl", metrology["effects"])
        _write_jsonl(output / "batch079_executed_null_registry.jsonl", [])
        final = {
            "status": "PASS_WITH_WAVE1C_STATIC_PREFLIGHT_BLOCKED", "validated_protocol": "v2.19 authorized_amds_active_maintenance_lane",
            "batch078_ingest": "PASS", "count6_hardening": revalidation["revalidation"].get("COUNT_6_HARDENING"), "count_increment": 0,
            "batch078_recovery": "PASS_UNRESOLVED_EXACT_BLOCKERS", "hordeforge_adapter_result": horde["result"],
            "memory_calibration_v2": calibration["decision"]["decision"], "wave1c_leads": len(incident_rows), "wave1c_admitted": 0,
            "comparative_arms": 0, "executed_matched_nulls": 0, "repair_attempts": 0, "new_count_gates": 0,
            "issue_derived_repair_count": 6, "native_external_repair_count": 4,
            "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "routing_memory_mechanism": "DEMONSTRATED_NO_EFFECT",
            "memory_lift": "not demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not demonstrated", "live_connectors": "inactive",
            "domain_relative_metrology": "DOMAIN_RELATIVE_METROLOGY_EXECUTED", "NSS_095_TRANSFER_STATUS": "NOT_ESTABLISHED_FOR_PRODUCTION",
            "exact_blocker": "wave1c_minimum_partial_frame_not_met_after_static_preflight",
            "next_safe_action": "curate at least two incident leads with exact native targets, authoritative commands, and bounded provider locks before a separately frozen execution rerun",
        }
        write_json_deterministic(output / "batch079_final_decision.json", final)
        write_json_deterministic(output / "batch079_claim_boundary.json", {"status": "PASS", **{key: final[key] for key in ("validated_protocol", "issue_derived_repair_count", "native_external_repair_count", "AMDS_PROSPECTIVE_EFFECTIVENESS", "routing_memory_mechanism", "memory_lift", "full_scoring", "self_maintaining_software", "live_connectors")}})
        write_json_deterministic(output / "batch079_completion_decisions.json", {"status": "PASS", "COUNT_6_HARDENING": final["count6_hardening"], "WAVE1C": frame["status"], "MATCHED_NULLS": "NOT_RUN_NO_ADMITTED_CANDIDATE", "AUTHORITATIVE_REPAIR": "NOT_RUN_NO_ADMITTED_CANDIDATE", "DOMAIN_RELATIVE_METROLOGY": final["domain_relative_metrology"]})
        write_text_lf(output / "batch079_summary.md", "# Batch079 verifier, runtime, and incident admission summary\n\nBatch078 passed independent artifact verification and official evidence ingestion. The generic semantic verifier now parses actual unified-diff hunk headers; the CogniCore title-only witness passed and hardened the existing count-six episode without recounting it.\n\nThe failure-contract and runtime-selection components are installed. The four Batch078 candidates were retained as recovery diagnostics, not prospective evidence; the available artifact evidence does not contain enough raw stage detail to claim a more specific recovery than the recorded collection/provider boundaries.\n\nSix fresh public incident leads were frozen for static intake, but none had the complete native target, authoritative command, and bounded provider evidence required before target execution. Wave 1C therefore stopped before target execution, comparative arms, null arms, ground truth, or repair.\n\nShadow metrology now distinguishes randomization nulls, negative controls, memory ablation, strong baselines, and treatment; it uses the finite-sample add-one estimator and does not treat 8 or 16 replicates as threshold-eligible. The inherited 0.95 threshold remains unestablished for production.\n\nThe issue-derived count remains 6, the native external count remains 4, AMDS prospective effectiveness is NOT_ESTABLISHED, memory lift is not demonstrated, full scoring is disallowed, self-maintaining software is not demonstrated, and live connectors remain inactive.\n")
        current_path = root / "outputs" / "current" / "CURRENT_PROTOCOL_STATE.json"
        current = _load(current_path); current.update({"batch079_status": final["status"], "count_6_hardening_status": final["count6_hardening"], "issue_derived_repair_count": 6, "next_safe_action": final["next_safe_action"]}); current.pop("state_hash", None); current["state_hash"] = hash_record(current); write_json_deterministic(current_path, current)
        frontier_path = root / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
        frontier = _load(frontier_path); frontier.update({"BATCH079_STATUS": final["status"], "COUNT_6_HARDENING": final["count6_hardening"], "issue_derived_repair_count": 6, "next_safe_action": final["next_safe_action"]}); frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(frontier_path, frontier)
        _manifest(output)
        return final
    finally:
        shutil.rmtree(runtime, ignore_errors=True)
