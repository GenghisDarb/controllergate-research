from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic


def require_absent_and_create(output: Path, *, repo_root: Path, engine_path: Path, candidate_manifest: Path, workflow_path: Path) -> dict[str, Any]:
    if output.exists():
        raise RuntimeError("batch082_precommitted_result_directory_detected")
    checked_out_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True).stdout.strip()
    output.mkdir(parents=True)
    record: dict[str, Any] = {
        "status": "PASS",
        "output_absent_at_checkout": True,
        "fresh_output_generated": True,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "LOCAL_NOT_OFFICIAL"),
        "job_id": os.getenv("GITHUB_JOB", "local_prepare"),
        "github_sha": os.getenv("GITHUB_SHA", checked_out_head),
        "checked_out_head": checked_out_head,
        "workflow_file_hash": sha256_file(workflow_path),
        "engine_hash": sha256_file(engine_path),
        "candidate_manifest_hash": sha256_file(candidate_manifest),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    record["guard_hash"] = hash_record(record)
    write_json_deterministic(output / "batch082_ci_native_result_guard.json", record)
    return record


def audit_guard(record: dict[str, Any]) -> dict[str, Any]:
    failures = []
    if record.get("output_absent_at_checkout") is not True:
        failures.append("output_not_absent_at_checkout")
    if record.get("fresh_output_generated") is not True:
        failures.append("fresh_output_not_generated")
    if record.get("github_sha") != record.get("checked_out_head") and record.get("workflow_run_id") != "LOCAL_NOT_OFFICIAL":
        failures.append("workflow_head_mismatch")
    check = dict(record)
    claimed = check.pop("guard_hash", None)
    if hash_record(check) != claimed:
        failures.append("guard_hash_invalid")
    return {"status": "PASS" if not failures else "BLOCK", "failures": failures}

