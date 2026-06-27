#!/usr/bin/env python3
"""Audit v2.31 scoreable external repair episode consolidation evidence."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_31_scoreable_repair_episode_consolidation_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V230_ROOT = REPO_ROOT / "outputs" / "v2_30_failure_signature_canonicalization_repair_lane"
EPISODE_REGISTRY_PATH = REPO_ROOT / "configs" / "external_repair_episode_registry.json"
EXTERNAL_CANDIDATE_REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
FAILURE_LEDGER_PATH = REPO_ROOT / "configs" / "failure_memory_weight_ledger.json"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED = {
    "candidate_id": "py_bugger_issue_65",
    "repo_url": "https://github.com/ehmatthes/py-bugger",
    "buggy_commit_sha": "67cf214f2d619848e90280fd4469377123e81b94",
    "test_command": "python -m pytest tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys -q",
    "target_test_path": "tests/integration_tests/test_modifications.py",
    "target_test_sha256": "3e3c9521a4c1084df9269fb6bd38cb47808061559d7eb3eafa3fd78f4f3965b1",
    "support_file_path": "tests/sample_code/sample_scripts/two_trys.py",
    "support_file_sha256": "66a72a7abc6f2bffec7881d0a5b0a006deb408a8c496148210e14caafd1a2d11",
    "environment_lock_source_sha256": "2f1fe04032ca64b556e4db66a1aa5af3c81ccc958735a390226ea1b987484631",
    "semantic_failure_signature_hash": "3e54d6c5566c0c373b8b409134879cb58026d970111365d0c348cd2398ec334f",
    "patch_sha256": "02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee",
    "patch_source_path": "src/py_bugger/utils/bug_utils.py",
    "artifact_sha256": "6321a219fc57832d23bb6028beb61f2dbd873ac825b51ba3581e7a30eca1b883",
    "workflow_run_id": 28274637503,
    "artifact_id": 7919820263,
}

REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_30_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "scoreable_repair_episode_record.json",
    "scoreable_repair_episode_registry_before.json",
    "scoreable_repair_episode_registry_after.json",
    "v2_30_patch_provenance_record.json",
    "v2_30_patch_replay_evidence_record.json",
    "v2_30_registry_signature_history_record.json",
    "v2_30_claim_boundary_consolidation.json",
    "failure_memory_weight_ledger_before.json",
    "failure_memory_weight_ledger_after.json",
    "failure_memory_weight_ledger_update_report.json",
    "external_candidate_registry_status_v2_31.json",
    "next_candidate_readiness_plan_v2_31.json",
    "next_candidate_requirements_v2_31.json",
    "prospective_memory_lift_requirements_v2_31.json",
    "scoreable_episode_public_summary.md",
    "roadmap_carry_forward_check_v2_31.json",
    "resolution_depth_diagnostic_v2_31.json",
    "public_language_audit.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_31.json",
    "SHA256SUMS.txt",
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing JSON: {path.relative_to(REPO_ROOT).as_posix()}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path.relative_to(REPO_ROOT).as_posix()}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected object: {path.relative_to(REPO_ROOT).as_posix()}")
        return {}
    return value


def expect(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def verify_manifest(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file():
        return [f"missing manifest: {manifest.relative_to(REPO_ROOT).as_posix()}"], 0
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
    expected_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    for rel in sorted(expected_files - seen):
        errors.append(f"manifest missing {rel}")
    for rel in sorted(seen - expected_files):
        errors.append(f"manifest contains extra {rel}")
    return errors, checked


def run_python_script(script: str, errors: list[str]) -> None:
    result = subprocess.run([sys.executable, str(REPO_ROOT / script)], cwd=str(REPO_ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        tail = "\n".join((result.stdout + "\n" + result.stderr).splitlines()[-20:])
        errors.append(f"regression audit failed: {script}\n{tail}")


def audit_proof_ledger(ledger: dict[str, Any], errors: list[str]) -> None:
    expect(ledger.get("status") == "PASS", errors, "proof ledger status mismatch")
    entries = ledger.get("entries")
    expect(isinstance(entries, list) and len(entries) >= 8, errors, "proof ledger entries missing")
    if not isinstance(entries, list):
        return
    previous = "0" * 64
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"proof ledger entry {index} invalid")
            return
        expect(entry.get("index") == index, errors, f"proof ledger index mismatch at {index}")
        expect(entry.get("previous_entry_hash") == previous, errors, f"proof ledger previous hash mismatch at {index}")
        recorded = entry.get("entry_hash")
        payload = {key: value for key, value in entry.items() if key != "entry_hash"}
        computed = sha256_text(json.dumps(payload, sort_keys=True))
        expect(recorded == computed, errors, f"proof ledger hash mismatch at {index}")
        previous = str(recorded)
    expect(ledger.get("head_hash") == previous, errors, "proof ledger head hash mismatch")


def section_present(path: Path, heading: str) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return f"## {heading}" in text


def candidate_entry(errors: list[str]) -> dict[str, Any]:
    registry = load_json(EXTERNAL_CANDIDATE_REGISTRY_PATH, errors)
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        errors.append("external candidate registry candidates field is invalid")
        return {}
    matches = [item for item in candidates if isinstance(item, dict) and item.get("candidate_id") == EXPECTED["candidate_id"]]
    expect(len(matches) == 1, errors, "expected exactly one py-bugger candidate")
    return matches[0] if matches else {}


def hidden_public_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "bio" + "logical",
        "iso" + "morphic",
        "TO" + "RUS",
        "T" + "LD",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "meta" + "phorical",
    ]


def audit_outputs(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        expect((OUTPUT_ROOT / rel).is_file(), errors, f"missing required output: {rel}")
    manifest_errors, checked = verify_manifest(OUTPUT_ROOT)
    errors.extend(manifest_errors)
    expect(checked == len(REQUIRED_FILES) - 1, errors, "manifest entry count mismatch")

    results = load_json(OUTPUT_ROOT / "campaign_results.json", errors)
    official = load_json(OUTPUT_ROOT / "v2_30_artifact_ingest_verification.json", errors)
    episode = load_json(OUTPUT_ROOT / "scoreable_repair_episode_record.json", errors)
    episode_registry = load_json(EPISODE_REGISTRY_PATH, errors)
    episode_registry_after = load_json(OUTPUT_ROOT / "scoreable_repair_episode_registry_after.json", errors)
    patch_provenance = load_json(OUTPUT_ROOT / "v2_30_patch_provenance_record.json", errors)
    replay = load_json(OUTPUT_ROOT / "v2_30_patch_replay_evidence_record.json", errors)
    signature_history = load_json(OUTPUT_ROOT / "v2_30_registry_signature_history_record.json", errors)
    claim_v230 = load_json(OUTPUT_ROOT / "v2_30_claim_boundary_consolidation.json", errors)
    ledger_report = load_json(OUTPUT_ROOT / "failure_memory_weight_ledger_update_report.json", errors)
    ledger_after = load_json(FAILURE_LEDGER_PATH, errors)
    registry_status = load_json(OUTPUT_ROOT / "external_candidate_registry_status_v2_31.json", errors)
    readiness = load_json(OUTPUT_ROOT / "next_candidate_readiness_plan_v2_31.json", errors)
    next_requirements = load_json(OUTPUT_ROOT / "next_candidate_requirements_v2_31.json", errors)
    memory_requirements = load_json(OUTPUT_ROOT / "prospective_memory_lift_requirements_v2_31.json", errors)
    roadmap = load_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_31.json", errors)
    resolution = load_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_31.json", errors)
    public_language = load_json(OUTPUT_ROOT / "public_language_audit.json", errors)
    claim = load_json(OUTPUT_ROOT / "claim_boundary_v2_31.json", errors)
    proof = load_json(OUTPUT_ROOT / "proof_obligations_ledger.json", errors)
    candidate = candidate_entry(errors)
    matrix = load_json(CAPABILITY_MATRIX_PATH, errors)
    backlog = load_json(BACKLOG_PATH, errors)
    resolution_map = load_json(RESOLUTION_MAP_PATH, errors)

    expect(official.get("status") == "PASS", errors, "v2.30 official ingest not PASS")
    expect(official.get("manual_artifact_boundary") == "PASS", errors, "v2.30 manual artifact boundary not PASS")
    expect(official.get("downloaded_by_codex") is False, errors, "v2.30 artifact boundary violated")
    expect(official.get("zip_sha256") == EXPECTED["artifact_sha256"], errors, "v2.30 artifact SHA mismatch")
    expect(official.get("workflow_run_id") == EXPECTED["workflow_run_id"], errors, "v2.30 workflow run mismatch")
    expect(official.get("artifact_id") == EXPECTED["artifact_id"], errors, "v2.30 artifact id mismatch")
    official_cf = official.get("carry_forward") if isinstance(official.get("carry_forward"), dict) else {}
    expect(official_cf.get("selected_candidate_scoreable") is True, errors, "v2.30 official scoreable carry-forward missing")
    expect(official_cf.get("patch_sha256") == EXPECTED["patch_sha256"], errors, "v2.30 official patch carry-forward mismatch")
    expect(official_cf.get("target_validation_status") == "PASS", errors, "v2.30 target validation carry-forward missing")
    expect(official_cf.get("duplicate_clean_replay_status") == "PASS", errors, "v2.30 duplicate replay carry-forward missing")

    expect(results.get("status") == "PASS", errors, "v2.31 campaign results not PASS")
    expect(results.get("v2_30_scoreable_episode_ingest_status") == "PASS", errors, "scoreable episode ingest status mismatch")
    expect(results.get("external_repair_episode_registry_status") == "PASS", errors, "episode registry status mismatch")
    expect(results.get("scoreable_external_repair_episode_count") == 1, errors, "scoreable episode count mismatch")
    expect(results.get("selected_candidate_id") == EXPECTED["candidate_id"], errors, "selected candidate mismatch")
    expect(results.get("selected_candidate_scoreable") is True, errors, "selected candidate scoreable mismatch")
    expect(results.get("selected_candidate_positive_memory_only") is False, errors, "positive-memory-only status mismatch")
    expect(results.get("patch_sha256") == EXPECTED["patch_sha256"], errors, "campaign patch SHA mismatch")
    expect(results.get("target_validation_carry_forward_status") == "PASS", errors, "target validation carry-forward status mismatch")
    expect(results.get("duplicate_replay_carry_forward_status") == "PASS", errors, "duplicate replay carry-forward status mismatch")
    expect(results.get("stochastic_replay_reliability_carry_forward_status") == "PASS", errors, "reliability carry-forward status mismatch")
    expect(results.get("observed_reliability") == 1.0, errors, "observed reliability mismatch")
    expect(results.get("failure_memory_ledger_update_status") == "PASS", errors, "failure memory ledger update status mismatch")
    expect(results.get("next_candidate_readiness_plan_status") == "PASS", errors, "next candidate readiness status mismatch")
    expect(results.get("prospective_memory_lift_requirements_status") == "PASS", errors, "prospective memory requirements mismatch")
    expect(results.get("roadmap_backlog_update_status") == "PASS", errors, "roadmap/backlog update status mismatch")
    expect(results.get("public_language_audit_status") == "PASS", errors, "public language status mismatch")
    expect(results.get("external_clone_attempted") is False, errors, "v2.31 attempted external clone")
    expect(results.get("test_command_executed") is False, errors, "v2.31 executed target command")
    expect(results.get("patch_generated") is False, errors, "v2.31 generated patch")
    expect(results.get("repair_attempted") is False, errors, "v2.31 attempted repair")
    expect(results.get("s_engine_invoked") is False, errors, "v2.31 invoked S-engine")
    expect(results.get("exact_blocker") is None, errors, "v2.31 exact blocker not None")

    expect(episode.get("candidate_id") == EXPECTED["candidate_id"], errors, "episode candidate mismatch")
    expect(episode.get("episode_version") == "v2.30", errors, "episode version mismatch")
    expect(episode.get("episode_type") == "external_non_ansible_source_only_target_repair", errors, "episode type mismatch")
    expect(episode.get("scoreable") is True, errors, "episode not scoreable")
    expect(episode.get("positive_memory_only") is False, errors, "episode positive-memory-only mismatch")
    expect(episode.get("full_scoring") == "NOT_RUN/disallowed", errors, "episode full scoring mismatch")
    expect(episode.get("memory_lift") == "undemonstrated", errors, "episode memory lift mismatch")
    expect(episode.get("self_maintaining_software") == "false/not_demonstrated", errors, "episode self-maintaining mismatch")
    expect(episode.get("repo_url") == EXPECTED["repo_url"], errors, "episode repo mismatch")
    expect(episode.get("buggy_commit_sha") == EXPECTED["buggy_commit_sha"], errors, "episode commit mismatch")
    expect(episode.get("test_command") == EXPECTED["test_command"], errors, "episode command mismatch")
    target = episode.get("target_test_file") if isinstance(episode.get("target_test_file"), dict) else {}
    support = episode.get("support_file") if isinstance(episode.get("support_file"), dict) else {}
    env = episode.get("environment_lock_source") if isinstance(episode.get("environment_lock_source"), dict) else {}
    expect(target.get("path") == EXPECTED["target_test_path"], errors, "episode target path mismatch")
    expect(target.get("sha256") == EXPECTED["target_test_sha256"], errors, "episode target SHA mismatch")
    expect(support.get("path") == EXPECTED["support_file_path"], errors, "episode support path mismatch")
    expect(support.get("sha256") == EXPECTED["support_file_sha256"], errors, "episode support SHA mismatch")
    expect(env.get("sha256") == EXPECTED["environment_lock_source_sha256"], errors, "episode environment SHA mismatch")
    expect(episode.get("semantic_failure_signature_hash") == EXPECTED["semantic_failure_signature_hash"], errors, "episode semantic hash mismatch")
    expect(episode.get("registry_signature_refresh_status") == "PASS", errors, "episode registry refresh not PASS")
    expect(episode.get("patch_sha256") == EXPECTED["patch_sha256"], errors, "episode patch SHA mismatch")
    expect(EXPECTED["patch_source_path"] in (episode.get("patch_modified_files") or []), errors, "episode patch source path missing")
    expect(episode.get("patch_safety_status") == "PASS", errors, "episode patch safety not PASS")
    expect(episode.get("target_validation_status") == "PASS", errors, "episode target validation not PASS")
    expect(episode.get("target_validation_exit_status") == 0, errors, "episode target exit mismatch")
    expect(episode.get("duplicate_replay_status") == "PASS", errors, "episode duplicate replay not PASS")
    expect(episode.get("duplicate_replay_count") == "3 / 3", errors, "episode duplicate replay count mismatch")
    expect((episode.get("stochastic_replay_reliability") or {}).get("observed_reliability") == 1.0, errors, "episode reliability mismatch")
    expect(episode.get("diagnostic_reward_signal_status") == "PASS", errors, "episode reward status mismatch")
    expect(episode.get("artifact_sha256") == EXPECTED["artifact_sha256"], errors, "episode artifact SHA mismatch")
    expect(episode.get("workflow_run_id") == EXPECTED["workflow_run_id"], errors, "episode workflow run mismatch")
    expect(episode.get("artifact_id") == EXPECTED["artifact_id"], errors, "episode artifact id mismatch")

    for registry_obj, label in [(episode_registry, "live"), (episode_registry_after, "output")]:
        episodes = registry_obj.get("episodes")
        expect(isinstance(episodes, list), errors, f"{label} episode registry episodes invalid")
        if isinstance(episodes, list):
            matches = [
                item for item in episodes
                if isinstance(item, dict)
                and item.get("candidate_id") == EXPECTED["candidate_id"]
                and item.get("episode_version") == "v2.30"
            ]
            expect(len(matches) == 1, errors, f"{label} registry does not have exactly one v2.30 py-bugger episode")
            if matches:
                expect(matches[0].get("patch_sha256") == EXPECTED["patch_sha256"], errors, f"{label} registry patch SHA mismatch")
                expect(matches[0].get("scoreable") is True, errors, f"{label} registry scoreable mismatch")
            inconsistent = [
                item for item in episodes
                if isinstance(item, dict)
                and item.get("candidate_id") == EXPECTED["candidate_id"]
                and item.get("episode_version") == "v2.30"
                and item.get("patch_sha256") != EXPECTED["patch_sha256"]
            ]
            expect(not inconsistent, errors, f"{label} registry has inconsistent duplicate episode")

    expect(patch_provenance.get("status") == "PASS", errors, "patch provenance not PASS")
    expect(patch_provenance.get("patch_sha256") == EXPECTED["patch_sha256"], errors, "patch provenance SHA mismatch")
    expect(patch_provenance.get("patch_file_sha256_matches") is True, errors, "patch file hash mismatch")
    expect(patch_provenance.get("source_only") is True, errors, "patch provenance not source-only")
    expect(not patch_provenance.get("forbidden_files"), errors, "patch provenance forbidden files")
    expect(replay.get("status") == "PASS", errors, "replay evidence not PASS")
    expect(replay.get("target_validation_status") == "PASS", errors, "replay target validation mismatch")
    expect(replay.get("target_validation_exit_status") == 0, errors, "replay target exit mismatch")
    expect(replay.get("duplicate_replay_status") == "PASS", errors, "replay duplicate mismatch")
    expect(replay.get("duplicate_replay_passed_replays") == 3, errors, "replay duplicate pass count mismatch")
    expect(replay.get("observed_reliability") == 1.0, errors, "replay reliability mismatch")
    expect(signature_history.get("status") == "PASS", errors, "signature history record not PASS")
    expect(signature_history.get("semantic_failure_signature_hash") == EXPECTED["semantic_failure_signature_hash"], errors, "signature history semantic hash mismatch")
    expect(signature_history.get("signature_history_count", 0) >= 5, errors, "signature history incomplete")
    expect(signature_history.get("registry_lineage_transition_status") == "PASS", errors, "registry lineage carry-forward not PASS")

    expect(claim_v230.get("status") == "PASS", errors, "v2.30 claim boundary consolidation not PASS")
    expect(claim_v230.get("current_protocol_version") == "v2.13", errors, "v2.30 current protocol mismatch")
    expect(claim_v230.get("full_scoring") == "NOT_RUN", errors, "v2.30 full scoring mismatch")
    expect(claim_v230.get("memory_lift_status") == "undemonstrated", errors, "v2.30 memory lift mismatch")
    expect(claim_v230.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "v2.30 self-maintaining mismatch")

    expect(ledger_report.get("status") == "PASS", errors, "failure memory ledger report not PASS")
    expect(ledger_report.get("diagnostic_weight_update") == "bounded_success_marker", errors, "failure memory marker mismatch")
    expect(ledger_report.get("memory_lift_claimed") is False, errors, "failure memory claimed memory lift")
    expect(ledger_report.get("self_maintaining_software_claimed") is False, errors, "failure memory claimed self-maintaining")
    ledger_entries = ledger_after.get("entries") if isinstance(ledger_after.get("entries"), list) else []
    expect(
        any(
            isinstance(item, dict)
            and item.get("lane") == CAMPAIGN_ID
            and item.get("candidate_id") == EXPECTED["candidate_id"]
            and item.get("repair_episode_version") == "v2.30"
            and item.get("patch_sha256") == EXPECTED["patch_sha256"]
            and item.get("diagnostic_only") is True
            and item.get("memory_lift_claimed") is False
            for item in ledger_entries
        ),
        errors,
        "failure memory ledger v2.31 diagnostic entry missing",
    )

    expect(registry_status.get("status") == "PASS", errors, "external candidate registry status not PASS")
    expect(registry_status.get("py_bugger_candidate_present") is True, errors, "py-bugger registry candidate missing")
    expect(registry_status.get("registry_unchanged_by_v2_31") is True, errors, "v2.31 changed external candidate registry")
    expect(candidate.get("registry_review_status") == "reviewed", errors, "candidate not reviewed")
    expect(candidate.get("repo_url") == EXPECTED["repo_url"], errors, "candidate repo mismatch")
    expect(candidate.get("buggy_commit_sha") == EXPECTED["buggy_commit_sha"], errors, "candidate commit mismatch")
    expect(candidate.get("test_command") == EXPECTED["test_command"], errors, "candidate command mismatch")
    fresh_validation = registry_validator.validate_registry()
    expect(fresh_validation.get("registry_validation_status") == "PASS", errors, "fresh registry validation not PASS")

    expect(readiness.get("status") == "PASS", errors, "readiness plan not PASS")
    for key in ["candidate_selected_in_v2_31", "external_clone_attempted", "target_test_command_executed", "patch_generated", "repair_attempted", "s_engine_invoked"]:
        expect(readiness.get(key) is False, errors, f"readiness key {key} not false")
    requirements_text = "\n".join(next_requirements.get("requirements") or [])
    for phrase in [
        "public GitHub or public HTTPS Git repository",
        "exact 40-character buggy commit SHA",
        "native target test file physically present in buggy commit tree",
        "no generated/manual reproducer",
        "no external network dependency during test command",
        "no BugsInPy checkout/materialization",
        "no fixed/later/gold/synthetic evidence",
        "environment lock source physically present in buggy commit tree",
    ]:
        expect(phrase in requirements_text, errors, f"next candidate requirement missing: {phrase}")
    memory_text = "\n".join(memory_requirements.get("future_requirements") or [])
    for phrase in [
        "pre-registered comparison before patch generation",
        "memory-enabled vs no-memory or reduced-memory conditions",
        "no access to successful patch bytes in baseline condition",
        "frozen prompt/context hashes",
        "aggregate criteria across more than one candidate",
    ]:
        expect(phrase in memory_text, errors, f"memory-lift requirement missing: {phrase}")
    expect(memory_requirements.get("memory_lift_status") == "undemonstrated", errors, "memory requirements overclaim memory lift")

    expect(roadmap.get("status") == "PASS", errors, "roadmap carry-forward not PASS")
    expect(resolution.get("status") == "PASS", errors, "resolution diagnostic not PASS")
    expect(resolution.get("scoreable_external_repair_episode_count") == 1, errors, "resolution episode count mismatch")
    expect(public_language.get("status") == "PASS", errors, "public language audit failed")
    for term in hidden_public_terms():
        expect(term not in (OUTPUT_ROOT / "campaign_summary.md").read_text(encoding="utf-8"), errors, f"blocked term in campaign summary: {term}")
        expect(term not in (OUTPUT_ROOT / "scoreable_episode_public_summary.md").read_text(encoding="utf-8"), errors, f"blocked term in public summary: {term}")

    expect(claim.get("status") == "PASS", errors, "v2.31 claim boundary not PASS")
    expect(claim.get("current_protocol_version") == "v2.13", errors, "current protocol changed")
    expect(claim.get("v2_30_promoted_to_current") is False, errors, "v2.30 promoted to current")
    expect(claim.get("v2_31_promoted_to_current") is False, errors, "v2.31 promoted to current")
    expect(claim.get("full_scoring") == "NOT_RUN", errors, "full scoring changed")
    expect(claim.get("full_scoring_allowed") is False, errors, "full scoring allowed")
    expect(claim.get("memory_lift_status") == "undemonstrated", errors, "memory lift claimed")
    expect(claim.get("self_maintaining_software_status") == "false/not_demonstrated", errors, "self-maintaining claim changed")
    expect(claim.get("final_non_ansible_positive_memory_count") == 0, errors, "non-Ansible positive-memory count changed")
    expect(claim.get("scoreable_external_repair_episode_count") == 1, errors, "claim episode count mismatch")
    expect(claim.get("selected_candidate_scoreable") is True, errors, "claim candidate scoreable mismatch")
    expect(claim.get("selected_candidate_positive_memory_only") is False, errors, "claim positive-memory-only mismatch")
    for key in ["no_new_candidate_selected", "no_external_clone_attempted", "no_test_command_executed", "no_patch_generated", "no_repair_attempted", "no_s_engine_invoked"]:
        expect(claim.get(key) is True, errors, f"claim {key} not true")
    expect(claim.get("pysnooper1_reopened") is False, errors, "PySnooper:1 reopened")
    expect(claim.get("pysnooper2_pursued") is False, errors, "PySnooper:2 pursued")
    expect(claim.get("ansible_candidate_selected") is False, errors, "Ansible candidate selected")
    expect(claim.get("bugsinpy_active_candidate_acquisition_used") is False, errors, "BugsInPy active candidate acquisition used")

    expect(matrix.get("capabilities", {}).get("scoreable_external_repair_episode_consolidation") == "implemented_active", errors, "capability matrix v2.31 status missing")
    expect(matrix.get("capabilities", {}).get("next_candidate_readiness") == "prepared_no_candidate_selected", errors, "capability matrix readiness missing")
    expect(backlog.get("scoreable_external_repair_episode_consolidation_v2_31", {}).get("status") == "implemented_active", errors, "backlog v2.31 status missing")
    expect(resolution_map.get("resolution_bands", {}).get("v2.31", {}).get("status") == "consolidated_one_episode_not_full_scoring", errors, "resolution map v2.31 missing")
    expect(section_present(README_PATH, "v2.31 scoreable external repair episode consolidation"), errors, "README v2.31 section missing")
    expect(section_present(ROADMAP_PATH, "v2.31 Scoreable External Repair Episode Consolidation"), errors, "roadmap v2.31 section missing")
    expect(section_present(CAPABILITY_PLAN_PATH, "v2.31 consolidation status"), errors, "capability plan v2.31 section missing")
    expect(section_present(RESOLUTION_DOC_PATH, "v2.31 consolidation status"), errors, "resolution doc v2.31 section missing")
    expect(section_present(SHAREABLE_PATH, "v2.31 Scoreable External Repair Episode Consolidation"), errors, "shareable summary v2.31 section missing")
    audit_proof_ledger(proof, errors)

    print(f"v2.31 manifest entries checked: {checked}")
    for key in [
        "v2_30_scoreable_episode_ingest_status",
        "external_repair_episode_registry_status",
        "scoreable_external_repair_episode_count",
        "selected_candidate_id",
        "selected_candidate_scoreable",
        "selected_candidate_positive_memory_only",
        "target_validation_carry_forward_status",
        "duplicate_replay_carry_forward_status",
        "stochastic_replay_reliability_carry_forward_status",
        "failure_memory_ledger_update_status",
        "next_candidate_readiness_plan_status",
        "prospective_memory_lift_requirements_status",
        "roadmap_backlog_update_status",
        "public_language_audit_status",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "exact_blocker",
    ]:
        print(f"{key}={results.get(key)}")


def main() -> int:
    errors: list[str] = []
    if not OUTPUT_ROOT.is_dir():
        errors.append(f"missing output root: {OUTPUT_ROOT.relative_to(REPO_ROOT).as_posix()}")
    else:
        audit_outputs(errors)
    run_python_script("scripts/audit_v2_30_failure_signature_canonicalization_repair_lane.py", errors)
    current_audit = subprocess.run([sys.executable, "scripts/controllergate_audit.py", "--protocol", "current"], cwd=str(REPO_ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if current_audit.returncode != 0:
        errors.append("current protocol audit failed")
    current_dry_run = subprocess.run([sys.executable, "scripts/controllergate_run.py", "--protocol", "current", "--dry-run"], cwd=str(REPO_ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if current_dry_run.returncode != 0:
        errors.append("current protocol dry-run failed")
    if errors:
        print("v2.31 audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.31 audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
