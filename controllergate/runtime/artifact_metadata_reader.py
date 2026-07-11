from __future__ import annotations

from email import message_from_bytes
import io
from pathlib import Path, PurePosixPath
import tarfile
import tomllib
import zipfile


def _safe(name: str) -> bool:
    pure = PurePosixPath(name)
    return not name.startswith("/") and "\\" not in name and all(part not in {"", ".", ".."} for part in pure.parts)


def parse_metadata_bytes(payload: bytes) -> dict[str, object]:
    message = message_from_bytes(payload)
    return {"name": message.get("Name"), "version": message.get("Version"), "requires_python": message.get("Requires-Python"), "requires_dist": message.get_all("Requires-Dist") or [], "provides_extra": message.get_all("Provides-Extra") or [], "metadata_version": message.get("Metadata-Version"), "build_requires": [], "build_backend": None}


def read_wheel_metadata(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if any(not _safe(name) for name in names): raise ValueError("unsafe_archive_path")
        targets = [name for name in names if name.endswith(".dist-info/METADATA") and len(PurePosixPath(name).parts) == 2]
        if len(targets) != 1: raise ValueError("wheel_metadata_missing_or_ambiguous")
        return parse_metadata_bytes(archive.read(targets[0]))


def read_sdist_metadata(path: Path) -> dict[str, object]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if any(not _safe(name) for name in names): raise ValueError("unsafe_archive_path")
            targets = [name for name in names if name.endswith(("PKG-INFO", "METADATA"))]
            if not targets: return {"status": "BLOCK", "blocker": "unresolved_dynamic_metadata"}
            result = parse_metadata_bytes(archive.read(sorted(targets)[0]))
            pyprojects = [name for name in names if name.endswith("pyproject.toml")]
            if pyprojects:
                build = tomllib.loads(archive.read(sorted(pyprojects)[0]).decode("utf-8")).get("build-system", {})
                result.update({"build_requires": build.get("requires", []), "build_backend": build.get("build-backend")})
            return {"status": "PASS", **result}
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        if any(not _safe(member.name) for member in members): raise ValueError("unsafe_archive_path")
        targets = [member for member in members if member.name.endswith(("PKG-INFO", "METADATA")) and member.isfile()]
        if not targets: return {"status": "BLOCK", "blocker": "unresolved_dynamic_metadata"}
        handle = archive.extractfile(sorted(targets, key=lambda item: item.name)[0]); assert handle is not None
        result = parse_metadata_bytes(handle.read())
        pyprojects = [member for member in members if member.name.endswith("pyproject.toml") and member.isfile()]
        if pyprojects:
            pyproject_handle = archive.extractfile(sorted(pyprojects, key=lambda item: item.name)[0]); assert pyproject_handle is not None
            build = tomllib.loads(pyproject_handle.read().decode("utf-8")).get("build-system", {})
            result.update({"build_requires": build.get("requires", []), "build_backend": build.get("build-backend")})
        return {"status": "PASS", **result}


def read_artifact_metadata(path: Path) -> dict[str, object]:
    """Read static distribution metadata without executing build-system code."""
    if path.name.endswith(".whl"):
        return {"status": "PASS", **read_wheel_metadata(path)}
    return read_sdist_metadata(path)
