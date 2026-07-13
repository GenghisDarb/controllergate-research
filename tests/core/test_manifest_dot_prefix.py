from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from controllergate.core.official_ingest import verify_zip_manifest


def test_outer_manifest_accepts_safe_dot_slash_prefix(tmp_path: Path):
    payload = b"evidence\n"
    archive_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("evidence.json", payload)
        archive.writestr("ARTIFACT_SHA256SUMS.txt", f"{hashlib.sha256(payload).hexdigest()}  ./evidence.json\n")
    with zipfile.ZipFile(archive_path) as archive:
        result = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
    assert result["status"] == "PASS"
    assert result["checked"] == 1


def test_dot_dot_remains_rejected(tmp_path: Path):
    archive_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("safe.txt", b"safe")
        archive.writestr("ARTIFACT_SHA256SUMS.txt", f"{'0' * 64}  ../safe.txt\n")
    with zipfile.ZipFile(archive_path) as archive:
        result = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
    assert result["status"] == "FAIL"
    assert result["malformed"] == ["../safe.txt"]
