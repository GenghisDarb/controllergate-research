#!/usr/bin/env python3
"""Audit v2.20 coupled test-provenance repair-lane evidence."""

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
DEFAULT_ROOT = REPO_ROOT / "outputs" / "v2_20_test_provenance_repair_lane"
EXPECTED_REVISION = "e21a31162f4c54be693d8ca8260e42393b39abd3"
REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "bugsinpy_harness_origin_manifest.json",
    "bugsinpy_harness_origin_audit.json",
    "proposed_harness_origin_candidate.json",
    "test_acquisition_audit.json",
    "test_provenance.json",
    "materialized_test_equivalence_summary.json",
    "test_workspace_equivalence.json",
    "test_purity_report.json",
    "workspace_purity_report.json",
    "workspace_equivalence_summary.json",
    "replisome_coupling_check.json",
    "chaperonin_topology_map.json",
    "recursive_provenance_chain_audit.json",
    "nuclear_pore_transport_log.json",
    "redundancy_cache_lookup.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v1.json",
    "baseline_registry_snapshot_v2_20.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "isolated_execution_log.txt",
    "s_engine_cognitive_state_snapshot.json",
    "retrocausal_reward_signal.json",
    "test_suite_structural_signature.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "patch_application_step.json",
    "telomere_workspace_protection_status.json",
    "post_validation_workspace_analysis.json",
    "patch_candidate_safety_check.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_20.json",
    "roadmap_carry_forward_check_v2_20.json",
    "resolution_depth_diagnostic_v2_20.json",
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
        errors.append("blocked lane lacks rollback entry")
    if ledger.get("ghost_state_count") != 0:
        errors.append("ledger reports ghost states")


def audit_v219_boundary(errors: list[str]) -> None:
    record = load_json(REPO_ROOT / "outputs" / "v2_19_bugsinpy_materialized_test_provenance" / "v2_19_official_artifact_verification.json", errors)
    if record.get("status") != "PASS":
        errors.append("v2.19 official artifact verification record missing PASS")
    if record.get("zip_sha256") != "bd7ee23458a60051abe2137266b91d06c72b06449941f2720ddc09b0b6ead695":
        errors.append("v2.19 official artifact digest mismatch")
    audit = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "audit_v2_19_bugsinpy_materialized_test_provenance.py")],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if audit.returncode != 0:
        errors.append("v2.19 audit did not pass from v2.20 audit")


