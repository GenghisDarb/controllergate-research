from __future__ import annotations

import sqlite3
import time

import pytest

from controllergate.state.integrity import verify_event_chain
from controllergate.state.lease import acquire, release
from controllergate.state.recovery import recover_run
from controllergate.state.repository import ControllerStateRepository
from controllergate.state.schema import SCHEMA_VERSION, TABLES


def test_schema_wal_foreign_keys_and_migration(tmp_path):
    repo = ControllerStateRepository(tmp_path / "state.db")
    assert repo.connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert repo.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert repo.connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == SCHEMA_VERSION
    present = {row[0] for row in repo.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(TABLES) <= present


def test_atomic_run_stage_idempotency_recovery_and_integrity(tmp_path):
    repo = ControllerStateRepository(tmp_path / "state.db")
    repo.create_run("run-1", "candidate", {"candidate": "candidate"})
    first = repo.complete_stage("run-1", "SOURCE_ACQUIRED", [], ["token-1"])
    second = repo.complete_stage("run-1", "SOURCE_ACQUIRED", [], ["token-1"])
    assert first["event_hash"] == second["event_hash"]
    assert recover_run(repo.connection, "run-1")["stage"] == "SOURCE_ACQUIRED"
    assert repo.load_run("run-1")["integrity"]["status"] == "PASS"


def test_transaction_rolls_back_and_foreign_key_enforces(tmp_path):
    repo = ControllerStateRepository(tmp_path / "state.db")
    with pytest.raises(sqlite3.IntegrityError):
        repo.connection.execute("INSERT INTO run_manifests VALUES ('missing','{}','x')")


def test_tamper_detected(tmp_path):
    repo = ControllerStateRepository(tmp_path / "state.db")
    repo.create_run("run-1", "candidate", {})
    repo.connection.execute("UPDATE events SET status='TAMPERED' WHERE run_id='run-1'")
    assert verify_event_chain(repo.connection, "run-1")["status"] == "FAIL"
    with pytest.raises(RuntimeError, match="tamper"):
        repo.load_run("run-1")


def test_worker_lease_single_owner_expiry_and_release(tmp_path):
    repo = ControllerStateRepository(tmp_path / "state.db")
    repo.create_run("run-1", "candidate", {})
    assert acquire(repo.connection, "run-1", "worker-a", 0.01)
    assert not acquire(repo.connection, "run-1", "worker-b", 30)
    time.sleep(0.02)
    assert acquire(repo.connection, "run-1", "worker-b", 30)
    assert release(repo.connection, "run-1", "worker-b")


@pytest.mark.parametrize("run_id", ["../escape", "a/b", "", "x" * 129])
def test_unsafe_run_id_rejected(tmp_path, run_id):
    repo = ControllerStateRepository(tmp_path / "state.db")
    with pytest.raises(ValueError, match="unsafe"):
        repo.create_run(run_id, "candidate", {})
