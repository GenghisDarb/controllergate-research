from __future__ import annotations

import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record, sha256_file
from .runtime_root_policy import validate_runtime_root


def attest_runtime_root(path: str | Path, *, repo_root: str | Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    root = Path(path)
    policy = validate_runtime_root(root, repo_root=repo_root, env=env)
    if policy["status"] != "PASS":
        return {**policy, "attestation_hash": hash_record(policy)}
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ".controllergate-runtime-attestation"
    renamed = root / ".controllergate-runtime-attestation-renamed"
    timings: dict[str, float] = {}
    errors: list[str] = []
    try:
        start = time.monotonic(); probe.write_text("runtime-root-attestation\n", encoding="utf-8", newline="\n"); timings["write"] = time.monotonic() - start
        start = time.monotonic(); content = probe.read_text(encoding="utf-8"); timings["read"] = time.monotonic() - start
        start = time.monotonic(); probe.replace(renamed); timings["rename"] = time.monotonic() - start
        start = time.monotonic(); list(root.iterdir()); timings["enumeration"] = time.monotonic() - start
        long_dir = root / ("long-path-" + "x" * 80); long_dir.mkdir(exist_ok=True); (long_dir / "probe.txt").write_text("ok\n", encoding="utf-8"); long_ok = True; shutil.rmtree(long_dir)
        start = time.monotonic(); renamed.unlink(); timings["delete"] = time.monotonic() - start
    except OSError as exc:
        content = ""; long_ok = False; errors.append(str(exc))
    record: dict[str, Any] = {
        **policy, "status": "PASS" if not errors else "BLOCK", "filesystem": "local",
        "free_space_bytes": shutil.disk_usage(root).free, "path_length": len(str(root.resolve())),
        "write_test": not errors, "read_test": content == "runtime-root-attestation\n",
        "rename_test": "rename" in timings, "delete_test": "delete" in timings,
        "directory_enumeration": "enumeration" in timings, "long_path_test": long_ok,
        "temporary_executable_test": "NOT_RUN_PLATFORM_NEUTRAL",
        "docker_bind_mount_test": "NOT_RUN_DOCKER_CAPABILITY_NOT_ASSUMED",
        "docker_read_only_mount_test": "NOT_RUN_DOCKER_CAPABILITY_NOT_ASSUMED",
        "docker_writable_mount_test": "NOT_RUN_DOCKER_CAPABILITY_NOT_ASSUMED",
        "latencies_seconds": timings, "permission_errors": errors,
        "controlled_folder_or_sync_indicators": False,
        "preflight_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    record["attestation_hash"] = hash_record(record)
    return record
