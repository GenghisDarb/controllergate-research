from __future__ import annotations

import hashlib
import zipfile

from controllergate.core.evidence import (
    duplicate_zip_paths,
    hash_record,
    safe_zip_paths,
    sha256_bytes,
    sha256_file,
    verify_zip_artifact,
    write_json_deterministic,
)


def test_sha256_helpers_and_deterministic_json(tmp_path):
    target = tmp_path / "record.json"
    write_json_deterministic(target, {"b": 2, "a": 1})

    assert target.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}\n'
    assert sha256_bytes(b"abc") == hashlib.sha256(b"abc").hexdigest()
    assert sha256_file(target) == hashlib.sha256(target.read_bytes()).hexdigest()
    assert hash_record({"b": 2, "a": 1}) == hash_record({"a": 1, "b": 2})


def test_zip_path_safety_and_identity(tmp_path):
    zip_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("outputs/lane/file.txt", "ok\n")
        archive.writestr("../unsafe.txt", "bad\n")

    assert safe_zip_paths(zip_path) == ["outputs/lane/file.txt"]
    assert duplicate_zip_paths(zip_path) == []

    result = verify_zip_artifact(
        zip_path,
        expected_size=zip_path.stat().st_size,
        expected_sha256=sha256_file(zip_path),
    )
    assert result["status"] == "FAIL"
    assert result["unsafe_path_count"] == 1
