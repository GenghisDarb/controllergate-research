from __future__ import annotations

from controllergate.core.transport import (
    compare_transfer_hashes,
    hash_after_transfer,
    hash_before_transfer,
    record_workspace_to_repo_transfer,
    reject_unsafe_transport_paths,
)


def test_transport_hash_record(tmp_path):
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination.txt"
    source.write_text("ok\n", encoding="utf-8", newline="\n")
    destination.write_text("ok\n", encoding="utf-8", newline="\n")

    assert compare_transfer_hashes(hash_before_transfer(source), hash_after_transfer(destination))
    record = record_workspace_to_repo_transfer(
        source,
        destination,
        transfer_reason="unit_test",
        allowlist_class="test_fixture",
    )
    assert record["transport_decision"] == "PASS"


def test_transport_rejects_unsafe_paths():
    assert reject_unsafe_transport_paths(["safe/file.txt", "../bad.txt", "x/__pycache__/y.pyc", "artifact.zip"]) == [
        "../bad.txt",
        "x/__pycache__/y.pyc",
        "artifact.zip",
    ]
