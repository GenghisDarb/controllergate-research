from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from controllergate.core.artifacts import (
    audit_zip_entries,
    safe_copy_verified_payload,
    verify_artifact_zip,
    verify_zip_manifest,
)


def _write_zip(path: Path, files: dict[str, bytes], *, manifest: bool = True) -> None:
    rows = [f"{hashlib.sha256(data).hexdigest()}  {name}" for name, data in files.items()]
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        if manifest:
            archive.writestr("ARTIFACT_SHA256SUMS.txt", "\n".join(rows) + "\n")
            archive.writestr("SHA256SUMS.txt", "\n".join(rows) + "\n")


def test_valid_zip_with_manifest_passes(tmp_path: Path) -> None:
    zip_path = tmp_path / "artifact.zip"
    _write_zip(zip_path, {"outputs/example/result.json": b'{"status":"PASS"}\n'})
    assert verify_artifact_zip(zip_path)["status"] == "PASS"


def test_unsafe_zip_path_rejected(tmp_path: Path) -> None:
    zip_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("../escape.txt", b"bad")
        archive.writestr("ARTIFACT_SHA256SUMS.txt", "")
        archive.writestr("SHA256SUMS.txt", "")
    assert audit_zip_entries(zip_path)["unsafe_path_count"] == 1


def test_duplicate_path_detected(tmp_path: Path) -> None:
    zip_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("a.txt", b"one")
        archive.writestr("a.txt", b"two")
        archive.writestr("ARTIFACT_SHA256SUMS.txt", "")
        archive.writestr("SHA256SUMS.txt", "")
    assert audit_zip_entries(zip_path)["duplicate_path_count"] == 1


def test_manifest_missing_and_malformed_detected(tmp_path: Path) -> None:
    missing = tmp_path / "missing.zip"
    _write_zip(missing, {"a.txt": b"a"}, manifest=False)
    assert verify_zip_manifest(missing, "SHA256SUMS.txt")["missing_manifest"] is True
    malformed = tmp_path / "malformed.zip"
    with zipfile.ZipFile(malformed, "w") as archive:
        archive.writestr("a.txt", b"a")
        archive.writestr("SHA256SUMS.txt", "not-a-valid-line\n")
    assert verify_zip_manifest(malformed, "SHA256SUMS.txt")["malformed"]


def test_manifest_missing_file_and_hash_mismatch_detected(tmp_path: Path) -> None:
    zip_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("a.txt", b"a")
        archive.writestr("SHA256SUMS.txt", f"{'0'*64}  a.txt\n{'1'*64}  absent.txt\n")
    result = verify_zip_manifest(zip_path, "SHA256SUMS.txt")
    assert result["failures"] == ["a.txt"]
    assert result["missing"] == ["absent.txt"]


def test_raw_zip_payload_is_not_copied(tmp_path: Path) -> None:
    zip_path = tmp_path / "artifact.zip"
    _write_zip(zip_path, {"outputs/example/result.json": b"{}", "outputs/example/nested.zip": b"zip"})
    dest = tmp_path / "dest"
    result = safe_copy_verified_payload(zip_path, dest, allowed_prefixes=("outputs/example",))
    assert result["raw_zip_payload_copied"] is False
    assert (dest / "outputs/example/result.json").is_file()
    assert not (dest / "outputs/example/nested.zip").exists()
