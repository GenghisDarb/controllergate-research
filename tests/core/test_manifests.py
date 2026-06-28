from __future__ import annotations

from controllergate.core.manifests import (
    read_sha256sums,
    reject_unsafe_paths,
    verify_manifest,
    write_sha256sums,
)


def test_manifest_roundtrip(tmp_path):
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8", newline="\n")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "b.txt").write_text("beta\n", encoding="utf-8", newline="\n")

    manifest = write_sha256sums(tmp_path)
    entries = read_sha256sums(manifest)

    assert sorted(entries) == ["a.txt", "nested/b.txt"]
    assert verify_manifest(tmp_path)["status"] == "PASS"


def test_manifest_rejects_unsafe_paths():
    assert reject_unsafe_paths(["safe/file.txt", "../bad.txt", "bad\\path.txt"]) == [
        "../bad.txt",
        "bad\\path.txt",
    ]
