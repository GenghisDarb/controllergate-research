#!/usr/bin/env python3
"""Audit v2.18 Origin Licensing / Source Acquisition Lane evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "outputs" / "v2_18_origin_licensing_source_acquisition"
CAMPAIGN_ID = "v2_18_origin_licensing_source_acquisition"
EXPECTED_REVISION = "e21a31162f4c54be693d8ca8260e42393b39abd3"
REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "source_acquisition_audit.json",
    "workspace_equivalence_summary.json",
    "workspace_provenance.json",
    "workspace_purity_report.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v1.json",
    "baseline_registry_snapshot_v2_18.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "isolated_execution_log.txt",
    "patch_candidate_safety_check.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_18.json",
    "SHA256SUMS.txt",
]
OPTIONAL_PATCH_FILES = {
    "memory_enabled_source_only_repair_patch.diff",
    "no_memory_source_only_repair_patch.diff",
    "target_validation_log.txt",
    "duplicate_replay_summary.json",
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing JSON: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected object: {path}")
        return {}
    return value


def verify_manifest(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file():
        return [f"missing manifest: {manifest}"], 0
    seen: set[str] = set()
    checked = 0
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            errors.append(f"SHA256SUMS.txt:{line_no}: malformed entry")
            continue
        expected, rel = parts
        pure = PurePosixPath(rel)
        if rel.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
            errors.append(f"SHA256SUMS.txt:{line_no}: unsafe path {rel}")
            continue
        path = root.joinpath(*pure.parts)
        seen.add(rel)
        if not path.is_file():
            errors.append(f"SHA256SUMS.txt:{line_no}: missing file {rel}")
            continue
        if sha256_path(path) != expected:
            errors.append(f"SHA256SUMS.txt:{line_no}: hash mismatch {rel}")
        checked += 1
    expected_files = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"}
    for rel in sorted(expected_files - seen):
        errors.append(f"manifest missing {rel}")
    for rel in sorted(seen - expected_files):
        errors.append(f"manifest contains extra {rel}")
    return errors, checked


def is_outside_repo(path_text: str | None) -> bool:
    if not path_text:
        return False
    path = Path(path_text)
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    repo = REPO_ROOT.resolve()
    return resolved != repo and repo not in resolved.parents


def audit_ledger(root: Path, ledger: dict[str, Any], errors: list[str]) -> None:
    previous = None
    rollback_seen = False
    failure_seen = False
    for index, entry in enumerate(ledger.get("ledger_entries") or []):
        material = {k: v for k, v in entry.items() if k != "entry_hash"}
        if entry.get("index") != index:
            errors.append(f"ledger index mismatch at {index}")
        if entry.get("previous_entry_hash") != previous:
            errors.append(f"ledger previous hash mismatch at {index}")
        if canonical_sha(material) != entry.get("entry_hash"):
            errors.append(f"ledger entry hash mismatch at {index}")
        rel = entry.get("path")
        if rel:
            path = root / str(rel)
            if not path.is_file():
                errors.append(f"ledger target missing: {rel}")
            elif sha256_path(path) != entry.get("sha256"):
                errors.append(f"ledger target hash mismatch: {rel}")
        if str(entry.get("action", "")).endswith("failed") or entry.get("result") == "block":
            failure_seen = True
        if entry.get("action") == "rollback_workspace_and_stop":
            rollback_seen = entry.get("workspace_cleanup_confirmed") is True and entry.get("rollback_target_entry_index") is not None
        previous = entry.get("entry_hash")
    if ledger.get("ledger_tip") != previous:
        errors.append("ledger tip mismatch")
    if failure_seen and not rollback_seen:
        errors.append("blocked acquisition/materialization lacks rollback entry")
    if ledger.get("ghost_state_count") != 0:
        errors.append("ledger reports ghost states")


def audit_claims(results: dict[str, Any], claims: dict[str, Any], errors: list[str]) -> None:
    if results.get("candidate_scope") != ["PySnooper:1"] or claims.get("candidate_scope") != ["PySnooper:1"]:
        errors.append("v2.18 scope must be PySnooper:1 only")
    if results.get("pysnooper2_pursued") is not False or claims.get("pysnooper2_pursued") is not False:
        errors.append("PySnooper:2 was pursued")
    if results.get("current_protocol_version") != "v2.13" or claims.get("current_protocol_version") != "v2.13":
        errors.append("current protocol changed")
    if claims.get("v2_18_promoted_to_current") is not False:
        errors.append("v2.18 promoted to current")
    if results.get("full_scoring") != "NOT_RUN" or results.get("full_scoring_allowed") is not False:
        errors.append("full scoring boundary changed")
    if results.get("final_scoreable_count") != 5 or results.get("final_positive_memory_count") != 2:
        errors.append("scoreable/positive count changed")
    if results.get("final_non_ansible_positive_memory_count") != 0:
        errors.append("non-Ansible positive-memory count changed")
    if results.get("memory_lift_status") != "undemonstrated":
        errors.append("memory lift was claimed")
    if results.get("self_maintaining_software_status") != "false/not_demonstrated":
        errors.append("self-maintaining software was claimed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v2.18 origin licensing source acquisition outputs.")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing required output: {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required output: {rel}")
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        parts = set(PurePosixPath(rel).parts)
        if path.suffix.lower() in {".zip", ".tar"} or parts.intersection({".venv", "venv", "__pycache__"}):
            errors.append(f"forbidden packaged path: {rel}")

    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)
    results = load_json(root / "campaign_results.json", errors)
    source = load_json(root / "source_acquisition_audit.json", errors)
    purity = load_json(root / "workspace_purity_report.json", errors)
    equivalence = load_json(root / "workspace_equivalence_summary.json", errors)
    provenance = load_json(root / "workspace_provenance.json", errors)
    env_lock = load_json(root / "environment_lock_summary.json", errors)
    command = load_json(root / "bugsinpy_command_map_v1.json", errors)
    baseline = load_json(root / "baseline_registry_snapshot_v2_18.json", errors)
    dep = load_json(root / "dependency_recovery_audit.json", errors)
    replay = load_json(root / "pre_repair_replay_gate_summary.json", errors)
    patch = load_json(root / "patch_candidate_safety_check.json", errors)
    ledger = load_json(root / "proof_obligations_ledger.json", errors)
    claims = load_json(root / "claim_boundary_v2_18.json", errors)
    v217 = load_json(REPO_ROOT / "outputs" / "v2_17_pysnooper1_runtime_workspace_materialization" / "v2_17_official_artifact_verification.json", errors)

    if v217.get("status") != "PASS" or v217.get("v2_17_promoted_to_current") is not False:
        errors.append("v2.17 official ingest boundary missing or promoted")
    if baseline.get("status") != "PASS" or baseline.get("precheck_ran_before_source_acquisition") is not True:
        errors.append("baseline precheck did not pass before acquisition")
    if baseline.get("expected_scoreable_count") != 5 or baseline.get("expected_positive_memory_count") != 2:
        errors.append("baseline expected counts changed")
    if baseline.get("ansible2_preserved") is not True or baseline.get("ansible5_preserved") is not True:
        errors.append("ansible positive-memory preservation not recorded")

    if source.get("repo_url") != "https://github.com/cool-RR/PySnooper":
        errors.append("unexpected PySnooper source repository")
    if source.get("buggy_commit_id") != EXPECTED_REVISION:
        errors.append("unexpected PySnooper buggy revision")
    if source.get("source_acquisition_status") == "source_checkout_acquired":
        if source.get("acquired_head_sha") != EXPECTED_REVISION:
            errors.append("source acquisition did not acquire expected revision")
    if source.get("checkout_workspace_outside_repo") is not True or not is_outside_repo(source.get("checkout_workspace")):
        errors.append("source workspace is not outside repository")
    if source.get("fixed_or_gold_patch_used") is not False or source.get("future_outcome_evidence_used") is not False:
        errors.append("source acquisition used forbidden evidence")
    if source.get("hidden_label_evidence_used") is not False:
        errors.append("hidden-label evidence used")

    if purity.get("status") != "PASS":
        errors.append("workspace purity did not pass")
    if purity.get("stale_cache_contamination_count") != 0 or purity.get("forbidden_residual_files_count") != 0:
        errors.append("workspace purity detected stale contamination")
    if purity.get("workspace_path_under_onedrive") is not False:
        errors.append("runtime workspace used OneDrive")
    if provenance.get("fixed_revision_contents_accessed") is not False or provenance.get("gold_patch_accessed") is not False:
        errors.append("workspace provenance accessed fixed/gold")
    if provenance.get("tests_fixtures_expectations_mutated") is not False:
        errors.append("workspace provenance mutated tests/fixtures/expectations")

    if env_lock.get("status") != "PASS":
        if env_lock.get("blocker") != "pre_repair_environment_lock_missing":
            errors.append("environment lock blocked without exact blocker")
    elif env_lock.get("python_toolbox_declared") is not True:
        errors.append("environment lock did not record python-toolbox declaration")
    if command.get("status") != "PASS":
        if command.get("blocker") != "blocked_command_manifest_missing_or_unsafe":
            errors.append("command manifest blocked without exact blocker")
    if command.get("target_command") != "python -m pytest -q -s tests/test_chinese.py::test_chinese":
        errors.append("unexpected target command")

    if equivalence.get("status") == "PASS" and replay.get("pre_repair_replay_attempted") is not True:
        errors.append("workspace equivalence passed but replay was not attempted")
    if equivalence.get("status") == "BLOCK" and dep.get("dependency_recovery_status") != "not_executed_workspace_equivalence_blocked":
        errors.append("dependency recovery should be blocked by workspace equivalence")
    if dep.get("import_statements_alone_used_to_authorize_install") is not False:
        errors.append("dependency install was authorized by imports alone")
    if dep.get("undeclared_dependency_installed") is not False or dep.get("global_environment_mutated") is not False:
        errors.append("dependency recovery crossed install/environment boundary")
    if patch.get("patch_attempt_count", 0) > 1:
        errors.append("patch attempts exceed one")
    if patch.get("patch_generated") is False:
        for rel in OPTIONAL_PATCH_FILES:
            if (root / rel).exists():
                errors.append(f"optional patch output exists despite patch_generated=false: {rel}")
        if patch.get("patch_authorized") is not False or patch.get("patch_attempted") is not False:
            errors.append("patch false state inconsistent")
    if patch.get("tests_modified") is not False or patch.get("fixtures_modified") is not False:
        errors.append("patch modified tests/fixtures")
    if patch.get("benchmark_metadata_modified") is not False or patch.get("harness_modified") is not False:
        errors.append("patch modified benchmark/harness")
    if results.get("pysnooper1_scoreable") is True and results.get("duplicate_replay_status") != "PASS":
        errors.append("scoreable result lacks duplicate replay PASS")

    if ledger:
        audit_ledger(root, ledger, errors)
    if results and claims:
        audit_claims(results, claims, errors)

    status = "PASS" if not errors else "FAIL"
    print(f"v2.18 origin licensing source acquisition audit {status} ({checked} manifest entries)")
    if results:
        for key in [
            "source_acquisition_status",
            "source_commit_revision_acquired",
            "workspace_equivalence_status",
            "workspace_purity_status",
            "environment_lock_status",
            "command_manifest_status",
            "baseline_registry_precheck_status",
            "dependency_recovery_status",
            "pre_repair_replay_status",
            "patch_generated",
            "patch_authorized",
            "patch_attempted",
            "pysnooper1_scoreable",
            "pysnooper1_positive_memory_only",
        ]:
            print(f"{key}={results.get(key)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
