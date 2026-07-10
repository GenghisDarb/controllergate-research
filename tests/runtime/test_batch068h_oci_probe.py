from __future__ import annotations

from pathlib import Path

from controllergate.runtime.container_evidence import inspect_security_observation
from controllergate.runtime.network_policy import execution_network_policy
from controllergate.runtime.oci_probe_sandbox import secure_container_create_command
from controllergate.runtime.provider_pipeline import verify_archive_manifest
from controllergate.runtime.resource_policy import ResourcePolicy
from controllergate.runtime.workspace_snapshot import diff_snapshots, snapshot_tree


def test_secure_oci_command_has_required_controls(tmp_path: Path) -> None:
    source = tmp_path / "source"; wheelhouse = tmp_path / "wheelhouse"; source.mkdir(); wheelhouse.mkdir()
    command, user = secure_container_create_command(image_digest="python@sha256:" + "a" * 64, source=source, wheelhouse=wheelhouse, command=["python", "--version"], name="test", resource_policy=ResourcePolicy())
    joined = " ".join(command)
    for token in ["--read-only", "--cap-drop ALL", "--security-opt no-new-privileges", "--network none", "--pids-limit 256", "--memory 2g", "--memory-swap 2g", "--cpus 2"]: assert token in joined
    assert user not in {"0", "0:0", "root"}
    assert "docker.sock" not in joined


def test_container_policy_observation() -> None:
    record = {"Config": {"User": "1001:1001"}, "HostConfig": {"ReadonlyRootfs": True, "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges"], "NetworkMode": "none", "Privileged": False, "PidMode": "", "IpcMode": "private", "Memory": 2147483648, "MemorySwap": 2147483648, "PidsLimit": 256, "NanoCpus": 2000000000, "Ulimits": [{"Name": "nofile", "Soft": 1024, "Hard": 1024}]}, "Mounts": [{"Destination": "/source", "RW": False}]}
    observed = inspect_security_observation(record, expected_user="1001:1001")
    assert observed["status"] == "PASS"
    assert observed["network_isolation_verified"] is True


def test_network_none_policy() -> None:
    policy = execution_network_policy()
    assert policy["network_mode"] == "none"
    assert policy["network_requests_allowed"] is False


def test_workspace_snapshots_diff_and_rollback(tmp_path: Path) -> None:
    source = tmp_path / "source"; source.mkdir(); (source / "a.py").write_text("x=1\n", encoding="utf-8")
    pre = snapshot_tree(source); post = snapshot_tree(source)
    assert diff_snapshots(pre, post)["status"] == "PASS"
    (source / "a.py").write_text("x=2\n", encoding="utf-8")
    changed = snapshot_tree(source)
    assert diff_snapshots(pre, changed)["mutation_count"] == 1


def test_provider_archive_hash_verification(tmp_path: Path) -> None:
    wheel = tmp_path / "x-1-py3-none-any.whl"; wheel.write_bytes(b"wheel")
    import hashlib
    record = [{"filename": wheel.name, "sha256": hashlib.sha256(b"wheel").hexdigest()}]
    assert verify_archive_manifest(tmp_path, record)["status"] == "PASS"
    wheel.write_bytes(b"changed")
    assert verify_archive_manifest(tmp_path, record)["status"] == "BLOCK"
