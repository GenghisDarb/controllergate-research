from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record, sha256_file


DEPENDENCY_NAMES = ("pyproject.toml", "setup.cfg", "setup.py", "requirements.txt", "requirements-dev.txt", "tox.ini")
BUILD_NAMES = ("pyproject.toml", "setup.cfg", "setup.py")


def build_provider_dry_lock(source_root: Path, *, runtime: dict[str, Any], platform: dict[str, Any]) -> dict[str, Any]:
    roots = []
    for name in DEPENDENCY_NAMES:
        path = source_root / name
        if path.is_file():
            roots.append({"path": name, "sha256": sha256_file(path), "kind": "build" if name in BUILD_NAMES else "dependency"})
    build_roots = [item for item in roots if item["kind"] == "build"]
    dependency_roots = list(roots)
    pyproject = source_root / "pyproject.toml"
    backend = "legacy_setuptools"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^\s*build-backend\s*=\s*[\"']([^\"']+)", text)
        backend = match.group(1) if match else "pyproject_unspecified_backend"
    passed = bool(dependency_roots and build_roots and runtime.get("status") == "PASS" and platform.get("status") == "PASS")
    record = {
        "status": "PASS" if passed else "BLOCK",
        "provider_lock_version": 3,
        "dependency_roots": dependency_roots,
        "build_roots": build_roots,
        "build_backend": backend,
        "runtime_identity": runtime,
        "platform_identity": platform,
        "provider_bytes_acquired": False,
        "executed_provider_lock_mutable": False,
        "exact_blocker_known_before_capsule": not passed,
    }
    if not passed:
        record["blocker"] = "candidate_specific_provider_plan_unresolved"
    record["provider_dry_lock_hash"] = hash_record(record)
    return record
