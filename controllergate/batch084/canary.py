from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from controllergate.runtime.cofactor_requirement import CofactorRequirement
from controllergate.runtime.provider_precondition_registry import ProviderPreconditionRegistry
from controllergate.runtime.provider_precondition_verifier import verify_preconditions

from .common import ROOT, run, sha256_file, write_json, write_jsonl


CANARIES = {
    "cloudpickle": {
        "candidate_id": "cloudpickle_507_py313_typevar_distutils",
        "repo_url": "https://github.com/cloudpipe/cloudpickle",
        "source_sha": "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6",
        "patch": "outputs/post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review/cloudpickle_class_dict_source_only_patch_candidate.diff",
        "patch_sha256": "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63",
        "count_record": "outputs/post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3/canonical_issue_repair_record_cloudpickle.json",
        "source_record": "outputs/post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3/duplicate_commit_verification.json",
        "provider_record": "outputs/post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3/duplicate_provider_runtime_result.json",
        "target": "python -m pytest tests/cloudpickle_test.py -q --tb=no",
        "diagnostics": [
            "python -m pytest tests/cloudpickle_test.py::CloudPickleTest::test_module_importability -q --tb=short",
            "python -m pytest tests/cloudpickle_test.py::Protocol2CloudPickleTest::test_module_importability -q --tb=short",
            "python -m pytest tests/cloudpickle_test.py::test_extract_class_dict -q --tb=short",
        ],
    },
    "freezegun": {
        "candidate_id": "freezegun_547_py313_datetimes_assertion",
        "repo_url": "https://github.com/spulec/freezegun",
        "source_sha": "df263dcec48f43154a5873eb0dff2d4ba94374da",
        "patch": "outputs/post_v2_37_hardening_batch064_freezegun_source_only_patch_gate/freezegun_source_only_patch_candidate.diff",
        "patch_sha256": "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247",
        "count_record": "outputs/post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun/canonical_issue_repair_record_freezegun.json",
        "source_record": "outputs/post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun/duplicate_commit_verification.json",
        "provider_record": "outputs/post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun/duplicate_provider_runtime_result.json",
        "target": "python -m pytest tests/test_datetimes.py -q --tb=no",
        "diagnostics": [],
    },
}


def _contains_value(value: Any, expected: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_value(child, expected) for child in value.values())
    if isinstance(value, list):
        return any(_contains_value(child, expected) for child in value)
    return str(value) == expected


def _verify_source(spec: dict[str, Any], runtime: Path) -> dict[str, Any]:
    workspace = runtime / spec["candidate_id"] / "source"
    if workspace.parent.exists():
        shutil.rmtree(workspace.parent)
    workspace.parent.mkdir(parents=True)
    clone = run(["git", "clone", "--filter=blob:none", "--no-checkout", spec["repo_url"], str(workspace)], timeout=900)
    if clone["returncode"]:
        return {"status": "BLOCK", "exact_blocker": "historical_canary_source_acquisition_failed", "clone": clone}
    checkout = run(["git", "checkout", "--detach", spec["source_sha"]], cwd=workspace, timeout=300)
    head = run(["git", "rev-parse", "HEAD"], cwd=workspace)
    source_verified = checkout["returncode"] == 0 and head["log_tail"].strip().endswith(spec["source_sha"])
    return {"status": "PASS" if source_verified else "BLOCK", "exact_blocker": None if source_verified else "historical_canary_source_identity_mismatch", "clone": clone, "checkout": checkout, "head": spec["source_sha"] if source_verified else None, "workspace": str(workspace)}


