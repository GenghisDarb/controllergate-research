
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "source" / "darker"


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_variant(variant_id, command, env=None):
    completed = subprocess.run(command, cwd=str(SOURCE), env=env, text=True, capture_output=True, timeout=180)
    combined = completed.stdout + "\n" + completed.stderr
    target_terms = ["Not a git repository", "git_get_modified_files", "_git_check_output_lines", "git diff --name-only"]
    precondition_terms = ["ModuleNotFoundError", "ImportError", "No module named", "dependency API mismatch"]
    return {
        "variant_id": variant_id,
        "command": " ".join(command),
        "cwd": str(SOURCE),
        "returncode": completed.returncode,
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": completed.stdout[-1200:],
        "sanitized_stderr_excerpt": completed.stderr[-1200:],
        "target_indicator_seen": any(term in combined for term in target_terms),
        "environment_precondition_error_seen": any(term in combined for term in precondition_terms),
    }


def main() -> int:
    base_env = os.environ.copy()
    absolute_env = base_env.copy()
    absolute_env["GIT_DIR"] = str(SOURCE / ".git")
    absolute_env["GIT_WORK_TREE"] = str(SOURCE)
    variants = [
        run_variant("source_root_no_git_dir_python_module", ["python", "-m", "darker", "--check", "src"], base_env),
        run_variant("absolute_git_dir_work_tree_python_module", ["python", "-m", "darker", "--check", "src"], absolute_env),
    ]
    verified = any(
        item["returncode"] != 0
        and item["target_indicator_seen"]
        and not item["environment_precondition_error_seen"]
        for item in variants
    )
    print(json.dumps({
        "status": "PASS" if verified else "BLOCK",
        "harness_v9_generated": True,
        "target_aligned_pre_repair_failure_reproduced": verified,
        "active_command_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_used": False,
        "variant_results": variants,
        "blocker": None if verified else "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
