from __future__ import annotations

from typing import Any

from controllergate.core.evidence import hash_record


def build_provider_capsule_v3(*, source_sha: str, platform: dict[str, Any], abi: dict[str, Any], toolchain: dict[str, Any], dry_lock: dict[str, Any], artifacts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    artifacts = artifacts or []
    record = {
        "status": "PASS" if platform.get("status") == abi.get("status") == toolchain.get("status") == dry_lock.get("status") == "PASS" and bool(artifacts) and all(item.get("sha256") and item.get("source_url") for item in artifacts) else "BLOCK",
        "provider_lock_version": 3,
        "source_commit": source_sha,
        "platform": platform,
        "python_abi": abi,
        "build_toolchain": toolchain,
        "dependency_roots": dry_lock.get("dependency_roots", []),
        "build_backend": dry_lock.get("build_backend"),
        "package_artifacts": artifacts,
        "provider_bytes_committed": False,
        "execution_network": "none",
        "immutable_after_execution": True,
    }
    if record["status"] != "PASS":
        record["blocker"] = "provider_capsule_v3_incomplete"
    record["provider_capsule_identity"] = hash_record(record)
    return record
