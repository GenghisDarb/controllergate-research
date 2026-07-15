from __future__ import annotations

import json
import os
import subprocess
import zipfile
from pathlib import Path

import pytest

from controllergate.core.artifacts import verify_zip_manifest
from controllergate.custody.capsules import (
    CapsuleType,
    activate_source_capsule,
    build_file_capsule,
    build_source_capsule,
    scan_transport_residue,
    verify_capsule,
)


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()


@pytest.fixture
def source_repository(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "batch091@example.invalid")
    git(repo, "config", "user.name", "Batch091 Test")
    git(repo, "remote", "add", "origin", "https://example.invalid/project.git")
    (repo / ".gitignore").write_text("*.tmp\n", encoding="utf-8", newline="\n")
    workflow = repo / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("name: ci\n", encoding="utf-8", newline="\n")
    script = repo / "run.sh"
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8", newline="\n")
    if os.name != "nt":
        script.chmod(0o755)
    git(repo, "add", ".")
    env = {**os.environ, "GIT_AUTHOR_DATE": "2024-01-02T03:04:05Z", "GIT_COMMITTER_DATE": "2024-01-02T03:04:05Z"}
    git(repo, "commit", "-m", "fixture", env=env)
    return repo, git(repo, "rev-parse", "HEAD")


def test_git_object_capsule_preserves_hidden_files_and_identity(source_repository: tuple[Path, str], tmp_path: Path) -> None:
    repo, commit = source_repository
    capsule = tmp_path / "source.zip"
    receipt = build_source_capsule(
        repo=repo,
        repository_origin="https://example.invalid/project",
        candidate_id="fixture",
        candidate_commit=commit,
        archive_path=capsule,
        producer_identity="test.producer",
        producer_job="test",
        consumer_identity="test.consumer",
        destination="runtime/source",
        expiry="2027-01-01T00:00:00Z",
    )
    assert receipt["status"] == "PASS"
    assert receipt["entry_count"] == 3
    verification = verify_capsule(capsule)
    assert verification["status"] == "PASS"
    with zipfile.ZipFile(capsule) as archive:
        assert "payload/.gitignore" in archive.namelist()
        assert "payload/.github/workflows/ci.yml" in archive.namelist()
        manifest = json.loads(archive.read("CAPSULE_MANIFEST.json"))
    assert manifest["git_tree_id"] == git(repo, "rev-parse", f"{commit}^{{tree}}")
    activated = activate_source_capsule(capsule, tmp_path / "activated")
    assert activated["status"] == "PASS"
    assert activated["producer_consumer_conservation"] is True


def test_source_capsule_is_deterministic(source_repository: tuple[Path, str], tmp_path: Path) -> None:
    repo, commit = source_repository
    kwargs = dict(
        repo=repo,
        repository_origin="https://example.invalid/project",
        candidate_id="fixture",
        candidate_commit=commit,
        producer_identity="test.producer",
        producer_job="test",
        consumer_identity="test.consumer",
        destination="runtime/source",
        expiry="2027-01-01T00:00:00Z",
    )
    first = build_source_capsule(archive_path=tmp_path / "a.zip", **kwargs)
    second = build_source_capsule(archive_path=tmp_path / "b.zip", **kwargs)
    assert first["archive_sha256"] == second["archive_sha256"]


def test_missing_hidden_file_is_rejected(source_repository: tuple[Path, str], tmp_path: Path) -> None:
    repo, commit = source_repository
    capsule = tmp_path / "source.zip"
    build_source_capsule(
        repo=repo,
        repository_origin="https://example.invalid/project",
        candidate_id="fixture",
        candidate_commit=commit,
        archive_path=capsule,
        producer_identity="test.producer",
        producer_job="test",
        consumer_identity="test.consumer",
        destination="runtime/source",
        expiry="2027-01-01T00:00:00Z",
    )
    mutated = tmp_path / "mutated.zip"
    with zipfile.ZipFile(capsule) as source, zipfile.ZipFile(mutated, "w") as target:
        for item in source.infolist():
            if item.filename != "payload/.gitignore":
                target.writestr(item, source.read(item))
    result = verify_capsule(mutated)
    assert result["status"] == "FAIL"
    assert "manifest_paths_missing" in result["failures"]


@pytest.mark.parametrize("path", ["venv/pyvenv.cfg", "x/site-packages/a.py", "x/__pycache__/a.pyc", ".git/config", "bin/activate"])
def test_transport_residue_is_rejected(path: str) -> None:
    result = scan_transport_residue([path])
    assert result["status"] == "FAIL"
    assert result["residue_count"] == 1


def test_provider_capsule_contains_files_not_environment(tmp_path: Path) -> None:
    wheel = tmp_path / "dependency-1.0-py3-none-any.whl"
    wheel.write_bytes(b"registered wheel")
    capsule = tmp_path / "provider.zip"
    result = build_file_capsule(
        capsule_type=CapsuleType.PROVIDER,
        files=[wheel],
        archive_path=capsule,
        candidate_id="fixture",
        producer_identity="test.producer",
        consumer_identity="test.consumer",
        metadata={"cutoff": "2024-01-01T00:00:00Z"},
    )
    assert result["status"] == "PASS"
    assert verify_capsule(capsule)["status"] == "PASS"


def test_portable_manifest_dot_prefix_is_supported(tmp_path: Path) -> None:
    archive = tmp_path / "artifact.zip"
    payload = b"value\n"
    import hashlib

    with zipfile.ZipFile(archive, "w") as target:
        target.writestr("value.txt", payload)
        target.writestr("PORTABLE_ARTIFACT_SHA256SUMS.txt", f"{hashlib.sha256(payload).hexdigest()}  ./value.txt\n")
    result = verify_zip_manifest(archive, "PORTABLE_ARTIFACT_SHA256SUMS.txt")
    assert result["status"] == "PASS"
    assert result["checked"] == 1
