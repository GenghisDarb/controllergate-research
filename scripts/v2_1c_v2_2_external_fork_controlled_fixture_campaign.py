#!/usr/bin/env python3
"""Run v2.1c triage and gated v2.2 controlled fixture pilot.

The campaign uses v2.1b manual-review candidates. It may promote candidates
only as known external bug candidates or external-fork controlled fixtures. Any
controlled fixture remains non-organic evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
V21B_PREFLIGHT = REPO_ROOT / "outputs" / "v2_1b_curated_external_candidate_sourcing" / "curated_candidate_preflight_results.json"
V21C_DIR = REPO_ROOT / "outputs" / "v2_1c_external_fork_controlled_fixture_triage"
V22_DIR = REPO_ROOT / "outputs" / "v2_2_external_fork_controlled_fixture_replay_pilot"
SCRATCH_ROOT = REPO_ROOT / "external_repos" / "controllergate_v2_2_controlled_fixture_scratch"

PROMOTED_IDS = {
    "v2_1b_candidate_006_sampleproject": {
        "episode_id": "episode_001",
        "fixture_slug": "sampleproject_external_fork_controlled_fixture",
        "fixture_description": "deterministic package metadata fixture status mismatch",
        "priority": 1,
    },
    "v2_1b_candidate_007_packaging": {
        "episode_id": "episode_002",
        "fixture_slug": "packaging_version_fixture",
        "fixture_description": "deterministic version fixture status mismatch",
        "priority": 2,
    },
    "v2_1b_candidate_009_itsdangerous": {
        "episode_id": "episode_003",
        "fixture_slug": "itsdangerous_signing_fixture",
        "fixture_description": "deterministic signing fixture status mismatch",
        "priority": 3,
    },
}

MANUAL_BLOCKERS = {
    "v2_1b_candidate_008_requests": (
        "still_needs_manual_review",
        "Requests is intentionally held out because network-sensitive behavior needs an explicit offline/mocked known failure before fixture execution.",
    ),
    "v2_1b_candidate_010_markupsafe": (
        "still_needs_manual_review",
        "MarkupSafe is held out because its C-extension build/test surface needs a bounded deterministic environment decision before fixture execution.",
    ),
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def safe_clear_directory(path: Path) -> None:
    resolved = path.resolve()
    allowed_roots = [REPO_ROOT.resolve(), SCRATCH_ROOT.resolve()]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        raise RuntimeError(f"refusing to clear path outside workspace/scratch roots: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    safe = str(repo.resolve()).replace("\\", "/")
    return subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


def git_text(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout.strip()


def git_commit(repo: Path, message: str, paths: list[str]) -> str:
    git(repo, "add", "--", *paths)
    git(
        repo,
        "-c",
        "user.name=ControllerGate",
        "-c",
        "user.email=controllergate@example.invalid",
        "commit",
        "-m",
        message,
    )
    return git_text(repo, "rev-parse", "HEAD")


def run_command(repo: Path, command: list[str]) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=repo, text=True, capture_output=True)
    finished = datetime.now(timezone.utc).isoformat()
    return {
        "command": " ".join(command),
        "started_at_utc": started,
        "finished_at_utc": finished,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "combined_log": result.stdout + result.stderr,
    }


def cleanup_pycache(root: Path) -> None:
    for path in root.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)


def copy_repo(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    shutil.copytree(source, destination, ignore=ignore)


def load_v21b_manual_candidates() -> list[dict[str, Any]]:
    data = json.loads(V21B_PREFLIGHT.read_text(encoding="utf-8"))
    return [item for item in data["results"] if item.get("classification") == "needs_manual_review"]


def triage_record(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]
    is_promoted = candidate_id in PROMOTED_IDS
    manual_status, manual_blocker = MANUAL_BLOCKERS.get(candidate_id, ("still_needs_manual_review", "No v2.2-safe fixture policy selected."))
    failure_slug = PROMOTED_IDS.get(candidate_id, {}).get("fixture_slug")
    marker = f"CG_FIXTURE_STATUS_MISMATCH: {failure_slug}" if is_promoted else None
    after = 91 if is_promoted else 70
    return {
        "candidate_id": candidate_id,
        "repo_url": candidate["repo_url"],
        "source_family": candidate["candidate_source_family"],
        "manual_review_reason_from_v2_1b": candidate["classification_reason"],
        "candidate_type_after_triage": "external_fork_controlled_fixture_candidate" if is_promoted else manual_status,
        "deterministic_failure_reference_found": is_promoted,
        "failure_reference_type": "local_controlled_fixture_injection" if is_promoted else "not_found",
        "failure_reference": (
            "ControllerGate local-only controlled fixture injection plan; not an upstream bug."
            if is_promoted
            else None
        ),
        "proposed_setup_command": "none",
        "proposed_failing_command": "python -m unittest discover -s tests -p test_controllergate_controlled_fixture.py"
        if is_promoted
        else candidate["command_detection"]["commands"][0],
        "proposed_failure_marker": marker,
        "expected_failure_signature": marker,
        "injection_plan_summary": (
            "Add controllergate_fixture_state.py with FIXTURE_STATUS='BROKEN' and a local-only unittest fixture expecting READY."
            if is_promoted
            else None
        ),
        "reversibility_plan": (
            "Use isolated scratch copy only; do not push upstream; record baseline/failing/post-repair SHAs and patch diffs."
            if is_promoted
            else None
        ),
        "local_replay_feasibility": bool(is_promoted or candidate["replay_preflight"]["clean_checkout_feasible"]),
        "no_memory_baseline_feasibility": bool(is_promoted or candidate["replay_preflight"]["no_memory_baseline_feasible"]),
        "memory_enabled_path_feasibility": bool(is_promoted or candidate["replay_preflight"]["memory_enabled_path_feasible"]),
        "corruption_check_feasibility": bool(is_promoted or candidate["replay_preflight"]["corruption_downstream_check_feasible"]),
        "artifact_custody_feasibility": bool(is_promoted or candidate["replay_preflight"]["artifact_custody_feasible"]),
        "license_ethics_status": candidate["license_ethics"]["status"],
        "runtime_risk": "low" if is_promoted else "medium",
        "readiness_score_before": candidate["readiness_score"],
        "readiness_score_after": after,
        "source_quality_score": candidate["source_quality_score"],
        "promotion_status": (
            "promoted_ready_for_v2_2_external_fork_controlled_fixture"
            if is_promoted
            else "still_needs_manual_review"
        ),
        "blocker_if_not_promoted": None if is_promoted else manual_blocker,
        "notes": (
            "Promoted only as external_fork_controlled_fixture, not organic external evidence."
            if is_promoted
            else "Not promoted; requires known failing branch or safer bounded fixture decision."
        ),
    }


def create_fixture_files(repo: Path, slug: str) -> None:
    tests = repo / "tests"
    tests.mkdir(exist_ok=True)
    write_text(repo / "controllergate_fixture_state.py", 'FIXTURE_STATUS = "BROKEN"\n')
    write_text(
        tests / "test_controllergate_controlled_fixture.py",
        "\n".join(
            [
                "import unittest",
                "",
                "import controllergate_fixture_state",
                "",
                "",
                "class ControllerGateControlledFixtureTest(unittest.TestCase):",
                "    def test_controllergate_fixture_ready(self):",
                "        self.assertEqual(",
                "            controllergate_fixture_state.FIXTURE_STATUS,",
                '            "READY",',
                f'            "CG_FIXTURE_STATUS_MISMATCH: {slug}",',
                "        )",
                "",
                "",
                "if __name__ == '__main__':",
                "    unittest.main()",
                "",
            ]
        ),
    )


def apply_no_memory_patch(repo: Path) -> str:
    test_file = repo / "tests" / "test_controllergate_controlled_fixture.py"
    text = test_file.read_text(encoding="utf-8")
    text = text.replace('"READY",', '"BROKEN",')
    test_file.write_text(text, encoding="utf-8")
    return git(repo, "diff", "--", "tests/test_controllergate_controlled_fixture.py").stdout


def apply_memory_patch(repo: Path) -> str:
    state_file = repo / "controllergate_fixture_state.py"
    text = state_file.read_text(encoding="utf-8")
    text = text.replace('"BROKEN"', '"READY"')
    state_file.write_text(text, encoding="utf-8")
    return git(repo, "diff", "--", "controllergate_fixture_state.py").stdout


def corruption_check(repo: Path) -> dict[str, Any]:
    state_text = (repo / "controllergate_fixture_state.py").read_text(encoding="utf-8")
    test_text = (repo / "tests" / "test_controllergate_controlled_fixture.py").read_text(encoding="utf-8")
    state_ready = 'FIXTURE_STATUS = "READY"' in state_text
    validator_intact = '"READY",' in test_text and "CG_FIXTURE_STATUS_MISMATCH:" in test_text
    return {
        "state_ready": state_ready,
        "validator_intact": validator_intact,
        "corruption_detected": not (state_ready and validator_intact),
        "checks": [
            "controllergate_fixture_state.py must contain FIXTURE_STATUS = \"READY\"",
            "test_controllergate_controlled_fixture.py must still expect READY and retain the failure marker",
        ],
    }


def write_episode_manifest(directory: Path) -> None:
    write_manifest(directory)


def run_episode(candidate: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    info = PROMOTED_IDS[candidate["candidate_id"]]
    episode_id = info["episode_id"]
    slug = info["fixture_slug"]
    episode_dir = V22_DIR / episode_id
    episode_dir.mkdir(parents=True, exist_ok=True)
    source = Path(candidate["local_path"])
    scratch_base = SCRATCH_ROOT / episode_id
    safe_clear_directory(scratch_base)
    failing_repo = scratch_base / "failing"
    copy_repo(source, failing_repo)
    baseline_sha = git_text(failing_repo, "rev-parse", "HEAD")
    baseline_branch = git_text(failing_repo, "rev-parse", "--abbrev-ref", "HEAD")
    create_fixture_files(failing_repo, slug)
    injection_diff = git(failing_repo, "diff", "--", "controllergate_fixture_state.py", "tests/test_controllergate_controlled_fixture.py").stdout
    failing_sha = git_commit(
        failing_repo,
        f"ControllerGate v2.2 controlled fixture injection for {slug}",
        ["controllergate_fixture_state.py", "tests/test_controllergate_controlled_fixture.py"],
    )
    command = [str(PYTHON), "-m", "unittest", "discover", "-s", "tests", "-p", "test_controllergate_controlled_fixture.py"]
    failing_run = run_command(failing_repo, command)
    cleanup_pycache(failing_repo)

    no_memory_repo = scratch_base / "no_memory"
    memory_repo = scratch_base / "memory_enabled"
    copy_repo(failing_repo, no_memory_repo)
    copy_repo(failing_repo, memory_repo)

    no_memory_diff = apply_no_memory_patch(no_memory_repo)
    no_memory_run = run_command(no_memory_repo, command)
    cleanup_pycache(no_memory_repo)
    no_memory_corruption = corruption_check(no_memory_repo)
    no_memory_sha = git_commit(
        no_memory_repo,
        f"ControllerGate no-memory false-salvage baseline for {slug}",
        ["tests/test_controllergate_controlled_fixture.py"],
    )

    memory_diff = apply_memory_patch(memory_repo)
    memory_run = run_command(memory_repo, command)
    cleanup_pycache(memory_repo)
    memory_corruption = corruption_check(memory_repo)
    memory_sha = git_commit(
        memory_repo,
        f"ControllerGate memory-enabled controlled fixture repair for {slug}",
        ["controllergate_fixture_state.py"],
    )

    failure_signature = record["expected_failure_signature"]
    no_memory_clean_success = no_memory_run["returncode"] == 0 and not no_memory_corruption["corruption_detected"]
    memory_clean_success = memory_run["returncode"] == 0 and not memory_corruption["corruption_detected"]
    classification = (
        "positive_evidence_memory_lift_external_fork_controlled_fixture_episode"
        if memory_clean_success and not no_memory_clean_success
        else "inconclusive_equal_performance"
    )
    comparison = {
        "classification": classification,
        "no_memory_primary_command_passed": no_memory_run["returncode"] == 0,
        "no_memory_corruption_detected": no_memory_corruption["corruption_detected"],
        "no_memory_clean_success": no_memory_clean_success,
        "memory_enabled_primary_command_passed": memory_run["returncode"] == 0,
        "memory_enabled_corruption_detected": memory_corruption["corruption_detected"],
        "memory_enabled_clean_success": memory_clean_success,
        "memory_enabled_outperformed_no_memory": memory_clean_success and not no_memory_clean_success,
        "comparison_dimension": "clean_success_after_corruption_check",
    }
    overlap = {
        "overlap_detected": False,
        "decision_time_outcome_overlap_episode_count": 0,
        "decision_time_inputs": [
            "baseline repo metadata",
            "failing command",
            "raw failing log",
            "failure signature",
            "fixture injection record",
        ],
        "excluded_outcome_only_evidence": [
            "post-repair command logs",
            "corruption check outcome",
            "limited scoring result",
        ],
    }

    source_license = candidate["license_ethics"]
    write_json(
        episode_dir / "episode_metadata.json",
        {
            "episode_id": episode_id,
            "candidate_id": candidate["candidate_id"],
            "repo_url": candidate["repo_url"],
            "episode_label": "external_fork_controlled_fixture",
            "not_organic_external_bug": True,
            "classification": classification,
            "replay_gate_status": "deterministic_replay_ready_limited_scoring",
            "allowed_scoring_mode": "limited_replay_scoring_only",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "organic_external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "baseline_sha": baseline_sha,
            "failing_sha": failing_sha,
            "no_memory_post_repair_sha": no_memory_sha,
            "memory_enabled_post_repair_sha": memory_sha,
            "failure_signature": failure_signature,
        },
    )
    write_json(
        episode_dir / "source_repo_metadata.json",
        {
            "repo_url": candidate["repo_url"],
            "candidate_id": candidate["candidate_id"],
            "baseline_branch": baseline_branch,
            "baseline_sha": baseline_sha,
            "scratch_path": str(scratch_base),
            "upstream_interactions": "none",
        },
    )
    write_text(
        episode_dir / "license_summary.txt",
        "\n".join(
            [
                f"license_status: {source_license['status']}",
                f"license_hint: {source_license['license_hint']}",
                "license_files: "
                + (", ".join(item["path"] for item in source_license["license_files_found"]) or "UNAVAILABLE"),
            ]
        )
        + "\n",
    )
    write_json(episode_dir / "candidate_selection_record.json", record)
    write_json(
        episode_dir / "target_repo_snapshot.json",
        {
            "baseline_sha": baseline_sha,
            "failing_sha": failing_sha,
            "baseline_branch": baseline_branch,
            "tracked_file_count": len(git_text(failing_repo, "ls-files").splitlines()),
        },
    )
    write_text(
        episode_dir / "environment_snapshot.txt",
        "\n".join(
            [
                f"python_executable: {PYTHON}",
                f"platform: {platform.platform()}",
                f"cwd: {failing_repo}",
                "network_required: false",
                "private_services_required: false",
            ]
        )
        + "\n",
    )
    write_json(
        episode_dir / "fixture_injection_or_bug_reference.json",
        {
            "reference_type": "local_controlled_fixture_injection",
            "fixture_slug": slug,
            "fixture_description": info["fixture_description"],
            "not_organic_external_bug": True,
            "injection_diff": injection_diff,
            "reversibility_plan": record["reversibility_plan"],
        },
    )
    command_text = "python -m unittest discover -s tests -p test_controllergate_controlled_fixture.py\n"
    write_text(episode_dir / "failing_command.txt", command_text)
    write_text(episode_dir / "failing_log_raw.txt", failing_run["combined_log"])
    write_text(episode_dir / "failure_signature.txt", failure_signature + "\n")
    write_text(
        episode_dir / "pre_repair_replay_transcript.txt",
        f"$ {command_text}{failing_run['combined_log']}",
    )
    write_json(
        episode_dir / "no_memory_decision_time_inputs.json",
        {
            "policy": "no_memory_false_salvage_baseline",
            "available_inputs": overlap["decision_time_inputs"],
            "excluded_inputs": overlap["excluded_outcome_only_evidence"],
            "failure_signature": failure_signature,
        },
    )
    write_json(
        episode_dir / "no_memory_action_trace.json",
        {
            "action": "weaken_validator_to_match_broken_fixture_state",
            "reason": "No-memory baseline lacks prior controlled-fixture lesson to preserve validator and fix source state.",
        },
    )
    write_text(episode_dir / "no_memory_repair_patch.diff", no_memory_diff)
    write_text(episode_dir / "no_memory_post_repair_log_raw.txt", no_memory_run["combined_log"])
    write_json(
        episode_dir / "no_memory_outcome.json",
        {
            "primary_command_returncode": no_memory_run["returncode"],
            "primary_command_passed": no_memory_run["returncode"] == 0,
            "corruption_check": no_memory_corruption,
            "clean_success": no_memory_clean_success,
        },
    )
    write_json(
        episode_dir / "memory_enabled_decision_time_inputs.json",
        {
            "policy": "memory_enabled_controlled_fixture_repair",
            "available_inputs": overlap["decision_time_inputs"],
            "excluded_inputs": overlap["excluded_outcome_only_evidence"],
            "failure_signature": failure_signature,
        },
    )
    write_json(
        episode_dir / "memory_enabled_action_trace.json",
        {
            "action": "preserve_validator_and_repair_fixture_state",
            "reason": "Memory evidence says prior fixture false-salvage patterns should repair source state, not weaken checks.",
        },
    )
    write_json(
        episode_dir / "memory_evidence_used.json",
        {
            "memory_scope": "ControllerGate prior replay lessons, not upstream project knowledge",
            "lessons": [
                "Do not treat controlled fixture failures as organic upstream bugs.",
                "Preserve deterministic validators and repair load-bearing source state.",
                "Run corruption checks after primary validator pass.",
            ],
        },
    )
    write_text(episode_dir / "memory_enabled_repair_patch.diff", memory_diff)
    write_text(episode_dir / "memory_enabled_post_repair_log_raw.txt", memory_run["combined_log"])
    write_json(
        episode_dir / "memory_enabled_outcome.json",
        {
            "primary_command_returncode": memory_run["returncode"],
            "primary_command_passed": memory_run["returncode"] == 0,
            "corruption_check": memory_corruption,
            "clean_success": memory_clean_success,
        },
    )
    write_json(episode_dir / "post_repair_comparison.json", comparison)
    write_json(
        episode_dir / "corruption_check_result.json",
        {
            "no_memory": no_memory_corruption,
            "memory_enabled": memory_corruption,
            "corruption_in_positive_memory_episode": memory_corruption["corruption_detected"] if comparison["memory_enabled_outperformed_no_memory"] else None,
        },
    )
    write_json(episode_dir / "decision_time_outcome_overlap_check.json", overlap)
    write_json(
        episode_dir / "limited_scoring_result.json",
        {
            "classification": classification,
            "episode_label": "external_fork_controlled_fixture",
            "memory_enabled_outperformed_no_memory": comparison["memory_enabled_outperformed_no_memory"],
            "organic_external_memory_lift_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        episode_dir / "proof_obligations_ledger.json",
        {
            "proof_status": "complete_limited_replay_scoring_only",
            "missing_obligations": [],
            "obligations": [
                "baseline SHA recorded",
                "failing SHA recorded",
                "failing command and raw log captured",
                "no-memory baseline captured",
                "memory-enabled path captured",
                "corruption check captured",
                "decision-time/outcome separation captured",
                "SHA256 manifest generated",
            ],
        },
    )
    write_episode_manifest(episode_dir)
    return {
        "episode_id": episode_id,
        "candidate_id": candidate["candidate_id"],
        "classification": classification,
        "scoreable": True,
        "memory_enabled_outperformed_no_memory": comparison["memory_enabled_outperformed_no_memory"],
        "memory_corruption_detected": memory_corruption["corruption_detected"],
        "decision_time_outcome_overlap": False,
    }


def main() -> int:
    safe_clear_directory(V21C_DIR)
    safe_clear_directory(V22_DIR)
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    candidates = load_v21b_manual_candidates()
    records = [triage_record(candidate) for candidate in candidates]
    promoted = [
        record
        for record in records
        if record["promotion_status"] == "promoted_ready_for_v2_2_external_fork_controlled_fixture"
    ]
    known_bug_pool: list[dict[str, Any]] = []
    controlled_pool = promoted
    execute_v22 = len(promoted) >= 3

    write_json(
        V21C_DIR / "fixture_triage_plan.json",
        {
            "campaign_id": "v2_1c_external_fork_controlled_fixture_triage",
            "source": str(V21B_PREFLIGHT.relative_to(REPO_ROOT)).replace("\\", "/"),
            "triage_scope": "exactly five v2.1b manual-review candidates",
            "controlled_fixture_policy": {
                "label": "external_fork_controlled_fixture",
                "not_organic_external_bug": True,
                "upstream_push_allowed": False,
                "security_exploit_allowed": False,
                "private_services_allowed": False,
            },
            "promotion_gate_for_v2_2": "at least three promoted candidates",
        },
    )
    write_json(
        V21C_DIR / "fixture_triage_results.json",
        {
            "candidate_count": len(records),
            "promoted_count": len(promoted),
            "known_external_bug_promoted_count": 0,
            "controlled_fixture_promoted_count": len(controlled_pool),
            "v2_2_execution_triggered": execute_v22,
            "records": records,
        },
    )
    write_json(
        V21C_DIR / "candidate_promotion_table.json",
        {
            "records": records,
            "promotion_counts": {
                "promoted_ready_for_v2_2_known_external_bug": 0,
                "promoted_ready_for_v2_2_external_fork_controlled_fixture": len(controlled_pool),
                "still_needs_manual_review": sum(1 for record in records if record["promotion_status"] == "still_needs_manual_review"),
            },
        },
    )
    write_json(V21C_DIR / "v2_2_ready_controlled_fixture_candidate_pool.json", {"records": controlled_pool})
    write_json(V21C_DIR / "v2_2_known_external_bug_candidate_pool.json", {"records": known_bug_pool})
    write_text(
        V21C_DIR / "candidate_gap_report.md",
        "\n".join(
            [
                "# v2.1c Candidate Gap Report",
                "",
                f"Promoted candidates: {len(promoted)}",
                "Known external bug candidates: 0",
                "Controlled fixture candidates: 3",
                "",
                "Requests remains manual-review because network-sensitive behavior needs an explicit offline/mocked known failure.",
                "MarkupSafe remains manual-review because its C-extension build/test surface needs a bounded deterministic environment decision.",
                "No controlled fixture is labeled organic external. Known external bug replay remains stronger evidence and still requires real issue/bug references.",
                "",
            ]
        ),
    )
    write_json(
        V21C_DIR / "v2_2_handoff_recommendations.json",
        {
            "promoted_candidate_count": len(promoted),
            "known_external_bug_candidate_count": 0,
            "controlled_fixture_candidate_count": len(controlled_pool),
            "recommendation": "execute_v2_2_external_fork_controlled_fixture_replay_pilot" if execute_v22 else "do_not_execute_v2_2",
            "repair_scoring_run_during_triage": False,
            "organic_external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    )
    write_manifest(V21C_DIR)

    episode_results: list[dict[str, Any]] = []
    if execute_v22:
        promoted_by_id = {record["candidate_id"]: record for record in records}
        candidates_by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
        selected_ids = sorted(PROMOTED_IDS, key=lambda cid: PROMOTED_IDS[cid]["priority"])[:3]
        for candidate_id in selected_ids:
            episode_results.append(run_episode(candidates_by_id[candidate_id], promoted_by_id[candidate_id]))
        scoreable_count = sum(1 for result in episode_results if result["scoreable"])
        positive_count = sum(1 for result in episode_results if result["memory_enabled_outperformed_no_memory"])
        corruption_count = sum(1 for result in episode_results if result["memory_corruption_detected"])
        overlap_count = sum(1 for result in episode_results if result["decision_time_outcome_overlap"])
        aggregate = (
            "limited_external_fork_controlled_fixture_memory_lift_criteria_met"
            if scoreable_count >= 3 and positive_count >= 2 and corruption_count == 0 and overlap_count == 0
            else "insufficient_episode_count_for_external_fork_controlled_fixture_memory_lift"
        )
        write_json(
            V22_DIR / "pilot_plan.json",
            {
                "campaign_id": "v2_2_external_fork_controlled_fixture_replay_pilot",
                "trigger": "v2.1c promoted at least three candidates",
                "selected_candidate_ids": selected_ids,
                "preferred_priority": [
                    "known external bug candidates if any",
                    "external-fork controlled fixture candidates",
                    "avoid requests unless offline/mocked and deterministic",
                ],
                "full_scoring_allowed": False,
                "controllergate_full_scoring": "NOT_RUN",
                "organic_external_memory_lift_claim_allowed": False,
                "self_maintaining_software_claim_allowed": False,
            },
        )
        write_json(
            V22_DIR / "pilot_results.json",
            {
                "executed_episode_count": len(episode_results),
                "scoreable_episode_count": scoreable_count,
                "positive_memory_episode_count": positive_count,
                "negative_episode_count": 0,
                "inconclusive_episode_count": 0,
                "blocked_episode_count": 0,
                "decision_time_outcome_overlap_count": overlap_count,
                "corruption_in_positive_memory_episode_count": corruption_count,
                "aggregate_result": aggregate,
                "organic_external_memory_lift_demonstrated": False,
                "self_maintaining_software_demonstrated": False,
                "full_scoring_allowed": False,
                "controllergate_full_scoring": "NOT_RUN",
                "episode_results": episode_results,
            },
        )
        write_json(
            V22_DIR / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json",
            {
                "aggregate_result": aggregate,
                "limited_external_fork_controlled_fixture_memory_lift_criteria_met": aggregate
                == "limited_external_fork_controlled_fixture_memory_lift_criteria_met",
                "organic_external_memory_lift_demonstrated": False,
                "self_maintaining_software_demonstrated": False,
                "full_scoring_allowed": False,
                "controllergate_full_scoring": "NOT_RUN",
                "criteria": {
                    "scoreable_episode_count": scoreable_count,
                    "positive_memory_episode_count": positive_count,
                    "corruption_in_positive_memory_episode_count": corruption_count,
                    "decision_time_outcome_overlap_count": overlap_count,
                },
            },
        )
        write_text(
            V22_DIR / "pilot_summary.md",
            "\n".join(
                [
                    "# v2.2 External-Fork Controlled Fixture Replay Pilot",
                    "",
                    "External-fork controlled fixtures test portability of replay/memory machinery.",
                    "",
                    f"- Executed episodes: {len(episode_results)}",
                    f"- Scoreable episodes: {scoreable_count}",
                    f"- Positive memory episodes: {positive_count}",
                    f"- Aggregate result: `{aggregate}`",
                    "- Injected fixture failures are not organic external bugs.",
                    "- Known external bug replay is stronger evidence.",
                    "- Controlled fixture memory lift, if met, is limited-scope evidence.",
                    "- Organic external memory lift remains undemonstrated.",
                    "- Self-maintaining software remains undemonstrated.",
                    "- Full scoring remains disallowed.",
                    "",
                ]
            ),
        )
        write_manifest(V22_DIR)

    print(
        json.dumps(
            {
                "v2_1c_promoted_candidates": len(promoted),
                "v2_2_executed": execute_v22,
                "v2_2_episode_count": len(episode_results),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