def audit_transport(root: Path, transport: dict[str, Any], errors: list[str]) -> None:
    if transport.get("transport_integrity_status") != "PASS":
        errors.append("transport integrity did not pass")
    entries = transport.get("entries")
    if not isinstance(entries, list):
        errors.append("transport entries missing")
        return
    for entry in entries:
        rel = entry.get("repo_output_path")
        if not rel:
            errors.append("transport entry missing repo_output_path")
            continue
        path = REPO_ROOT / str(rel)
        if not path.is_file():
            errors.append(f"transport target missing: {rel}")
            continue
        actual = sha256_path(path)
        if entry.get("repo_ingested_sha256") != actual or entry.get("workspace_sha256") != actual:
            errors.append(f"transport hash mismatch: {rel}")
        if entry.get("transport_integrity") != "PASS":
            errors.append(f"transport FAIL entry: {rel}")
    required = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "nuclear_pore_transport_log.json", "proof_obligations_ledger.json"}
    }
    covered = {str(entry.get("repo_output_path")) for entry in entries if entry.get("repo_output_path")}
    missing = required - covered
    if missing:
        errors.append(f"transport log missing outputs: {sorted(missing)[:5]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v2.20 coupled provenance precision repair lane.")
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
    harness_manifest = load_json(root / "bugsinpy_harness_origin_manifest.json", errors)
    harness_audit = load_json(root / "bugsinpy_harness_origin_audit.json", errors)
    proposal = load_json(root / "proposed_harness_origin_candidate.json", errors)
    test_acquisition = load_json(root / "test_acquisition_audit.json", errors)
    test_provenance = load_json(root / "test_provenance.json", errors)
    coupling = load_json(root / "replisome_coupling_check.json", errors)
    topology = load_json(root / "chaperonin_topology_map.json", errors)
    recursive = load_json(root / "recursive_provenance_chain_audit.json", errors)
    transport = load_json(root / "nuclear_pore_transport_log.json", errors)
    redundancy = load_json(root / "redundancy_cache_lookup.json", errors)
    env_lock = load_json(root / "environment_lock_summary.json", errors)
    command = load_json(root / "bugsinpy_command_map_v1.json", errors)
    baseline = load_json(root / "baseline_registry_snapshot_v2_20.json", errors)
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
    claims = load_json(root / "claim_boundary_v2_20.json", errors)
    roadmap_check = load_json(root / "roadmap_carry_forward_check_v2_20.json", errors)
    resolution = load_json(root / "resolution_depth_diagnostic_v2_20.json", errors)

    audit_v219_boundary(errors)
    audit_transport(root, transport, errors)

    if not (REPO_ROOT / "docs" / "controllergate_tld_resolution_map.md").is_file():
        errors.append("missing TLD/resolution map doc")
    if not (REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json").is_file():
        errors.append("missing resolution depth map config")
    if roadmap_check.get("status") != "PASS" or roadmap_check.get("roadmap_updated_for_v2_20") is not True:
        errors.append("roadmap carry-forward check did not pass")
    if roadmap_check.get("backlog_updated_for_v2_20") is not True:
        errors.append("backlog carry-forward check did not pass")

    if baseline.get("status") != "PASS" or baseline.get("precheck_ran_before_source_acquisition") is not True:
        errors.append("baseline precheck did not pass before acquisition")
    if baseline.get("expected_scoreable_count") != 5 or baseline.get("expected_positive_memory_count") != 2:
        errors.append("baseline counts changed")
    if baseline.get("ansible2_preserved") is not True or baseline.get("ansible5_preserved") is not True:
        errors.append("previous positive-memory preservation missing")

    if test_acquisition.get("source_acquisition_status") != "source_checkout_acquired":
        errors.append("source acquisition did not pass")
    if test_acquisition.get("acquired_head_sha") != EXPECTED_REVISION:
        errors.append("source acquisition revision mismatch")
    if test_acquisition.get("checkout_workspace_outside_repo") is not True or not is_outside_repo(test_acquisition.get("checkout_workspace")):
        errors.append("source workspace is not outside repo")

    if redundancy.get("lookup_ran_before_new_test_acquisition") is not True:
        errors.append("redundancy lookup did not run before new test acquisition")
    if redundancy.get("cache_file_trusted") is not False:
        errors.append("redundancy cache trusted without authoritative hash")
    if redundancy.get("result") not in {"not_found", "found_but_expected_hash_missing", "found_but_hash_mismatch"}:
        errors.append("unexpected redundancy cache result")
    if redundancy.get("result") == "found_but_expected_hash_missing" and redundancy.get("blocker_if_fail") != "redundancy_cache_expected_hash_missing":
        errors.append("redundancy expected-hash-missing blocker incorrect")

    if harness_manifest.get("status") != "BLOCK" or harness_audit.get("bootstrap_status") != "BLOCK":
        errors.append("harness origin should be blocked without authoritative pin")
    if harness_audit.get("blocker_if_fail") != "bugsinpy_harness_origin_bootstrap_missing":
        errors.append("harness origin blocker mismatch")
    if harness_audit.get("expected_sha256_generated_by_v2_20") is not False:
        errors.append("harness origin expected SHA generated by v2.20")
    if harness_audit.get("self_referential_hash_detected") is not False:
        errors.append("self-referential harness-origin hash detected")
    if proposal.get("proposal_only") is not True or proposal.get("not_authoritative_for_current_run") is not True:
        errors.append("proposed harness origin candidate was not proposal-only")
    if harness_audit.get("proposal_used_as_authority") is not False:
        errors.append("proposal was used as current-run authority")

    if test_provenance.get("status") != "BLOCK" or test_provenance.get("blocker") != "bugsinpy_harness_origin_bootstrap_missing":
        errors.append("target-test provenance block mismatch")
    forbidden_flags = [
        test_provenance.get("fixed_revision_contents_used"),
        test_provenance.get("gold_patch_used"),
        test_provenance.get("future_outcome_evidence_used"),
        test_provenance.get("hidden_label_evidence_used"),
        test_provenance.get("synthetic_or_generated_test_used"),
    ]
    if any(flag is not False for flag in forbidden_flags):
        errors.append("target-test provenance used forbidden source")
    if recursive.get("chain_clean") is not True:
        errors.append("recursive provenance chain not clean")
    if coupling.get("coupling_status") != "BLOCK":
        errors.append("coupling should block without target-test provenance")
    if topology.get("topology_status") != "BLOCK":
        errors.append("topology should block without harness origin/test")

    if env_lock.get("status") != "PASS" or env_lock.get("python_toolbox_declared") is not True:
        errors.append("environment lock did not pass")
    if command.get("status") != "PASS" or command.get("target_command") != "python -m pytest -q -s tests/test_chinese.py::test_chinese":
        errors.append("command manifest invalid")
    if dep.get("dependency_recovery_status") != "not_executed_harness_origin_blocked":
        errors.append("dependency recovery status mismatch")
    if replay.get("pre_repair_replay_status") != "not_run_harness_origin_blocked" or replay.get("pre_repair_replay_attempted") is not False:
        errors.append("pre-repair replay status mismatch")

    if cognitive.get("status") != "PASS":
        errors.append("cognitive state snapshot did not pass")
    for key in ["prompt_hash_pre_generation", "context_hash_pre_generation", "decision_time_evidence_hash_pre_generation", "cognitive_state_hash"]:
        if not re.fullmatch(r"[0-9a-f]{64}", str(cognitive.get(key) or "")):
            errors.append(f"cognitive state missing {key}")
    if cognitive.get("generated_patch_hash") and not cognitive.get("timestamp_pre_generation"):
        errors.append("cognitive_state_timestamp_inversion")
    if cognitive.get("fixed_gold_future_evidence_used") is not False:
        errors.append("cognitive state used forbidden evidence")

    if reward.get("precondition_failure") is not True or reward.get("graded_signal") != 0.0:
        errors.append("zero-lift reward did not classify precondition failure")
    if reward.get("failure_type") != "bugsinpy_harness_origin_missing":
        errors.append("reward failure type mismatch")
    if reward.get("full_scoring_enabled") is not False or reward.get("diagnostic_only") is not True:
        errors.append("reward signal enabled scoring or was not diagnostic-only")
    if structural.get("command_executed") is not False or structural.get("signature_status") != "not_run_precondition_blocked":
        errors.append("structural signature did not classify precondition block")
    if not re.fullmatch(r"[0-9a-f]{64}", str(structural.get("structural_signature_hash") or "")):
        errors.append("structural signature hash missing")

    if patch_size.get("cap_status") != "PASS" or patch_size.get("overshoot_severity") != "none":
        errors.append("patch size cap status mismatch")
    if patch.get("patch_generated") is not False or patch.get("patch_authorized") is not False or patch.get("patch_attempted") is not False:
        errors.append("patch should not be generated/authorized/attempted")
    if patch.get("patch_attempt_count") != 0:
        errors.append("patch attempt count should be zero")
    for key in ["tests_modified", "fixtures_modified", "benchmark_metadata_modified", "harness_modified", "generated_expectations_modified"]:
        if patch.get(key) is not False:
            errors.append(f"patch modified forbidden path category: {key}")
    for rel in OPTIONAL_PATCH_FILES:
        if (root / rel).exists():
            errors.append(f"optional patch output exists despite no patch: {rel}")
    if realtime.get("status") != "not_applicable_no_patch":
        errors.append("realtime patch safety should be not applicable")
    if application.get("verification_happened_before_application") is not True or application.get("apply_status") != "not_attempted":
        errors.append("patch application semantics incorrect")
    if post_validation.get("status") != "not_run_no_validation":
        errors.append("post-validation analysis status mismatch")

    if resolution.get("status") != "PASS":
        errors.append("resolution depth diagnostic did not pass")
    claim_boundary = resolution.get("claim_boundary") or {}
    for key in ["architecture_heuristic_only", "not_physics_validation", "not_full_scoring", "not_self_maintaining_software", "not_generalization"]:
        if claim_boundary.get(key) is not True:
            errors.append(f"resolution claim boundary missing {key}")
    if claims.get("current_protocol_version") != "v2.13" or claims.get("v2_20_promoted_to_current") is not False:
        errors.append("current protocol boundary changed")
    if claims.get("full_scoring") != "NOT_RUN" or claims.get("full_scoring_allowed") is not False:
        errors.append("full scoring boundary changed")
    if claims.get("self_maintaining_software_status") != "false/not_demonstrated":
        errors.append("self-maintaining claim changed")
    if claims.get("pysnooper2_pursued") is not False:
        errors.append("PySnooper:2 was pursued")
    if results.get("final_scoreable_count") != 5 or results.get("final_positive_memory_count") != 2:
        errors.append("aggregate counts changed")
    if results.get("final_non_ansible_positive_memory_count") != 0:
        errors.append("non-Ansible positive-memory count changed")
    if results.get("pysnooper1_scoreable") is True and results.get("duplicate_replay_status") != "PASS":
        errors.append("scoreable result lacks duplicate replay PASS")

    audit_ledger(root, ledger, errors)

    status = "PASS" if not errors else "FAIL"
    print(f"v2.20 coupled provenance precision repair audit {status} ({checked} manifest entries)")
    if results:
        for key in [
            "bugsinpy_harness_origin_status",
            "harness_origin_bootstrap_status",
            "target_test_provenance_status",
            "replisome_coupling_status",
            "chaperonin_topology_status",
            "redundancy_cache_lookup_result",
            "nuclear_pore_transport_status",
            "workspace_equivalence_status",
            "environment_lock_status",
            "command_manifest_status",
            "baseline_registry_precheck_status",
            "dependency_recovery_status",
            "pre_repair_replay_status",
            "cognitive_state_snapshot_status",
            "pre_generation_prompt_context_hash_status",
            "reward_signal_status",
            "reward_graded_signal",
            "reward_failure_type",
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
