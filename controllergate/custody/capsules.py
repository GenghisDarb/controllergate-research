from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Iterable


class CapsuleType(StrEnum):
    SOURCE = "SOURCE_CAPSULE"
    PROVIDER = "PROVIDER_CAPSULE"
    TRUTH = "TRUTH_CAPSULE"
    TERMINAL = "TERMINAL_CAPSULE"
    PACKAGE = "PACKAGE_CAPSULE"


_FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_FORBIDDEN_TRANSPORT_PARTS = {
    ".git",
    ".venv",
    "venv",
    "site-packages",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
_FORBIDDEN_TRANSPORT_NAMES = {"pyvenv.cfg", "activate", "activate.bat", "activate.ps1"}
_FORBIDDEN_TRANSPORT_SUFFIXES = (".pyc", ".pyo")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
    )
    return completed.stdout if binary else completed.stdout.strip()


def _safe_relative(path: str) -> bool:
    pure = PurePosixPath(path)
    return bool(path) and not path.startswith("/") and "\\" not in path and all(part not in {"", ".", ".."} for part in pure.parts)


def _zip_info(path: str, mode: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, _FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (mode & 0xFFFF) << 16
    return info


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


@dataclass(frozen=True)
class _TreeEntry:
    path: str
    mode: str
    kind: str
    object_id: str
    content: bytes

    def record(self) -> dict[str, object]:
        executable = self.mode == "100755"
        return {
            "path": self.path,
            "git_object_id": self.object_id,
            "content_sha256": _sha_bytes(self.content),
            "size": len(self.content),
            "git_mode": self.mode,
            "executable": executable,
        }


def _tree_entries(repo: Path, commit: str, *, symlink_policy: str, submodule_policy: str) -> tuple[str, list[_TreeEntry]]:
    resolved = str(_git(repo, "rev-parse", f"{commit}^{{commit}}"))
    if resolved != commit:
        raise ValueError("candidate_commit_identity_mismatch")
    tree_id = str(_git(repo, "rev-parse", f"{commit}^{{tree}}"))
    raw = bytes(_git(repo, "ls-tree", "-r", "-z", "--full-tree", commit, binary=True))
    entries: list[_TreeEntry] = []
    for row in raw.split(b"\0"):
        if not row:
            continue
        header, encoded_path = row.split(b"\t", 1)
        mode, kind, object_id = header.decode("ascii").split()
        path = encoded_path.decode("utf-8", errors="strict")
        if not _safe_relative(path):
            raise ValueError("git_tree_path_unsafe")
        if kind == "commit" or mode == "160000":
            if submodule_policy != "allow_registered":
                raise ValueError("submodule_ambiguity_rejected")
            continue
        if mode == "120000" and symlink_policy != "allow_registered":
            raise ValueError("symlink_rejected")
        if kind != "blob" or mode not in {"100644", "100755", "120000"}:
            raise ValueError("unsupported_git_tree_entry")
        content = bytes(_git(repo, "cat-file", "blob", object_id, binary=True))
        entries.append(_TreeEntry(path, mode, kind, object_id, content))
    return tree_id, sorted(entries, key=lambda item: item.path.encode("utf-8"))


def build_source_capsule(
    *,
    repo: str | Path,
    repository_origin: str,
    candidate_id: str,
    candidate_commit: str,
    archive_path: str | Path,
    producer_identity: str,
    producer_job: str,
    consumer_identity: str,
    destination: str,
    expiry: str,
    network_policy: str = "bounded_read_only_acquisition_then_none",
    activation_policy: str = "verify_before_extract",
    symlink_policy: str = "reject",
    submodule_policy: str = "reject",
) -> dict[str, object]:
    repo_path = Path(repo).resolve()
    archive = Path(archive_path).resolve()
    origin = str(_git(repo_path, "remote", "get-url", "origin"))
    if origin.rstrip("/").removesuffix(".git") != repository_origin.rstrip("/").removesuffix(".git"):
        raise ValueError("repository_origin_mismatch")
    tree_id, entries = _tree_entries(repo_path, candidate_commit, symlink_policy=symlink_policy, submodule_policy=submodule_policy)
    created = str(_git(repo_path, "show", "-s", "--format=%cI", candidate_commit))
    manifest: dict[str, object] = {
        "capsule_contract_version": 1,
        "capsule_type": CapsuleType.SOURCE.value,
        "candidate_id": candidate_id,
        "repository_origin": repository_origin,
        "candidate_commit": candidate_commit,
        "git_tree_id": tree_id,
        "entry_count": len(entries),
        "entries": [entry.record() for entry in entries],
        "symlink_policy": symlink_policy,
        "submodule_policy": submodule_policy,
        "producer_identity": producer_identity,
        "producer_job": producer_job,
        "consumer_identity": consumer_identity,
        "destination": destination,
        "creation_time": created,
        "expiry": expiry,
        "network_policy": network_policy,
        "activation_policy": activation_policy,
        "archive_sha256_scope": "external_producer_receipt_to_avoid_self_reference",
    }
    manifest["capsule_id"] = _sha_bytes(_canonical_bytes(manifest))
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w") as payload:
        payload.writestr(_zip_info("CAPSULE_MANIFEST.json", stat.S_IFREG | 0o644), manifest_bytes)
        for entry in entries:
            permissions = 0o755 if entry.mode == "100755" else 0o644
            payload.writestr(_zip_info(f"payload/{entry.path}", stat.S_IFREG | permissions), entry.content)
    receipt = {
        "status": "PASS",
        "capsule_id": manifest["capsule_id"],
        "capsule_type": CapsuleType.SOURCE.value,
        "archive_path": str(archive),
        "archive_sha256": _sha_file(archive),
        "archive_size": archive.stat().st_size,
        "manifest_sha256": _sha_bytes(manifest_bytes),
        "entry_count": len(entries),
        "git_tree_id": tree_id,
        "candidate_id": candidate_id,
        "candidate_commit": candidate_commit,
        "producer_identity": producer_identity,
        "consumer_identity": consumer_identity,
    }
    _write_json(archive.with_suffix(archive.suffix + ".manifest.json"), manifest)
    _write_json(archive.with_suffix(archive.suffix + ".receipt.json"), receipt)
    verification = verify_capsule(archive)
    if verification["status"] != "PASS":
        raise ValueError("source_capsule_self_verification_failed")
    return {**receipt, "self_verification": verification}


def build_file_capsule(
    *,
    capsule_type: CapsuleType,
    files: Iterable[Path],
    archive_path: str | Path,
    candidate_id: str,
    producer_identity: str,
    consumer_identity: str,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    if capsule_type is CapsuleType.SOURCE:
        raise ValueError("source_capsules_require_git_object_construction")
    archive = Path(archive_path).resolve()
    rows: list[tuple[str, Path, bytes]] = []
    for item in sorted((Path(value).resolve() for value in files), key=lambda value: value.name.casefold()):
        if not item.is_file():
            raise ValueError("capsule_input_not_file")
        residue = scan_transport_residue([item.name])
        if residue["residue_count"]:
            raise ValueError("forbidden_transport_residue")
        rows.append((item.name, item, item.read_bytes()))
    if len({name.casefold() for name, _, _ in rows}) != len(rows):
        raise ValueError("duplicate_capsule_path")
    manifest: dict[str, object] = {
        "capsule_contract_version": 1,
        "capsule_type": capsule_type.value,
        "candidate_id": candidate_id,
        "producer_identity": producer_identity,
        "consumer_identity": consumer_identity,
        "entry_count": len(rows),
        "entries": [{"path": name, "content_sha256": _sha_bytes(content), "size": len(content), "executable": False} for name, _, content in rows],
        "metadata": metadata or {},
    }
    manifest["capsule_id"] = _sha_bytes(_canonical_bytes(manifest))
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w") as payload:
        payload.writestr(_zip_info("CAPSULE_MANIFEST.json", stat.S_IFREG | 0o644), manifest_bytes)
        for name, _, content in rows:
            payload.writestr(_zip_info(f"payload/{name}", stat.S_IFREG | 0o644), content)
    receipt = {
        "status": "PASS",
        "capsule_id": manifest["capsule_id"],
        "capsule_type": capsule_type.value,
        "archive_path": str(archive),
        "archive_sha256": _sha_file(archive),
        "manifest_sha256": _sha_bytes(manifest_bytes),
        "entry_count": len(rows),
        "candidate_id": candidate_id,
        "producer_identity": producer_identity,
        "consumer_identity": consumer_identity,
    }
    _write_json(archive.with_suffix(archive.suffix + ".manifest.json"), manifest)
    _write_json(archive.with_suffix(archive.suffix + ".receipt.json"), receipt)
    return {**receipt, "self_verification": verify_capsule(archive)}


def acquire_provider_capsule(
    *,
    candidate_id: str,
    packages: Iterable[dict[str, object]],
    cutoff: str,
    download_root: str | Path,
    archive_path: str | Path,
    producer_identity: str,
    consumer_identity: str,
) -> dict[str, object]:
    root = Path(download_root).resolve()
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    cutoff_time = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    acquisition: list[dict[str, object]] = []
    files: list[Path] = []
    licenses: list[dict[str, object]] = []
    for package in packages:
        name = str(package["name"])
        version = str(package["version"])
        before = {item.name for item in root.iterdir()}
        command = [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--no-deps",
            "--dest",
            str(root),
            f"{name}=={version}",
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        created = sorted((item for item in root.iterdir() if item.name not in before and item.is_file()), key=lambda item: item.name.casefold())
        observed_sha = _sha_file(created[0]) if len(created) == 1 else None
        matched: dict[str, object] | None = None
        metadata: dict[str, object] = {}
        if completed.returncode == 0 and observed_sha:
            with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=30) as response:
                metadata = json.load(response)
            matched = next(
                (row for row in metadata.get("urls", []) if row.get("digests", {}).get("sha256") == observed_sha),
                None,
            )
        uploaded = str(matched.get("upload_time_iso_8601")) if matched else None
        uploaded_time = datetime.fromisoformat(uploaded.replace("Z", "+00:00")) if uploaded else None
        cutoff_pass = uploaded_time is not None and uploaded_time <= cutoff_time
        record = {
            "name": name,
            "version": version,
            "dependency_parent": package.get("dependency_parent"),
            "reason": package.get("reason"),
            "command_hash": _sha_bytes(_canonical_bytes(command)),
            "return_code": completed.returncode,
            "stdout_sha256": _sha_bytes(completed.stdout.encode()),
            "stderr_sha256": _sha_bytes(completed.stderr.encode()),
            "artifact": created[0].name if len(created) == 1 else None,
            "artifact_sha256": observed_sha,
            "registry_sha256": matched.get("digests", {}).get("sha256") if matched else None,
            "registry_hash_match": observed_sha is not None and observed_sha == (matched.get("digests", {}).get("sha256") if matched else None),
            "upload_time": uploaded,
            "observed_at_or_before_cutoff": cutoff_pass,
        }
        acquisition.append(record)
        licenses.append(
            {
                "name": name,
                "version": version,
                "license_expression": metadata.get("info", {}).get("license_expression"),
                "license": metadata.get("info", {}).get("license"),
            }
        )
        if completed.returncode != 0 or len(created) != 1 or not record["registry_hash_match"] or not cutoff_pass:
            return {
                "status": "BLOCK",
                "exact_blocker": "provider_cutoff_or_registry_identity_failed",
                "candidate_id": candidate_id,
                "cutoff": cutoff,
                "acquisition": acquisition,
            }
        files.append(created[0])
    capsule = build_file_capsule(
        capsule_type=CapsuleType.PROVIDER,
        files=files,
        archive_path=archive_path,
        candidate_id=candidate_id,
        producer_identity=producer_identity,
        consumer_identity=consumer_identity,
        metadata={
            "cutoff": cutoff,
            "cutoff_policy": "exact_registered_versions_observed_at_or_before_cutoff",
            "acquisition": acquisition,
            "dependency_graph": [
                {"name": row["name"], "version": row["version"], "dependency_parent": row["dependency_parent"]}
                for row in acquisition
            ],
            "sbom": [{"name": row["name"], "version": row["version"], "sha256": row["artifact_sha256"]} for row in acquisition],
            "license_inventory": licenses,
            "provider_contract": {
                "network_after_acquisition": "none",
                "environment_payload_in_capsule": False,
                "site_packages_in_capsule": False,
                "compiled_cache_in_capsule": False,
            },
        },
    )
    return {**capsule, "cutoff": cutoff, "acquisition": acquisition, "provider_capsule_result": "PASS"}


def scan_transport_residue(paths: Iterable[str]) -> dict[str, object]:
    residue: list[dict[str, str]] = []
    for raw in paths:
        path = PurePosixPath(raw.replace("\\", "/"))
        lowered_parts = {part.casefold() for part in path.parts}
        reason = None
        if lowered_parts & {part.casefold() for part in _FORBIDDEN_TRANSPORT_PARTS}:
            reason = "forbidden_runtime_or_checkout_path"
        elif path.name.casefold() in {name.casefold() for name in _FORBIDDEN_TRANSPORT_NAMES}:
            reason = "environment_activation_or_configuration_file"
        elif path.name.casefold().endswith(_FORBIDDEN_TRANSPORT_SUFFIXES):
            reason = "compiled_cache_file"
        if reason:
            residue.append({"path": raw, "reason": reason})
    return {"status": "PASS" if not residue else "FAIL", "residue_count": len(residue), "residue": residue}


def verify_capsule(archive_path: str | Path) -> dict[str, object]:
    archive = Path(archive_path).resolve()
    failures: list[str] = []
    with zipfile.ZipFile(archive) as payload:
        infos = payload.infolist()
        names = [item.filename for item in infos]
        if names.count("CAPSULE_MANIFEST.json") != 1:
            return {"status": "FAIL", "failures": ["capsule_manifest_missing_or_duplicate"]}
        if len({name.casefold() for name in names}) != len(names):
            failures.append("duplicate_archive_path")
        if any(not _safe_relative(name) for name in names):
            failures.append("unsafe_archive_path")
        residue = scan_transport_residue(names)
        if residue["status"] != "PASS":
            failures.append("forbidden_transport_residue")
        manifest = json.loads(payload.read("CAPSULE_MANIFEST.json").decode("utf-8"))
        expected = {str(row["path"]): row for row in manifest.get("entries", [])}
        observed: dict[str, dict[str, object]] = {}
        for info in infos:
            if not info.filename.startswith("payload/") or info.is_dir():
                continue
            relative = info.filename.removeprefix("payload/")
            content = payload.read(info.filename)
            mode = (info.external_attr >> 16) & 0o777
            observed[relative] = {
                "content_sha256": _sha_bytes(content),
                "size": len(content),
                "executable": bool(mode & 0o111),
            }
        missing = sorted(set(expected) - set(observed))
        extras = sorted(set(observed) - set(expected))
        mismatches = sorted(
            path
            for path in set(expected) & set(observed)
            if any(expected[path].get(key) != observed[path].get(key) for key in ("content_sha256", "size", "executable"))
        )
        if missing:
            failures.append("manifest_paths_missing")
        if extras:
            failures.append("unmanifested_paths_present")
        if mismatches:
            failures.append("manifest_entry_mismatch")
        if manifest.get("entry_count") != len(observed):
            failures.append("entry_count_mismatch")
        manifest_without_id = dict(manifest)
        capsule_id = manifest_without_id.pop("capsule_id", None)
        if capsule_id != _sha_bytes(_canonical_bytes(manifest_without_id)):
            failures.append("capsule_id_mismatch")
    return {
        "status": "PASS" if not failures else "FAIL",
        "archive_path": str(archive),
        "archive_sha256": _sha_file(archive),
        "capsule_id": manifest.get("capsule_id"),
        "capsule_type": manifest.get("capsule_type"),
        "candidate_id": manifest.get("candidate_id"),
        "git_tree_id": manifest.get("git_tree_id"),
        "manifest_sha256": _sha_bytes(json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"),
        "entry_count": len(observed),
        "missing_paths": missing,
        "extra_paths": extras,
        "mismatched_paths": mismatches,
        "transport_residue": residue,
        "failures": failures,
    }


def activate_source_capsule(archive_path: str | Path, destination: str | Path) -> dict[str, object]:
    verification = verify_capsule(archive_path)
    if verification["status"] != "PASS" or verification["capsule_type"] != CapsuleType.SOURCE.value:
        return {**verification, "activated": False, "exact_blocker": "source_capsule_not_activatable"}
    destination_path = Path(destination).resolve()
    shutil.rmtree(destination_path, ignore_errors=True)
    destination_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as payload:
        manifest = json.loads(payload.read("CAPSULE_MANIFEST.json").decode("utf-8"))
        for row in manifest["entries"]:
            relative = str(row["path"])
            target = destination_path / Path(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload.read(f"payload/{relative}"))
            target.chmod(0o755 if row.get("executable") else 0o644)
    observed = {
        path.relative_to(destination_path).as_posix(): {
            "content_sha256": _sha_file(path),
            "size": path.stat().st_size,
            "executable": bool(path.stat().st_mode & stat.S_IXUSR) if os.name != "nt" else expected_executable,
        }
        for path in sorted(destination_path.rglob("*"))
        if path.is_file()
        for expected_executable in [next(bool(row["executable"]) for row in manifest["entries"] if row["path"] == path.relative_to(destination_path).as_posix())]
    }
    expected = {
        str(row["path"]): {
            "content_sha256": row["content_sha256"],
            "size": row["size"],
            "executable": row["executable"],
        }
        for row in manifest["entries"]
    }
    conserved = observed == expected
    return {
        **verification,
        "status": "PASS" if conserved else "FAIL",
        "activated": conserved,
        "destination": str(destination_path),
        "producer_consumer_conservation": conserved,
        "mode_verification": "POSIX_EXACT" if os.name != "nt" else "ARCHIVE_EXACT_EXTRACTION_PLATFORM_LIMITED",
        "observed_entry_count": len(observed),
        "expected_entry_count": len(expected),
        "exact_blocker": None if conserved else "source_capsule_conservation_failed",
    }


def activate_provider_capsule(archive_path: str | Path, destination: str | Path) -> dict[str, object]:
    """Create an offline provider environment from a verified distribution-only capsule."""
    verification = verify_capsule(archive_path)
    if verification["status"] != "PASS" or verification["capsule_type"] != CapsuleType.PROVIDER.value:
        return {**verification, "activated": False, "exact_blocker": "provider_capsule_not_activatable"}
    destination_path = Path(destination).resolve()
    shutil.rmtree(destination_path, ignore_errors=True)
    wheelhouse = destination_path / "wheelhouse"
    wheelhouse.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as payload:
        manifest = json.loads(payload.read("CAPSULE_MANIFEST.json").decode("utf-8"))
        for row in manifest["entries"]:
            target = wheelhouse / Path(str(row["path"])).name
            target.write_bytes(payload.read(f"payload/{row['path']}"))
    environment = destination_path / "environment"
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True, text=True, capture_output=True)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    distributions = sorted(str(path) for path in wheelhouse.iterdir() if path.is_file())
    install = subprocess.run(
        [str(python), "-m", "pip", "install", "--no-index", "--no-deps", *distributions],
        text=True, capture_output=True, check=False,
    )
    freeze = subprocess.run([str(python), "-m", "pip", "freeze", "--all"], text=True, capture_output=True, check=False)
    activated = install.returncode == 0 and freeze.returncode == 0
    distribution_identity = [
        {"name": path.name, "sha256": _sha_file(path), "size": path.stat().st_size}
        for path in sorted(wheelhouse.iterdir(), key=lambda item: item.name.casefold()) if path.is_file()
    ]
    identity = _sha_bytes(_canonical_bytes(distribution_identity)) if activated else None
    return {
        **verification,
        "status": "PASS" if activated else "FAIL",
        "activated": activated,
        "destination": str(destination_path),
        "python": str(python),
        "distribution_count": len(distributions),
        "distribution_graph_sha256": identity,
        "distribution_graph": distribution_identity,
        "pip_freeze_raw_sha256": _sha_bytes(freeze.stdout.encode()) if activated else None,
        "install_return_code": install.returncode,
        "install_stdout_sha256": _sha_bytes(install.stdout.encode()),
        "install_stderr_sha256": _sha_bytes(install.stderr.encode()),
        "network_policy": "none",
        "exact_blocker": None if activated else "offline_provider_activation_failed",
    }
