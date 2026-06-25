#!/usr/bin/env python3
"""Audit v2.19 BugsInPy materialized-test provenance outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "outputs" / "v2_19_bugsinpy_materialized_test_provenance"
CAMPAIGN_ID = "v2_19_bugsinpy_materialized_test_provenance"
EXPECTED_REVISION = "e21a31162f4c54be693d8ca8260e42393b39abd3"
REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "source_acquisition_audit.json",
    "materialized_test_provenance.json",
    "materialized_test_equivalence_summary.json",
    "workspace_equivalence_summary.json",
    "workspace_purity_report.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v1.json",
    "baseline_registry_snapshot_v2_19.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "isolated_execution_log.txt",
    "patch_candidate_safety_check.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_19.json",
    "s_engine_cognitive_state_snapshot.json",
    "retrocausal_reward_signal.json",
    "test_suite_structural_signature.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "patch_application_step.json",
    "telomere_workspace_protection_status.json",
    "post_validation_workspace_analysis.json",
    "SHA256SUMS.txt",
]
OPTIONAL_PATCH_FILES = {
    "memory_enabled_source_only_repair_patch.diff",
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
    expected_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"}
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
    failure_seen = False
    rollback_seen = False
    for index, entry in enumerate(ledger.get("ledger_entries") or []):
        material = {key: value for key, value in entry.items() if key != "entry_hash"}
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
        errors.append("blocked v2.19 lane lacks rollback entry")
    if ledger.get("ghost_state_count") != 0:
        errors.append("ledger reports ghost states")


def audit_backlog(errors: list[str]) -> None:
    roadmap = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
    backlog = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
    if not roadmap.is_file():
        errors.append("missing non-Ansible capability roadmap")
    data = load_json(backlog, errors)
    items = data.get("items")
    if not isinstance(items, list) or len(items) != 18:
        errors.append("non-Ansible backlog must contain 18 capability items")
    required_ids = {
        "source_acquisition_origin_licensing",
        "environment_lock",
        "command_manifest_bugsinpy_translation_bridge",
        "fresh_workspace_stale_artifact_resistance",
        "baseline_registry_precheck",
        "cryptographic_rollback_markers",
        "repair_state_snapshot",
        "bounded_diagnostic_reward_signal",
        "test_run_structural_signature",
        "patch_size_cap_locality_limit",
        "real_time_patch_safety",
        "patch_application_step",
        "workspace_protection",
        "post_validation_workspace_analysis",
        "materialized_target_test_provenance_bridge",
        "pysnooper2_policy",
        "claims_boundary",
        "future_version_sequencing",
    }
    ids = {item.get("id") for item in items if isinstance(item, dict)}
    missing = required_ids - ids
    if missing:
        errors.append(f"non-Ansible backlog missing ids: {sorted(missing)}")
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        for key in ["status", "target_version", "required_files", "audit_checks", "stop_conditions"]:
            if key not in item:
                errors.append(f"backlog item {item.get('id')} missing {key}")


def audit_v218_boundary(errors: list[str]) -> None:
    record = load_json(REPO_ROOT / "outputs" / "v2_18_origin_licensing_source_acquisition" / "v2_18_official_artifact_verification.json", errors)
    if record.get("status") != "PASS":
        errors.append("v2.18 official artifact verification record missing PASS")
    if record.get("zip_sha256") != "4c91b8e69dd75e1ed49432611f834b73ec700054d6395c99b42c729e9f84eac5":
        errors.append("v2.18 official artifact digest mismatch")
    audit = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "audit_v2_18_origin_licensing_source_acquisition.py")],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if audit.returncode != 0:
        errors.append("v2.18 audit did not pass from v2.19 audit")


def audit_claims(results: dict[str, Any], claims: dict[str, Any], errors: list[str]) -> None:
    if results.get("candidate_scope") != ["PySnooper:1"] or claims.get("candidate_scope") != ["PySnooper:1"]:
        errors.append("candidate scope must be PySnooper:1 only")
    if results.get("pysnooper2_pursued") is not False or claims.get("pysnooper2_pursued") is not False:
        errors.append("PySnooper:2 was pursued")
    if results.get("current_protocol_version") != "v2.13" or claims.get("current_protocol_version") != "v2.13":
        errors.append("current protocol changed")
    if claims.get("v2_19_promoted_to_current") is not False:
        errors.append("v2.19 promoted to current")
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
    parser = argparse.ArgumentParser(description="Audit v2.19 BugsInPy materialized-test provenance outputs.")
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
        if path.suffix.lower() in {".zip", ".tar", ".tgz", ".gz", ".7z"} or parts.intersection({".venv", "venv", "__pycache__", ".pytest_cache"}):
            errors.append(f"forbidden packaged path: {rel}")

    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)

    results = load_json(root / "campaign_results.json", errors)
    source = load_json(root / "source_acquisition_audit.json", errors)
    materialized = load_json(root / "materialized_test_provenance.json", errors)
    materialized_eq = load_json(root / "materialized_test_equivalence_summary.json", errors)
    workspace_eq = load_json(root / "workspace_equivalence_summary.json", errors)
    purity = load_json(root / "workspace_purity_report.json", errors)
    workspace_protection = load_json(root / "telomere_workspace_protection_status.json", errors)
    env_lock = load_json(root / "environment_lock_summary.json", errors)
    command = load_json(root / "bugsinpy_command_map_v1.json", errors)
    baseline = load_json(root / "baseline_registry_snapshot_v2_19.json", errors)
    dep = load_json(root / "dependency_recovery_audit.json", errors)
    replay = load_json(root / "pre_repair_replay_gate_summary.json", errors)
    cognitive = load_json(root / "s_engine_cognitive_state_snapshot.json", errors)
    reward = load_json(root / "retrocausal_reward_signal.json", errors)
    structural = load_json(root / "test_suite_structural_signature.json", errors)
    patch_size = load_json(root / "patch_size_cap.json", errors)
    realtime = load_json(root / "realtime_patch_safety_trace.json", errors)
    application = load_json(root / "patch_application_step.json", errors)
    post_validation = load_json(root / "post_validation_workspace_analysis.json", errors)
    patch = load_json(root / "patch_candidate_safety_check.json", errors)
    ledger = load_json(root / "proof_obligations_ledger.json", errors)
    claims = load_json(root / "claim_boundary_v2_19.json", errors)

    audit_backlog(errors)
    audit_v218_boundary(errors)

    if baseline.get("status") != "PASS" or baseline.get("precheck_ran_before_source_acquisition") is not True:
        errors.append("baseline registry precheck did not pass before acquisition")
    if baseline.get("expected_scoreable_count") != 5 or baseline.get("expected_positive_memory_count") != 2:
        errors.append("baseline expected counts changed")
    if baseline.get("ansible2_preserved") is not True or baseline.get("ansible5_preserved") is not True:
        errors.append("previous positive-memory preservation missing")

    if source.get("source_acquisition_status") != "source_checkout_acquired":
        errors.append("PySnooper source checkout was not acquired")
    if source.get("acquired_head_sha") != EXPECTED_REVISION:
        errors.append("PySnooper acquired revision mismatch")
    if source.get("checkout_workspace_outside_repo") is not True or not is_outside_repo(source.get("checkout_workspace")):
        errors.append("source workspace is not outside repository")
    if source.get("fixed_or_gold_patch_used") is not False or source.get("future_outcome_evidence_used") is not False:
        errors.append("source acquisition used forbidden evidence")
    if source.get("hidden_label_evidence_used") is not False:
        errors.append("source acquisition used hidden-label evidence")

    materialized_status = materialized.get("provenance_status")
    if materialized_status not in {"PASS", "BLOCK"}:
        errors.append("materialized target-test provenance status must be PASS or BLOCK")
    if materialized.get("target_test") != "tests/test_chinese.py":
        errors.append("unexpected materialized target test")
    if materialized.get("fixed_revision_contents_used") is not False:
        errors.append("materialized target test used fixed revision content")
    if materialized.get("gold_patch_used") is not False or materialized.get("future_outcome_evidence_used") is not False:
        errors.append("materialized target test used gold/future evidence")
    if materialized.get("hidden_label_evidence_used") is not False or materialized.get("hallucinated_content_used") is not False:
        errors.append("materialized target test used hidden/hallucinated evidence")
    if materialized_status == "BLOCK":
        if materialized.get("blocker") != "blocked_materialized_target_test_provenance_missing":
            errors.append("materialized-test provenance block has wrong blocker")
        if results.get("pysnooper1_classification") != "blocked_materialized_target_test_provenance_missing":
            errors.append("final classification does not match materialized-test provenance block")
        if materialized.get("target_test_sha256") is not None:
            errors.append("blocked materialized-test provenance unexpectedly has target hash")
        if materialized_eq.get("status") != "BLOCK" or workspace_eq.get("status") != "BLOCK":
            errors.append("materialized-test block did not block equivalence")
    else:
        if not re.fullmatch(r"[0-9a-f]{64}", str(materialized.get("target_test_sha256") or "")):
            errors.append("materialized target-test PASS lacks SHA256")
        if materialized.get("benchmark_harness_materialization") is not True or materialized.get("repair_mutation") is not False:
            errors.append("materialized test not classified as benchmark harness setup")

    if purity.get("status") != "PASS":
        errors.append("workspace purity did not pass")
    if purity.get("stale_cache_contamination_count") != 0 or purity.get("forbidden_residual_files_count") != 0:
        errors.append("workspace purity detected stale contamination")
    if purity.get("workspace_path_under_onedrive") is not False:
        errors.append("workspace under OneDrive")
    if workspace_protection.get("status") != "PASS" or workspace_protection.get("protected_workspace") is not True:
        errors.append("workspace protection did not pass")
    if workspace_protection.get("stale_cache_count") != 0:
        errors.append("workspace protection stale cache count not zero")

    if env_lock.get("status") != "PASS":
        errors.append("environment lock did not pass")
    if env_lock.get("python_toolbox_declared") is not True:
        errors.append("environment lock did not record python-toolbox declaration")
    if env_lock.get("no_undeclared_dependency_install") is not True or env_lock.get("no_global_environment_mutation") is not True:
        errors.append("environment lock install/global mutation boundary failed")
    if command.get("status") != "PASS":
        errors.append("command manifest did not pass")
    if command.get("target_command") != "python -m pytest -q -s tests/test_chinese.py::test_chinese":
        errors.append("unexpected target command")

    if materialized_status == "BLOCK":
        if dep.get("dependency_recovery_status") != "not_executed_materialized_test_provenance_blocked":
            errors.append("dependency recovery should be blocked by target-test provenance")
        if replay.get("pre_repair_replay_status") != "not_run_materialized_test_provenance_blocked":
            errors.append("pre-repair replay should be blocked by target-test provenance")
        if replay.get("pre_repair_replay_attempted") is not False:
            errors.append("pre-repair replay attempted despite provenance block")
    if dep.get("undeclared_dependency_installed") is not False or dep.get("global_environment_mutated") is not False:
        errors.append("dependency recovery crossed install/environment boundary")
    if dep.get("import_statements_alone_used_to_authorize_install") is not False:
        errors.append("dependency install authorized by imports alone")

    if cognitive.get("status") != "PASS" or cognitive.get("written_before_patch_generation") is not True:
        errors.append("repair state snapshot missing or not before patch generation")
    if cognitive.get("fixed_gold_future_evidence_used") is not False:
        errors.append("repair state snapshot used forbidden evidence")
    if not re.fullmatch(r"[0-9a-f]{64}", str(cognitive.get("cognitive_state_hash") or "")):
        errors.append("repair state snapshot hash missing")
    if reward.get("diagnostic_only") is not True or reward.get("full_scoring_enabled") is not False:
        errors.append("reward signal is not diagnostic-only")
    if reward.get("broad_benchmark_claim") is not False:
        errors.append("reward signal made a broad benchmark claim")
    if not re.fullmatch(r"[0-9a-f]{64}", str(structural.get("structural_signature_hash") or "")):
        errors.append("test structural signature hash missing")
    if patch_size.get("status") != "PASS":
        errors.append("patch size cap did not pass")
    if patch_size.get("max_files_touched") != 3 or patch_size.get("max_lines_changed") != 50 or patch_size.get("max_functions_modified") != 2:
        errors.append("patch size cap limits changed")
    if realtime.get("status") not in {"PASS", "not_applicable_no_patch", "BLOCK"}:
        errors.append("invalid real-time patch safety status")
    if application.get("verification_happened_before_application") is not True:
        errors.append("patch application semantics incorrect")
    if "seal as verification" in json.dumps(application, sort_keys=True).lower():
        errors.append("patch application step uses forbidden verification wording")
    if post_validation.get("status") not in {"PASS", "not_run_no_validation", "BLOCK"}:
        errors.append("invalid post-validation workspace analysis status")

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
    if patch.get("generated_expectations_modified") is not False:
        errors.append("patch modified generated expectations")
    if results.get("pysnooper1_scoreable") is True and results.get("duplicate_replay_status") != "PASS":
        errors.append("scoreable result lacks duplicate replay PASS")

    if ledger:
        audit_ledger(root, ledger, errors)
    if results and claims:
        audit_claims(results, claims, errors)

    status = "PASS" if not errors else "FAIL"
    print(f"v2.19 BugsInPy materialized-test provenance audit {status} ({checked} manifest entries)")
    if results:
        for key in [
            "source_acquisition_status",
            "source_commit_revision_acquired",
            "materialized_target_test_provenance_status",
            "materialized_target_test_sha256",
            "workspace_equivalence_status",
            "workspace_purity_status",
            "environment_lock_status",
            "command_manifest_status",
            "baseline_registry_precheck_status",
            "dependency_recovery_status",
            "pre_repair_replay_status",
            "cognitive_state_snapshot_status",
            "reward_signal_status",
            "test_structural_signature_status",
            "patch_size_cap_status",
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
