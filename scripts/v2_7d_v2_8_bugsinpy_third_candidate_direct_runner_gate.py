#!/usr/bin/env python3
"""Generate v2.7d/v2.8 third-candidate direct-runner gate artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_7d_bugsinpy_third_candidate_direct_runner_expansion"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
V27C_POOL = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion" / "promoted_bugsinpy_real_bug_candidate_pool.json"
V27C_GATE = REPO_ROOT / "outputs" / "v2_7c_bugsinpy_direct_runner_artifact_ingestion" / "v2_8_execution_gate_decision.json"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


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


def update_summary(final_count: int, gate_result: str) -> None:
    section = f"""## v2.7d/v2.8 BugsInPy Third-Candidate Direct Runner Expansion

v2.7d adds a focused Linux/GitHub Actions direct-runner expansion to acquire the one missing clean target-matched BugsInPy candidate. It does not run repair scoring locally.

- Starting clean target-matched count from v2.7c: {final_count}.
- Runner artifact ingested: false.
- v2.8 executed: false.
- Gate result: `{gate_result}`.

The runner excludes already promoted or blocked candidates, derives direct commands from BugsInPy metadata, rejects dependency/import/runtime/wrapper failures, and stops after one clean new target-matched candidate. Candidate promotion is not repair success. Full scoring remains disallowed. Memory lift and self-maintaining software remain undemonstrated.

Next required action: run the `v2_7d_bugsinpy_third_candidate_direct_runner_expansion` GitHub Actions workflow and ingest the artifact.
"""
    marker = "## v2.7d/v2.8 BugsInPy Third-Candidate Direct Runner Expansion"
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pool = load_json(V27C_POOL)
    gate = load_json(V27C_GATE)
    records = pool.get("records", []) if isinstance(pool.get("records"), list) else []
    final_count = int(pool.get("count", len(records)))
    gate_result = "blocked_pending_v2_7d_runner_artifact"
    write_json(
        OUTPUT_DIR / "third_candidate_direct_runner_plan.json",
        {
            "campaign": "v2.7d/v2.8 BugsInPy third-candidate direct runner expansion",
            "workflow": ".github/workflows/v2_7d_bugsinpy_third_candidate_direct_runner_expansion.yml",
            "runner_script": "scripts/v2_7d_bugsinpy_third_candidate_direct_runner_expansion.py",
            "budget": 12,
            "purpose": "Acquire exactly one additional clean target-matched BugsInPy candidate before v2.8.",
            "full_scoring_allowed": False,
            "self_maintaining_software_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_selection_policy.json",
        {
            "exclude_already_promoted_or_failed_candidates": True,
            "prefer_pure_python_projects": True,
            "derive_direct_commands_from_bugsinpy_metadata": True,
            "dependency_import_runtime_wrapper_failures_count_as_target_replay": False,
            "fixed_or_gold_patch_allowed_at_decision_time": False,
        },
    )
    write_json(
        OUTPUT_DIR / "runner_status.json",
        {
            "artifact_ingested": False,
            "local_execution_status": "not_run_locally_requires_linux_github_actions",
            "starting_clean_target_matched_count": final_count,
            "v2_7c_gate_result": gate.get("gate_result"),
        },
    )
    write_json(
        OUTPUT_DIR / "promoted_bugsinpy_real_bug_candidate_pool.json",
        {
            "count": final_count,
            "records": records,
            "source": "v2.7c clean target-matched pool; no v2.7d artifact ingested yet",
        },
    )
    write_json(
        OUTPUT_DIR / "blocked_candidate_summary.json",
        {
            "blocked_count": 0,
            "records": [],
            "pending_artifact": "v2_7d_bugsinpy_third_candidate_direct_runner_expansion_artifacts",
        },
    )
    write_json(
        OUTPUT_DIR / "v2_8_execution_gate_decision.json",
        {
            "target_matched_candidate_count": final_count,
            "minimum_required": 3,
            "execute_v2_8": False,
            "repair_scoring_run": False,
            "gate_result": gate_result,
            "next_required_action": "Run v2.7d third-candidate direct-runner workflow and ingest artifact.",
        },
    )
    write_text(
        OUTPUT_DIR / "v2_8_not_executed_blocker_report.md",
        f"""# v2.8 Not Executed Blocker Report

v2.8 did not execute because only {final_count} clean target-matched BugsInPy candidates exist before the v2.7d runner artifact.

The next required action is to run `v2_7d_bugsinpy_third_candidate_direct_runner_expansion` in GitHub Actions and ingest its artifact.
""",
    )
    write_text(
        OUTPUT_DIR / "campaign_summary.md",
        f"""# v2.7d/v2.8 BugsInPy Third-Candidate Direct Runner Expansion

Result: `{gate_result}`.

The focused third-candidate runner workflow and script are implemented. No v2.7d artifact has been ingested yet, so v2.8 did not execute.

Starting clean target-matched count: {final_count}.
Repair scoring remains NOT RUN. Full scoring remains disallowed. Memory lift is not demonstrated. Self-maintaining software is not demonstrated.
""",
    )
    update_summary(final_count, gate_result)
    write_manifest(OUTPUT_DIR)
    print("v2.7d/v2.8 third-candidate gate artifacts generated")
    print(f"starting clean target-matched candidates: {final_count}")
    print("v2.8 executed: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
