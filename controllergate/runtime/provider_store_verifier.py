from __future__ import annotations

from email.parser import BytesParser
from pathlib import Path
import re
import zipfile
from typing import Any

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic


def _wheel_metadata(path: Path) -> tuple[str, str, str | None]:
    package = path.name.split("-")[0].replace("_", "-")
    version = path.name.split("-")[1] if "-" in path.name else "UNKNOWN"
    requires_python: str | None = None
    try:
        with zipfile.ZipFile(path) as archive:
            metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
            metadata = BytesParser().parsebytes(archive.read(metadata_name))
            package = str(metadata.get("Name") or package)
            version = str(metadata.get("Version") or version)
            requires_python = metadata.get("Requires-Python")
    except (OSError, KeyError, StopIteration, zipfile.BadZipFile):
        pass
    return package, version, requires_python


def build_provider_lock(
    wheelhouse: Path,
    *,
    version: int,
    dependency_analysis: dict[str, Any],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    artifacts = []
    for path in sorted(wheelhouse.glob("*.whl")):
        package, package_version, requires_python = _wheel_metadata(path)
        artifacts.append({
            "package": package,
            "version": package_version,
            "filename": path.name,
            "expected_sha256": sha256_file(path),
            "artifact_url": "provider-resolution-wheelhouse://" + path.name,
            "upload_timestamp": "NOT_APPLICABLE_LOCAL_OR_RESOLVED_PROVIDER",
            "Requires-Python": requires_python,
            "dependency_parent": "candidate/test-runtime",
            "dependency_class": "candidate" if re.search(r"(?:^|[-_])0\.0\.0", path.name) else "third_party_or_candidate",
            "selection_reason": "target-informed provider closure",
            "size_bytes": path.stat().st_size,
        })
    record: dict[str, Any] = {
        "provider_lock_version": version,
        "strategy": strategy.get("strategy"),
        "selected_extras": dependency_analysis.get("selected_extras", []),
        "requirement_files": dependency_analysis.get("requirement_files", []),
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "immutable_after_seal": True,
    }
    record["provider_lock_hash"] = hash_record(record)
    return record


def seal_and_verify_provider_store(wheelhouse: Path, record: dict[str, Any]) -> dict[str, Any]:
    lock_path = wheelhouse / f"provider-lock-v{record['provider_lock_version']}.json"
    write_json_deterministic(lock_path, record)
    checks = []
    for artifact in record.get("artifacts", []):
        path = wheelhouse / artifact["filename"]
        checks.append(path.is_file() and sha256_file(path) == artifact["expected_sha256"])
    return {
        "status": "PASS" if checks and all(checks) else "BLOCK",
        "provider_lock_path": str(lock_path),
        "provider_lock_hash": record["provider_lock_hash"],
        "expected_hashes_recorded_before_execution": lock_path.is_file() and bool(checks),
        "artifact_count": len(checks),
        "verified_artifact_count": sum(checks),
    }


def next_provider_lock_version(previous: dict[str, Any], justified_dependency: str) -> dict[str, Any]:
    return {
        "parent_provider_lock_hash": previous["provider_lock_hash"],
        "provider_lock_version": int(previous["provider_lock_version"]) + 1,
        "justified_dependency": justified_dependency,
        "fresh_environments_required": True,
        "previous_store_mutated": False,
    }
