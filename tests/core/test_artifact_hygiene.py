from __future__ import annotations

from controllergate.core.artifact_hygiene import audit_artifact_payload, is_cache_or_archive_payload, stage_artifact_payload, write_artifact_manifest


def test_artifact_payload_excludes_cache_and_compiled_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "outputs").mkdir()
    (source / "outputs" / "ok.json").write_text("{}\n", encoding="utf-8", newline="\n")
    cache_dir = source / "outputs" / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "bad.pyc").write_bytes(b"bad")

    payload = tmp_path / "payload"
    result = stage_artifact_payload(payload, [source / "outputs"])
    manifest = write_artifact_manifest(payload)
    audit = audit_artifact_payload(payload)

    assert "outputs/ok.json" in result["copied_files"]
    assert all("__pycache__" not in item for item in manifest["covered_files"])
    assert audit["status"] == "PASS"
    assert audit["cache_payloads"] == []


def test_artifact_hygiene_detects_forbidden_payloads():
    assert is_cache_or_archive_payload("x/__pycache__/bad.pyc")
    assert is_cache_or_archive_payload("artifact.zip")
    assert not is_cache_or_archive_payload("outputs/report.json")
