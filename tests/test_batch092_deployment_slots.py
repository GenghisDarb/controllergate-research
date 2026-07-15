from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from controllergate.deployment.slot_manager import BrokerBackedSlotManager


def _package(root: Path, name: str, value: str) -> tuple[Path, str]:
    package = root / name
    package.mkdir()
    payload = (value + "\n").encode()
    (package / "identity.txt").write_bytes(payload)
    return package, hashlib.sha256(payload).hexdigest()


def test_real_atomic_slot_switch_health_rollback_and_cleanup(tmp_path: Path) -> None:
    original, original_hash = _package(tmp_path, "original-package", "original")
    repaired, repaired_hash = _package(tmp_path, "repaired-package", "repaired")
    manager = BrokerBackedSlotManager(tmp_path / "runtime", "deployment")
    manager.materialize(slot_id="original", package_source=original, package_hash="a" * 64, source_hash="b" * 64, provider_identity="provider", interpreter_identity="python", parent_slot=None, rollback_slot=None, health_contract={"path": "identity.txt"})
    manager.materialize(slot_id="repaired", package_source=repaired, package_hash="c" * 64, source_hash="d" * 64, provider_identity="provider", interpreter_identity="python", parent_slot="original", rollback_slot="original", health_contract={"path": "identity.txt"})
    manager.switch("original", authorization_id="initial")
    assert manager.prove_active_content("identity.txt")["content_sha256"] == original_hash
    transition = manager.switch("repaired", authorization_id="switch")
    assert transition["atomic_mechanism"] == "os.replace_pointer_file"
    assert manager.prove_active_content("identity.txt")["content_sha256"] == repaired_hash
    events = [manager.health(event_id=f"health-{index}", relative_path="identity.txt", expected_sha256=repaired_hash) for index in range(3)]
    assert len({row["event_hash"] for row in events}) == 3
    assert all(row["status"] == "PASS" for row in events)
    manager.rollback("original", authorization_id="rollback")
    assert manager.prove_active_content("identity.txt")["content_sha256"] == original_hash
    assert manager.cleanup("repaired")["state"] == "CLEANED"
    assert all(row["adapter"].endswith("BrokerBackedSlotManager") for row in manager.operations)


def test_active_slot_cannot_be_cleaned(tmp_path: Path) -> None:
    package, _ = _package(tmp_path, "package", "active")
    manager = BrokerBackedSlotManager(tmp_path / "runtime", "deployment")
    manager.materialize(slot_id="active", package_source=package, package_hash="a" * 64, source_hash="b" * 64, provider_identity="provider", interpreter_identity="python", parent_slot=None, rollback_slot=None, health_contract={"path": "identity.txt"})
    manager.switch("active", authorization_id="initial")
    with pytest.raises(ValueError, match="active slot cannot be cleaned"):
        manager.cleanup("active")
