#!/usr/bin/env python3
"""Generate v2.5 BugsInPy Linux runtime runner planning artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "v2_5_bugsinpy_runtime_probe.yml"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

CANDIDATES = [
    {
        "candidate_id": "v2_5_bugsinpy_black_2",
        "artifact_dir": "black_2",
        "project": "black",
        "bug_id": "2",
        "checkout_command": "bugsinpy-checkout -p black -v 0 -i 2 -w <workspace>",
        "compile_command": "bugsinpy-compile -w <workspace>/black",
        "test_command": "bugsinpy-test -w <workspace>/black -r",
        "expected_dataset_test": "python -m unittest -q tests.test_black.BlackTestCase.test_fmtonoff4",
    },
    {
        "candidate_id": "v2_5_bugsinpy_youtube_dl_1",
        "artifact_dir": "youtube_dl_1",
        "project": "youtube-dl",
        "bug_id": "1",
        "checkout_command": "bugsinpy-checkout -p youtube-dl -v 0 -i 1 -w <workspace>",
        "compile_command": "bugsinpy-compile -w <workspace>/youtube-dl",
        "test_command": "bugsinpy-test -w <workspace>/youtube-dl -r",
        "expected_dataset_test": "python -m unittest -q test.test_utils.TestUtil.test_match_str",
    },
    {
        "candidate_id": "v2_5_bugsinpy_black_8",
        "artifact_dir": "black_8",
        "project": "black",
        "bug_id": "8",
        "checkout_command": "bugsinpy-checkout -p black -v 0 -i 8 -w <workspace>",
        "compile_command": "bugsinpy-compile -w <workspace>/black",
        "test_command": "bugsinpy-test -w <workspace>/black -r",
        "expected_dataset_test": "python -m unittest -q tests.test_black.BlackTestCase.test_comments7",
    },
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
    lines = [
        f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}"
        for path in paths
    ]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def update_shareable_summary() -> None:
    section = """## v2.5 BugsInPy Linux Runtime Runner

The current blocker is benchmark runtime acquisition.

- The workflow creates a Linux runtime path for BugsInPy replay.
- Candidate replay readiness requires fresh checkout/compile/test logs.
- BugsInPy candidates targeted: `black:2`, `youtube-dl:1`, and `black:8`.
- Workflow trigger: manual `workflow_dispatch`.
- Expected artifact: `v2_5_bugsinpy_runtime_probe_artifacts`.
- Current local status: workflow ready, runtime artifact pending.
- Repair scoring: not run.

Blocked runtime is not negative ControllerGate capability evidence. Gold/fixed patches are outcome-only. Candidate metadata alone does not prove replay readiness.

After the GitHub Actions artifact is produced, parse it with `scripts/v2_5_parse_bugsinpy_runtime_artifacts.py`. If three candidates promote, the next gated step is `v2_5_bugsinpy_real_bug_limited_replay_execution`; if one or two promote, run a small probe; if none promote, fix the runner environment.

Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.
"""
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        marker = "## v2.5 BugsInPy Linux Runtime Runner"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(
        OUTPUT_DIR / "runner_plan.json",
        {
            "campaign_id": "v2_5_bugsinpy_linux_runtime_runner",
            "purpose": "Create a Linux/GitHub Actions runtime path for BugsInPy real-bug replay smoke tests.",
            "workflow_path": str(WORKFLOW_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
            "workflow_trigger": "workflow_dispatch",
            "runner": "ubuntu-latest",
            "candidate_order": ["black:2", "youtube-dl:1", "black:8"],
            "do_not_run_full_scoring": True,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "gold_fixed_patches_decision_time_allowed": False,
        },
    )
    write_json(
        OUTPUT_DIR / "runtime_probe_expected_artifacts.json",
        {
            "artifact_name": "v2_5_bugsinpy_runtime_probe_artifacts",
            "root_files": [
                "runtime_environment.txt",
                "bugsinpy_install_log.txt",
                "bugsinpy_command_probe.txt",
                "runtime_probe_summary.json",
                "SHA256SUMS.txt",
            ],
            "candidate_directories": ["black_2", "youtube_dl_1", "black_8"],
            "candidate_files": [
                "candidate_metadata.json",
                "info_command.txt",
                "info_log_raw.txt",
                "checkout_command.txt",
                "checkout_log_raw.txt",
                "compile_command.txt",
                "compile_log_raw.txt",
                "test_command.txt",
                "test_log_raw.txt",
                "failure_signature.txt",
                "replay_feasibility_result.json",
                "gold_patch_exclusion_plan.json",
                "SHA256SUMS.txt",
            ],
        },
    )
    write_json(
        OUTPUT_DIR / "candidate_attempt_matrix.json",
        {
            "candidate_count": len(CANDIDATES),
            "records": [
                {
                    **candidate,
                    "promotion_status_before_artifact": "pending_github_actions_runtime_probe",
                    "gold_fixed_patch_policy": "outcome_only_not_decision_time",
                }
                for candidate in CANDIDATES
            ],
            "promotion_rules": [
                "buggy checkout succeeds",
                "compile/setup succeeds or is unnecessary",
                "failing test command runs locally",
                "failure is deterministic or strongly reproducible",
                "logs are captured",
                "fixed/gold patch is not used at decision time",
            ],
        },
    )
    write_text(
        OUTPUT_DIR / "github_actions_usage_instructions.md",
        """# v2.5 GitHub Actions Usage Instructions