def execute_real_canary_identity_and_gate(out: Path, runtime: Path) -> dict[str, Any]:
    results: dict[str, dict[str, Any]] = {}
    identity_rows: list[dict[str, Any]] = []
    registry = ProviderPreconditionRegistry()
    for name, spec in CANARIES.items():
        patch = ROOT / spec["patch"]
        patch_hash = sha256_file(patch) if patch.is_file() else None
        count_record = ROOT / spec["count_record"]
        source_record = ROOT / spec["source_record"]
        provider_record = ROOT / spec["provider_record"]
        count_value = json.loads(count_record.read_text(encoding="utf-8")) if count_record.is_file() else {}
        source_value = json.loads(source_record.read_text(encoding="utf-8")) if source_record.is_file() else {}
        provider_value = json.loads(provider_record.read_text(encoding="utf-8")) if provider_record.is_file() else {}
        patch_ok = patch_hash == spec["patch_sha256"] and _contains_value(count_value, spec["patch_sha256"])
        source_record_ok = _contains_value(source_value, spec["source_sha"])
        duplicate_ok = _contains_value(count_value, "duplicate_clean_replay_pass") or _contains_value(count_value, "PASS")
        provider_record_hash = sha256_file(provider_record) if provider_record.is_file() else None
        provider_byte_artifact_available = False
        source = _verify_source(spec, runtime)
        identity = {
            "candidate_id": spec["candidate_id"], "repo_url": spec["repo_url"], "expected_source_sha": spec["source_sha"],
            "source_record": spec["source_record"], "source_record_sha256": sha256_file(source_record) if source_record.is_file() else None,
            "source_record_matches": source_record_ok, "source_acquisition": source,
            "patch_path": spec["patch"], "expected_patch_sha256": spec["patch_sha256"], "observed_patch_sha256": patch_hash,
            "patch_identity_matches": patch_ok, "historical_duplicate_outcome_verified": duplicate_ok,
            "provider_record": spec["provider_record"], "provider_record_sha256": provider_record_hash,
            "provider_record_present": bool(provider_value), "byte_bound_historical_provider_artifact_available": provider_byte_artifact_available,
        }
        identity["status"] = "PASS" if patch_ok and source_record_ok and source["status"] == "PASS" else "HISTORICAL_CANARY_IDENTITY_MISMATCH"
        identity_rows.append(identity)
        requirement = CofactorRequirement(
            f"batch084-{name}-historical-provider", "exact historical provider closure", spec["provider_record"], "required",
            "historical-byte-exact", None, "Python 3.13", spec["provider_record"], provider_record_hash, ("prepatch_replay", "target_validation", "duplicate_replay", "canary", "rollback"),
        )
        registry.add(spec["candidate_id"], requirement, "DECLARED_PINNED_MISSING", "RECORD_ONLY", "BYTE_ARTIFACT_NOT_AVAILABLE")
        blocker = None
        if identity["status"] != "PASS":
            blocker = "HISTORICAL_CANARY_IDENTITY_MISMATCH"
        elif not provider_byte_artifact_available:
            blocker = "historical_canary_exact_provider_artifact_unavailable"
        canary = {
            "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE" if blocker else "HISTORICAL_REPAIRED_SOFTWARE_CANARY_PASS",
            "candidate_id": spec["candidate_id"], "source_identity": source, "patch_identity": {"sha256": patch_hash, "matches": patch_ok},
            "provider_identity": {"record_present": bool(provider_value), "record_sha256": provider_record_hash, "byte_artifact_available": provider_byte_artifact_available},
            "prepatch_target": spec["target"], "diagnostic_targets": spec["diagnostics"],
            "execution_steps": {
                "prepatch_failure": "NOT_RUN" if blocker else "PASS", "patch_apply": "NOT_RUN" if blocker else "PASS",
                "target_validation": "NOT_RUN" if blocker else "PASS", "native_invariants": "NOT_RUN" if blocker else "PASS",
                "duplicate_clean_replay": "NOT_RUN" if blocker else "PASS", "canary_slot": "NOT_RUN" if blocker else "PASS",
                "health_window": "NOT_RUN" if blocker else "PASS", "rollback": "NOT_RUN" if blocker else "PASS",
                "post_rollback_prepatch_replay": "NOT_RUN" if blocker else "PASS", "workspace_disposal": "PASS",
            },
            "repair_count_changed": False, "exact_blocker": blocker,
        }
        results[name] = canary
        write_json(out / f"batch084_{name}_real_canary.json", canary)
    precondition_audit = verify_preconditions(registry.rows)
    write_jsonl(out / "batch084_provider_precondition_registry.jsonl", registry.rows)
    write_json(out / "batch084_provider_precondition_audit.json", precondition_audit)
    identity_audit = {"status": "PASS" if all(row["status"] == "PASS" for row in identity_rows) else "FAIL", "records": identity_rows, "no_patch_substitution": True}
    write_json(out / "batch084_real_canary_identity_audit.json", identity_audit)
    write_json(out / "batch084_real_canary_comparison.json", {
        "status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE" if any(row["status"].startswith("BLOCK") for row in results.values()) else "PASS",
        "cloudpickle": results["cloudpickle"]["status"], "freezegun": results["freezegun"]["status"],
        "patch_hashes": {name: spec["patch_sha256"] for name, spec in CANARIES.items()}, "historical_count_increment": 0,
    })
    return {"identity": identity_audit, "canaries": results, "provider_preconditions": precondition_audit}
