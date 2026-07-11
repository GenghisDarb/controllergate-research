from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

from .historical_metadata import canonicalize_name, parse_utc
from .wheel_compatibility import wheel_compatibility


def fetch_json(url: str, store: Path) -> tuple[dict[str, Any], str]:
    store.mkdir(parents=True, exist_ok=True); key = hashlib.sha256(url.encode()).hexdigest(); path = store / f"{key}.json"
    if path.is_file(): payload = path.read_bytes()
    else:
        with urlopen(Request(url, headers={"User-Agent": "ControllerGate/Batch068h4"}), timeout=30) as response: payload = response.read()
        path.write_bytes(payload)
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


def enumerate_release_files(package: str, cutoff: str, store: Path) -> dict[str, Any]:
    name = canonicalize_name(package); data, metadata_hash = fetch_json(f"https://pypi.org/pypi/{name}/json", store); rows = []
    for version, files in data.get("releases", {}).items():
        try: Version(version)
        except InvalidVersion: continue
        for item in files:
            upload = item.get("upload_time_iso_8601") or item.get("upload_time")
            if not upload: continue
            cutoff_ok = parse_utc(upload) <= parse_utc(cutoff)
            wheel = wheel_compatibility(str(item.get("filename", "")))
            rows.append({"package": name, "version": version, "filename": item.get("filename"), "packagetype": item.get("packagetype"), "upload_timestamp": upload, "sha256": item.get("digests", {}).get("sha256"), "size": item.get("size"), "yanked": bool(item.get("yanked")), "requires_python": item.get("requires_python"), "python_tags": [str(tag) for tag in item.get("python_version", "").split()], "abi_tags": [], "platform_tags": [], "artifact_file_url": item.get("url"), "project_metadata_url": f"https://pypi.org/pypi/{name}/json", "metadata_available": item.get("has_sig") is not None, "cutoff_eligible": cutoff_ok, "target_environment_compatible": bool(wheel["compatible"]) if item.get("packagetype") == "bdist_wheel" else True, "selection_preference": wheel["preference"] if item.get("packagetype") == "bdist_wheel" else 4, "compatibility_reason": wheel["reason"] if item.get("packagetype") == "bdist_wheel" else "sdist_static_or_dynamic_metadata_required"})
    return {"package": name, "metadata_sha256": metadata_hash, "files": sorted(rows, key=lambda item: (Version(item["version"]), item["filename"]))}


def select_release_file(catalog: dict[str, Any], specifiers: list[str], python_version: str) -> dict[str, Any] | None:
    requirements = [SpecifierSet(item) for item in specifiers if item]
    versions = sorted({Version(item["version"]) for item in catalog["files"] if item["cutoff_eligible"]}, reverse=True)
    for version in versions:
        if any(not spec.contains(version, prereleases=True) for spec in requirements): continue
        files = []
        for item in catalog["files"]:
            if Version(item["version"]) != version or not item["cutoff_eligible"] or item["yanked"]: continue
            requires_python = item.get("requires_python")
            if requires_python and not SpecifierSet(requires_python).contains(Version(python_version), prereleases=True): continue
            if item["packagetype"] == "bdist_wheel" and not item["target_environment_compatible"]: continue
            files.append(item)
        if files: return sorted(files, key=lambda item: (item["selection_preference"], item["filename"]))[0]
    return None


def acquire_artifact(record: dict[str, Any], store: Path) -> dict[str, Any]:
    target = store / "artifacts" / str(record["sha256"]) / str(record["filename"]); target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        with urlopen(Request(str(record["artifact_file_url"]), headers={"User-Agent": "ControllerGate/Batch068h4"}), timeout=60) as response: target.write_bytes(response.read())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return {"status": "PASS" if digest == record["sha256"] and target.stat().st_size == record["size"] else "BLOCK", "path": str(target), "sha256": digest, "expected_sha256": record["sha256"], "size": target.stat().st_size, "expected_size": record["size"], "network_destination": record["artifact_file_url"]}
