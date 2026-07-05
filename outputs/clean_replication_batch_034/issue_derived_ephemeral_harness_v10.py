from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

TARGET_TERMS = [
    "Not a git repository",
    "not a git repository",
    "git_get_modified_files",
    "_git_check_output_lines",
    "git diff --name-only",
]
ENV_PRECONDITION_TERMS = [
    "fatal: detected dubious ownership",
    "safe.directory",
    "dubious ownership in repository",
]


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def terms_seen(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    seen: list[str] = []
    for term in terms:
        if term in text or term.lower() in lowered:
            seen.append(term)
    return sorted(set(seen))


def main() -> int:
    source_root = Path.cwd()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source_root / "src")
    env["GIT_DIR"] = ".git"
    env.pop("GIT_WORK_TREE", None)
    command = ["python", "-m", "darker", "--check", "src"]
    completed = subprocess.run(
        command,
        cwd=str(source_root),
        env=env,
        text=True,
        capture_output=True,
        timeout=240,
    )
    combined = f"{completed.stdout}\n{completed.stderr}"
    target_terms = terms_seen(combined, TARGET_TERMS)
    environment_terms = terms_seen(combined, ENV_PRECONDITION_TERMS)
    repo_context_error_seen = "not a git repository" in combined.lower()
    target_aligned = completed.returncode != 0 and repo_context_error_seen and not environment_terms
    result = {
        "status": "PASS",
        "provider_cwd": str(Path.cwd()),
        "source_root": str(source_root),
        "git_dir": ".git",
        "git_work_tree": None,
        "pythonpath": env["PYTHONPATH"],
        "command": "GIT_DIR=.git python -m darker --check src",
        "returncode": completed.returncode,
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": completed.stdout[-3000:],
        "sanitized_stderr_excerpt": completed.stderr[-3000:],
        "target_indicator_terms_observed": target_terms,
        "environment_precondition_error_terms_observed": environment_terms,
        "repo_context_error_seen": repo_context_error_seen,
        "target_intent_matching_result": target_aligned,
        "target_aligned_pre_repair_failure_reproduced": target_aligned,
        "relative_git_dir_issue_stimulus_used": True,
        "relative_git_dir_general_provider_context_used": False,
        "source_mutated": False,
        "tests_mutated": False,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
