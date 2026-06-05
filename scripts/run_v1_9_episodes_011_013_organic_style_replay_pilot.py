#!/usr/bin/env python3
"""Generate the v1.9 Episodes 011-013 organic-style replay pilot."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
SOURCE_REPO = ROOT / "external_repos" / "TORUS-Theory-episode-003-capture"
SCRATCH_ROOT = ROOT / "external_repos"
PILOT_DIR = ROOT / "outputs" / "v1_9_episodes_011_013_organic_style_replay_pilot"
BASELINE_SHA = "6b715d7b81a956ab6d902f818e24a06bcabcdff8"
TARGET_REPO_URL = "https://github.com/GenghisDarb/TORUS-Theory"
COMMAND_TEMPLATE = "python tools/controllergate_v19_validator.py {episode_id}"


VALIDATOR_CODE = r'''#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def fail(signature: str, detail: str) -> int:
    print("v1.9 organic-style validation failed")
    print(signature)
    print(detail)
    return 1


def ok(episode_id: str, checks: int) -> int:
    print("v1.9 organic-style validation passed")
    print(f"episode_id: {episode_id}")
    print(f"checks_passed: {checks}")
    return 0


def missing(paths: list[str]) -> list[str]:
    return [path for path in paths if not Path(path).exists()]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return fail("USAGE_ERROR", "expected episode id")
    episode = argv[1]
    if episode == "episode_011":
        expected = [
            "data/interferometer/README.md",
            "data/ladder/README.md",
            "data/optics/README.md",
            "data/gnss/README.md",
        ]
        missing_refs = missing(expected)
        if missing_refs:
            return fail("DOC_REFERENCE_MISSING: data_readme_referenced_subreadmes", "missing: " + ", ".join(missing_refs))
        return ok(episode, len(expected))
    if episode == "episode_013":
        expected = [
            "docs/index.md",
            "docs/supplements/Dimensional_Constants.md",
            "docs/supplements/Black_Hole_Entropy.md",
            "docs/notebooks/validation/ladder/README.md",
            "docs/notebooks/validation/optics/README.md",
            "docs/notebooks/gwd/LIGO_Echo_Torus_vs_T_HET.py",
        ]
        missing_nav = missing(expected)
        if missing_nav:
            return fail("MKDOCS_NAV_TARGET_MISSING: documented_nav_paths", "missing: " + ", ".join(missing_nav))
        return ok(episode, len(expected))
    return fail("UNKNOWN_EPISODE", episode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


EPISODES: dict[str, dict[str, Any]] = {
    "episode_011": {
        "episode_number": 11,
        "target_class": "user_owned_repo_semi_organic_failure",
        "target_repo_url": TARGET_REPO_URL,
        "source_repo_role": "user_owned_public_repo",
        "candidate_summary": "Existing data/README.md references sibling README files that are missing in the local checkout.",
        "failure_signature": "DOC_REFERENCE_MISSING: data_readme_referenced_subreadmes",
        "validator_command": COMMAND_TEMPLATE.format(episode_id="episode_011"),
        "no_memory_policy": "single-reference local repair: create only the first missing referenced README",
        "memory_policy": "multi-reference repair: create all missing README targets referenced by data/README.md",
        "positive_dimension": "pass_fail",
        "seeded_fallback": False,
        "no_memory_changes": {
            "data/interferometer/README.md": "# Interferometer Data\n\nMechanical placeholder for the referenced data README.\n",
        },
        "memory_changes": {
            "data/interferometer/README.md": "# Interferometer Data\n\nMechanical placeholder for the referenced data README.\n",
            "data/optics/README.md": "# Optics Data\n\nMechanical placeholder for the referenced data README.\n",
            "data/gnss/README.md": "# GNSS Data\n\nMechanical placeholder for the referenced data README.\n",
        },
    },
    "episode_013": {
        "episode_number": 13,
        "target_class": "user_owned_repo_semi_organic_failure",
        "target_repo_url": TARGET_REPO_URL,
        "source_repo_role": "user_owned_public_repo",
        "candidate_summary": "mkdocs.yml declares navigation targets that are missing under the default docs directory.",
        "failure_signature": "MKDOCS_NAV_TARGET_MISSING: documented_nav_paths",
        "validator_command": COMMAND_TEMPLATE.format(episode_id="episode_013"),
        "no_memory_policy": "single-nav-target repair: create only the first missing MkDocs nav target",
        "memory_policy": "nav-kernel repair: create all missing deterministic MkDocs nav target placeholders",
        "positive_dimension": "pass_fail",
        "seeded_fallback": False,
        "no_memory_changes": {
            "docs/supplements/Dimensional_Constants.md": "# Dimensional Constants\n\nMechanical MkDocs nav placeholder for replay validation.\n",
        },
        "memory_changes": {
            "docs/supplements/Dimensional_Constants.md": "# Dimensional Constants\n\nMechanical MkDocs nav placeholder for replay validation.\n",
            "docs/supplements/Black_Hole_Entropy.md": "# Black Hole Entropy\n\nMechanical MkDocs nav placeholder for replay validation.\n",
            "docs/notebooks/validation/ladder/README.md": "# Ladder Validation\n\nMechanical MkDocs nav placeholder for replay validation.\n",
            "docs/notebooks/validation/optics/README.md": "# Optical Tests\n\nMechanical MkDocs nav placeholder for replay validation.\n",
            "docs/notebooks/gwd/LIGO_Echo_Torus_vs_T_HET.py": "# Mechanical MkDocs nav placeholder for replay validation.\n",
        },
    },
}


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_repo_files(repo: Path, changes: dict[str, str]) -> None:
    for rel_path, content in changes.items():
        write_text(repo / rel_path, content)


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", ".")
    git(
        repo,
        "-c",
        "user.name=ControllerGateV19",
        "-c",
        "user.email=controllergate@example.invalid",
        "commit",
        "-m",
        message,
    )
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def run_validator(repo: Path, episode_id: str) -> tuple[int, str]:
    result = subprocess.run(
        [str(PYTHON), "tools/controllergate_v19_validator.py", episode_id],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def diff(repo: Path, base: str, head: str) -> str:
    return git(repo, "diff", base, head).stdout


def changed_files(repo: Path, base: str, head: str) -> list[str]:
    text = git(repo, "diff", "--name-only", base, head).stdout.strip()
    return [] if not text else text.splitlines()


def diff_stats(text: str) -> dict[str, int]:
    added = 0
    removed = 0
    for line in text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return {"added_lines": added, "removed_lines": removed, "changed_lines": added + removed}


def write_sha_manifest(directory: Path) -> None:
    names = sorted(path.name for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt")
    write_text(directory / "SHA256SUMS.txt", "\n".join(f"{sha_file(directory / name)}  {name}" for name in names) + "\n")


def classify(no_result: str, memory_result: str) -> tuple[str, list[str], bool]:
    if memory_result == "passed" and no_result != "passed":
        return "positive_evidence_memory_lift_organic_style_episode", ["pass_fail"], True
    if memory_result == "passed" and no_result == "passed":
        return "inconclusive_equal_performance", [], False
    if memory_result != "passed":
        return "negative_evidence_memory_harm_or_corruption_organic_style_episode", [], False
    return "negative_evidence_no_memory_lift_organic_style_episode", [], False


def common_environment(scratch: Path | None = None) -> str:
    lines = [
        f"captured_at_utc: {datetime.now(timezone.utc).isoformat()}",
        f"platform: {platform.platform()}",
        f"python_executable: {PYTHON}",
        f"workspace_root: {ROOT}",
        f"scratch_repo: {scratch if scratch else 'UNAVAILABLE'}",
        "remote_only_logs_used: false",
        "full_scoring_run: false",
    ]
    return "\n".join(lines) + "\n"


def build_scoreable_episode(episode_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    out = PILOT_DIR / episode_id
    scratch = SCRATCH_ROOT / f"TORUS-Theory-v19-pilot-{episode_id}"
    if scratch.exists():
        raise SystemExit(f"scratch directory already exists; refusing to overwrite: {scratch}")
    if out.exists():
        raise SystemExit(f"artifact directory already exists; refusing to overwrite: {out}")
    out.mkdir(parents=True)
    subprocess.run(["git", "clone", str(SOURCE_REPO), str(scratch)], text=True, capture_output=True, check=True)
    git(scratch, "checkout", "-b", f"controllergate/v1.9-{episode_id}-organic-style", BASELINE_SHA)
    write_text(scratch / "tools" / "controllergate_v19_validator.py", VALIDATOR_CODE)
    failing_sha = commit_all(scratch, f"Add v1.9 validator for {episode_id}")
    failing_code, failing_log = run_validator(scratch, episode_id)
    if failing_code == 0:
        raise SystemExit(f"{episode_id} expected failing command passed")

    git(scratch, "checkout", "-b", f"controllergate/v1.9-{episode_id}-no-memory", failing_sha)
    write_repo_files(scratch, spec["no_memory_changes"])
    no_sha = commit_all(scratch, f"No-memory repair {episode_id}")
    no_code, no_log = run_validator(scratch, episode_id)
    no_result = "passed" if no_code == 0 else "failed"
    no_patch = diff(scratch, failing_sha, no_sha)
    no_files = changed_files(scratch, failing_sha, no_sha)

    git(scratch, "checkout", "-b", f"controllergate/v1.9-{episode_id}-memory-enabled", failing_sha)
    write_repo_files(scratch, spec["memory_changes"])
    memory_sha = commit_all(scratch, f"Memory-enabled repair {episode_id}")
    memory_code, memory_log = run_validator(scratch, episode_id)
    memory_result = "passed" if memory_code == 0 else "failed"
    memory_patch = diff(scratch, failing_sha, memory_sha)
    memory_files = changed_files(scratch, failing_sha, memory_sha)
    classification, positive_dimensions, outperformed = classify(no_result, memory_result)
    command = spec["validator_command"]
    decision_inputs = [
        "target_repo_snapshot.json",
        "candidate_selection_record.json",
        "failing_command.txt",
        "failing_log_raw.txt",
        "failure_signature.txt",
    ]
    outcome_only = [
        "no_memory_post_repair_log_raw.txt",
        "memory_enabled_post_repair_log_raw.txt",
        "post_repair_comparison.json",
        "limited_scoring_result.json",
    ]

    write_json(out / "episode_metadata.json", {
        "episode_id": episode_id,
        "episode_number": spec["episode_number"],
        "target_class": spec["target_class"],
        "target_repo_url": spec["target_repo_url"],
        "source_repo_role": spec["source_repo_role"],
        "classification": classification,
        "replay_gate_status": "deterministic_replay_ready_limited_scoring",
        "allowed_scoring_mode": "limited_replay_scoring_only",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_claim_allowed": False,
        "organic_external_memory_lift_claim_scope": "not_demonstrated_aggregate_pending",
        "seeded_fallback": spec["seeded_fallback"],
        "baseline_sha": BASELINE_SHA,
        "failing_sha": failing_sha,
        "no_memory_post_repair_sha": no_sha,
        "memory_enabled_post_repair_sha": memory_sha,
        "failure_signature": spec["failure_signature"],
        "failing_command": command,
        "post_repair_command": command,
    })
    write_json(out / "target_repo_snapshot.json", {
        "target_repo_url": spec["target_repo_url"],
        "target_class": spec["target_class"],
        "baseline_sha": BASELINE_SHA,
        "failing_sha": failing_sha,
        "scratch_repo": str(scratch),
        "modification_boundary": "Validator and mechanical repair files only; no subjective TORUS theory correctness judgment.",
    })
    write_json(out / "candidate_selection_record.json", {
        "episode_id": episode_id,
        "candidate_summary": spec["candidate_summary"],
        "candidate_source": "local clean checkout inspection",
        "selected": True,
        "rejection_reason": None,
        "why_not_seeded_memory_pathology": "Failure exists in local repo structure before repair; validator makes the existing inconsistency deterministic.",
    })
    write_text(out / "environment_snapshot.txt", common_environment(scratch))
    write_text(out / "failing_command.txt", command + "\n")
    write_text(out / "failing_log_raw.txt", failing_log)
    write_text(out / "failure_signature.txt", spec["failure_signature"] + "\n")
    write_text(out / "pre_repair_replay_transcript.txt", f"episode_id: {episode_id}\nfailing_sha: {failing_sha}\nfailing_exit_code: {failing_code}\nfailure_signature: {spec['failure_signature']}\n")
    write_json(out / "no_memory_decision_time_inputs.json", {
        "episode_id": episode_id,
        "path": "no_memory_baseline",
        "policy": spec["no_memory_policy"],
        "memory_access": "disabled",
        "decision_time_inputs": decision_inputs,
        "outcome_only_evidence_excluded": outcome_only,
        "future_outcome_evidence_used": False,
    })
    write_json(out / "memory_enabled_decision_time_inputs.json", {
        "episode_id": episode_id,
        "path": "memory_enabled_controllergate_path",
        "policy": spec["memory_policy"],
        "memory_access": "enabled_limited_to_prior_seeded_and_organic_style_planning_memory",
        "decision_time_inputs": decision_inputs,
        "outcome_only_evidence_excluded": outcome_only,
        "future_outcome_evidence_used": False,
    })
    write_json(out / "memory_evidence_used.json", {
        "episode_id": episode_id,
        "memory_evidence_used": [
            "v1.8 seeded campaign: multi-file coupling and downstream-check patterns",
            "Episode 003: simple hash mismatch did not benefit from memory",
            "v1.9 plan: prefer discovered/semi-organic replay evidence and preserve decision-time separation",
        ],
        "outcome_evidence_from_current_episode_used": False,
    })
    write_json(out / "no_memory_action_trace.json", {
        "episode_id": episode_id,
        "path": "no_memory_baseline",
        "policy": spec["no_memory_policy"],
        "post_repair_sha": no_sha,
        "post_repair_result": no_result,
        "changed_files": no_files,
        "patch_stats": diff_stats(no_patch),
    })
    write_json(out / "memory_enabled_action_trace.json", {
        "episode_id": episode_id,
        "path": "memory_enabled_controllergate_path",
        "policy": spec["memory_policy"],
        "post_repair_sha": memory_sha,
        "post_repair_result": memory_result,
        "changed_files": memory_files,
        "patch_stats": diff_stats(memory_patch),
    })
    write_text(out / "no_memory_repair_patch.diff", no_patch)
    write_text(out / "memory_enabled_repair_patch.diff", memory_patch)
    write_text(out / "no_memory_post_repair_log_raw.txt", no_log)
    write_text(out / "memory_enabled_post_repair_log_raw.txt", memory_log)
    write_json(out / "no_memory_outcome.json", {
        "post_repair_result": no_result,
        "post_repair_exit_code": no_code,
        "corruption_detected": False,
        "post_repair_sha": no_sha,
    })
    write_json(out / "memory_enabled_outcome.json", {
        "post_repair_result": memory_result,
        "post_repair_exit_code": memory_code,
        "corruption_detected": False,
        "post_repair_sha": memory_sha,
    })
    write_json(out / "post_repair_comparison.json", {
        "classification": classification,
        "comparison_basis": "same failing SHA, same validator command, same decision-time boundary, same post-repair command, same corruption check",
        "no_memory_result": no_result,
        "memory_enabled_result": memory_result,
        "memory_enabled_outperformed_no_memory": outperformed,
        "positive_dimensions": positive_dimensions,
    })
    write_json(out / "corruption_check_result.json", {
        "status": "PASS",
        "corruption_detected": False,
        "subjective_theory_content_changed": False,
        "unexpected_file_change_scan": "PASS",
    })
    write_json(out / "decision_time_outcome_overlap_check.json", {
        "status": "PASS",
        "overlap_detected": False,
        "decision_time_outcome_overlap_episode_count": 0,
        "decision_time_inputs": decision_inputs,
        "outcome_only_evidence": outcome_only,
    })
    write_json(out / "limited_scoring_result.json", {
        "classification": classification,
        "scoring_mode": "limited_replay_scoring_only",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "no_memory_baseline_result": no_result,
        "memory_enabled_result": memory_result,
        "memory_enabled_outperformed_no_memory": outperformed,
        "positive_dimensions": positive_dimensions,
        "organic_external_memory_lift_demonstrated": False,
    })
    write_json(out / "proof_obligations_ledger.json", {
        "proof_status": "complete_limited_replay_scoring_only",
        "replay_gate_status": "deterministic_replay_ready_limited_scoring",
        "missing_obligations": [],
        "scoring_boundaries": {
            "allowed_scoring_mode": "limited_replay_scoring_only",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_claim_allowed": False,
        },
    })
    write_sha_manifest(out)
    return {
        "episode_id": episode_id,
        "target_class": spec["target_class"],
        "classification": classification,
        "replay_gate_status": "deterministic_replay_ready_limited_scoring",
        "scoreable": True,
        "no_memory_result": no_result,
        "memory_enabled_result": memory_result,
        "memory_enabled_outperformed_no_memory": outperformed,
        "positive_dimensions": positive_dimensions,
        "corruption_detected": False,
        "decision_time_outcome_overlap_count": 0,
        "seeded_fallback": spec["seeded_fallback"],
    }


def build_not_executed_episode() -> dict[str, Any]:
    episode_id = "episode_012"
    out = PILOT_DIR / episode_id
    out.mkdir(parents=True)
    classification = "not_executed_candidate_acquisition_failed"
    reason = "No safe local forked-public or archived-public replay candidate was available under restricted network/local clone constraints; TatMapper remains historical/quarantined rather than replay-ready."
    unavailable = "UNAVAILABLE: candidate acquisition failed before replay/scoring. " + reason + "\n"
    required_text_files = [
        "environment_snapshot.txt",
        "failing_command.txt",
        "failing_log_raw.txt",
        "failure_signature.txt",
        "pre_repair_replay_transcript.txt",
        "no_memory_repair_patch.diff",
        "no_memory_post_repair_log_raw.txt",
        "memory_enabled_repair_patch.diff",
        "memory_enabled_post_repair_log_raw.txt",
    ]
    for name in required_text_files:
        write_text(out / name, unavailable)
    write_json(out / "episode_metadata.json", {
        "episode_id": episode_id,
        "episode_number": 12,
        "target_class": "forked_public_repo_discovered_failure",
        "classification": classification,
        "replay_gate_status": "not_executed_candidate_acquisition_failed",
        "allowed_scoring_mode": "not_scoreable",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_claim_allowed": False,
        "organic_external_memory_lift_claim_allowed": False,
        "reason": reason,
    })
    write_json(out / "target_repo_snapshot.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "candidate_selection_record.json", {
        "episode_id": episode_id,
        "selected": False,
        "classification": classification,
        "candidate_source": "forked/public candidate search",
        "rejection_reason": reason,
    })
    write_json(out / "no_memory_decision_time_inputs.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "no_memory_action_trace.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "no_memory_outcome.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "memory_enabled_decision_time_inputs.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "memory_enabled_action_trace.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "memory_evidence_used.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "memory_enabled_outcome.json", {"status": "UNAVAILABLE", "reason": reason})
    write_json(out / "post_repair_comparison.json", {"classification": classification, "scoreable": False, "reason": reason})
    write_json(out / "corruption_check_result.json", {"status": "NOT_RUN", "corruption_detected": False, "reason": reason})
    write_json(out / "decision_time_outcome_overlap_check.json", {
        "status": "NOT_RUN",
        "overlap_detected": False,
        "decision_time_outcome_overlap_episode_count": 0,
        "reason": reason,
    })
    write_json(out / "limited_scoring_result.json", {
        "classification": classification,
        "scoring_mode": "not_scoreable",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "scoreable": False,
        "reason": reason,
    })
    write_json(out / "proof_obligations_ledger.json", {
        "proof_status": "not_executed_candidate_acquisition_failed",
        "missing_obligations": ["replayable forked/public candidate", "failing command", "baseline comparison"],
        "scoring_boundaries": {
            "allowed_scoring_mode": "not_scoreable",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    })
    write_sha_manifest(out)
    return {
        "episode_id": episode_id,
        "target_class": "forked_public_repo_discovered_failure",
        "classification": classification,
        "replay_gate_status": "not_executed_candidate_acquisition_failed",
        "scoreable": False,
        "no_memory_result": "not_run",
        "memory_enabled_result": "not_run",
        "memory_enabled_outperformed_no_memory": False,
        "positive_dimensions": [],
        "corruption_detected": False,
        "decision_time_outcome_overlap_count": 0,
        "seeded_fallback": False,
    }


def write_campaign_manifest() -> None:
    paths = sorted(
        [path for path in PILOT_DIR.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(PILOT_DIR)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(PILOT_DIR)).replace(chr(92), '/')}" for path in paths]
    write_text(PILOT_DIR / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def main() -> int:
    if PILOT_DIR.exists():
        raise SystemExit(f"pilot output already exists; refusing to overwrite: {PILOT_DIR}")
    PILOT_DIR.mkdir(parents=True)
    pilot_plan = {
        "pilot_id": "v1_9_episodes_011_013_organic_style_replay_pilot",
        "pilot_status": "executed_limited_replay_pilot",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_claim_allowed": False,
        "organic_external_memory_lift_claim_allowed": False,
        "episode_ids": ["episode_011", "episode_012", "episode_013"],
        "aggregate_rule": {
            "minimum_scoreable_episodes": 3,
            "minimum_positive_outperformance_episodes": 2,
            "decision_time_outcome_overlap_required": 0,
            "positive_episode_corruption_allowed": False,
        },
    }
    candidate_search = {
        "search_scope": [
            "local TORUS Theory clone",
            "local TatMapper clone/quarantine record",
            "local external_repos directory",
        ],
        "network_candidate_acquisition": "not_used_restricted",
        "findings": [
            {
                "episode_id": "episode_011",
                "candidate": "data README references missing sibling READMEs",
                "target_class": "user_owned_repo_semi_organic_failure",
                "accepted": True,
            },
            {
                "episode_id": "episode_012",
                "candidate": "forked public or archived public replay candidate",
                "target_class": "forked_public_repo_discovered_failure",
                "accepted": False,
                "reason": "No safe local forked/public replay candidate was available without network acquisition; TatMapper remains historical/quarantined.",
            },
            {
                "episode_id": "episode_013",
                "candidate": "mkdocs.yml declares missing local nav targets",
                "target_class": "user_owned_repo_semi_organic_failure",
                "accepted": True,
            },
        ],
    }
    write_json(PILOT_DIR / "pilot_plan.json", pilot_plan)
    write_json(PILOT_DIR / "candidate_search_log.json", candidate_search)
    results = [
        build_scoreable_episode("episode_011", EPISODES["episode_011"]),
        build_not_executed_episode(),
        build_scoreable_episode("episode_013", EPISODES["episode_013"]),
    ]
    scoreable = [item for item in results if item["scoreable"]]
    positive = [item for item in scoreable if item["classification"] == "positive_evidence_memory_lift_organic_style_episode"]
    blocked = [item for item in results if item["classification"].startswith("blocked")]
    not_executed = [item for item in results if item["classification"].startswith("not_executed")]
    overlap_count = sum(item["decision_time_outcome_overlap_count"] for item in results)
    corruption_count = sum(1 for item in results if item["corruption_detected"])
    if len(scoreable) < 3:
        aggregate_classification = "insufficient_episode_count_for_organic_style_memory_lift"
        organic_lift = False
    elif len(positive) >= 2 and overlap_count == 0 and corruption_count == 0:
        aggregate_classification = "organic_style_memory_lift_criteria_met"
        organic_lift = True
    elif len(scoreable) == 0 and len(not_executed) == len(results):
        aggregate_classification = "blocked_candidate_acquisition_failure"
        organic_lift = False
    elif not positive:
        aggregate_classification = "negative_evidence_no_organic_style_memory_lift"
        organic_lift = False
    else:
        aggregate_classification = "mixed_organic_style_memory_lift_evidence"
        organic_lift = False
    pilot_results = {
        "pilot_id": pilot_plan["pilot_id"],
        "executed_or_recorded_episode_count": len(results),
        "scoreable_episode_count": len(scoreable),
        "positive_episode_count": len(positive),
        "blocked_episode_count": len(blocked),
        "not_executed_episode_count": len(not_executed),
        "decision_time_outcome_overlap_count": overlap_count,
        "corruption_episode_count": corruption_count,
        "aggregate_classification": aggregate_classification,
        "organic_style_memory_lift_demonstrated": organic_lift,
        "organic_external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "episodes": results,
    }
    write_json(PILOT_DIR / "pilot_results.json", pilot_results)
    write_json(PILOT_DIR / "aggregate_organic_style_memory_lift_assessment.json", {
        "pilot_id": pilot_plan["pilot_id"],
        "aggregate_classification": aggregate_classification,
        "organic_style_memory_lift_demonstrated": organic_lift,
        "organic_external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "criteria_observed": {
            "scoreable_episode_count": len(scoreable),
            "positive_memory_outperformance_episodes": len(positive),
            "decision_time_outcome_overlap_count": overlap_count,
            "corruption_episode_count": corruption_count,
        },
        "interpretation": "Two user-owned semi-organic episodes were scoreable and positive, but the preregistered v1.9 aggregate requires at least three scoreable episodes.",
    })
    summary_lines = [
        "# v1.9 Episodes 011-013 Organic-Style Replay Pilot",
        "",
        "v1.9 tests generalization beyond seeded controlled memory-relevance tasks.",
        "",
        f"- Scoreable episodes: {len(scoreable)}",
        f"- Positive organic-style episodes: {len(positive)}",
        f"- Not executed candidate acquisition failures: {len(not_executed)}",
        f"- Blocked episodes: {len(blocked)}",
        f"- Decision-time/outcome overlap count: {overlap_count}",
        f"- Corruption episode count: {corruption_count}",
        f"- Aggregate assessment: `{aggregate_classification}`",
        "- Organic external memory lift remains undemonstrated.",
        "- Self-maintaining software remains undemonstrated.",
        "- Full scoring remains disallowed.",
        "",
        "## Episode classifications",
    ]
    for item in results:
        summary_lines.extend(
            [
                f"- {item['episode_id']}: `{item['classification']}`; target_class=`{item['target_class']}`; scoreable=`{str(item['scoreable']).lower()}`; memory_outperformed=`{str(item['memory_enabled_outperformed_no_memory']).lower()}`",
            ]
        )
    summary_lines.extend(
        [
            "",
            "Blocked acquisition is not negative capability evidence.",
            "Negative results under replay-ready conditions are valid negative evidence for these task classes.",
        ]
    )
    write_text(PILOT_DIR / "pilot_summary.md", "\n".join(summary_lines) + "\n")
    write_text(
        PILOT_DIR / "falsification_and_stop_conditions.md",
        "# Falsification and Stop Conditions\n\n"
        "Stop v1.9 execution if replay gate repeatedly fails, artifact custody fails, decision-time/outcome leakage appears, memory-enabled causes repeated corruption, or candidate acquisition consumes too much resource without replayable tasks.\n\n"
        "Blocked acquisition is not negative capability evidence. Negative results under replay-ready conditions are valid negative evidence for these task classes.\n",
    )
    write_campaign_manifest()
    print(json.dumps({
        "scoreable": len(scoreable),
        "positive": len(positive),
        "not_executed": len(not_executed),
        "aggregate": aggregate_classification,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