The workflow creates a Linux runtime path for BugsInPy replay.

1. Commit and push this workflow to GitHub.
2. Open the repository on GitHub.
3. Go to **Actions**.
4. Select **v2_5_bugsinpy_runtime_probe**.
5. Click **Run workflow** on branch `controllergate-v1.7-alpha-real-trace-pilot`.
6. Wait for the run to finish.
7. Download the artifact named `v2_5_bugsinpy_runtime_probe_artifacts`.
8. Provide the artifact back to Codex or unpack it into the repo workspace.
9. Run:

```powershell
C:\\Users\\thisb\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe scripts\\v2_5_parse_bugsinpy_runtime_artifacts.py <path-to-artifact-folder>
```

Candidate replay readiness requires fresh checkout/compile/test logs. Candidate metadata alone does not prove replay readiness.

Gold/fixed patches are outcome-only. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.
""",
    )
    write_text(
        OUTPUT_DIR / "runtime_artifact_ingestion_instructions.md",
        """# v2.5 Runtime Artifact Ingestion Instructions

After downloading and unpacking the GitHub Actions artifact, verify it contains:

- `runtime_environment.txt`
- `bugsinpy_install_log.txt`
- `bugsinpy_command_probe.txt`
- `runtime_probe_summary.json`
- `black_2/`
- `youtube_dl_1/`
- `black_8/`

Then run the parser:

```powershell
C:\\Users\\thisb\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe scripts\\v2_5_parse_bugsinpy_runtime_artifacts.py <artifact-folder>
```

Handoff logic:

- 3 promoted candidates: recommend `v2_5_bugsinpy_real_bug_limited_replay_execution`.
- 1-2 promoted candidates: recommend `v2_5_small_bugsinpy_probe_execution`.
- 0 promoted candidates: recommend `runner_environment_fix_required`.

Do not use fixed/gold patches as decision-time inputs. Do not run full scoring from this parser.
""",
    )
    write_json(
        OUTPUT_DIR / "runner_status.json",
        {
            "runner_status": "workflow_ready_pending_manual_github_actions_run",
            "artifact_ingested": False,
            "promoted_candidate_count": 0,
            "recommended_handoff": "run_github_actions_workflow_then_parse_artifact",
            "repair_scoring_run": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "v2_4_result_preserved": "blocked_real_external_bug_candidate_acquisition_failure",
            "v2_4b_result_preserved": "blocked_real_bug_runtime_unavailable",
        },
    )
    update_shareable_summary()
    write_manifest(OUTPUT_DIR)
    print("v2.5 BugsInPy Linux runtime runner artifacts generated")
    print("runner status: workflow_ready_pending_manual_github_actions_run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
