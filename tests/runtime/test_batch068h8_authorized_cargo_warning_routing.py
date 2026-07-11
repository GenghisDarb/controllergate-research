from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tarfile

from controllergate.amds.runtime_adapter import observation_driven_posterior
from controllergate.runtime.batch068h8_pipeline import classify_cargo_failure, migrate_board_v4, semantic_failure_signature
from controllergate.runtime.cargo_vendor import parse_cargo_lock, safe_extract_crate
from controllergate.runtime.execution_authorization import ExecutionAuthorization, ExecutionScope, seal_authorization, verify_authorization
from controllergate.runtime.network_authorization import authorize_network_operation
from controllergate.runtime.network_event_ledger import append_network_event, verify_network_event_ledger
from controllergate.runtime.network_policy import docker_network_mode, validate_network_policy


def bounded(phase: str = "provider") -> dict:
    return {"phase_id": phase, "network_mode": "bounded_read_only", "allowed_network_destinations": ["example.test"], "allowed_protocols": ["https"], "maximum_requests": 2, "maximum_download_bytes": 10, "dns_policy": "system_resolver_logged", "tls_verification_policy": "required", "redirect_policy": "allowlisted_hosts_only", "proxy_policy": "forbidden", "network_log_path": "events.jsonl"}


def test_network_authorization_enforces_phase_destination_tls_and_budgets():
    policy = bounded()
    assert validate_network_policy(policy, phase_id="provider")["status"] == "PASS"
    assert authorize_network_operation(phase_id="other", policy=policy, destination="https://example.test/a", requested_mode="bounded_read_only")["status"] == "BLOCK"
    assert authorize_network_operation(phase_id="provider", policy=policy, destination="https://outside.test/a", requested_mode="bounded_read_only")["blocker"] == "network_destination_not_allowlisted"
    assert authorize_network_operation(phase_id="provider", policy=policy, destination="http://example.test/a", requested_mode="bounded_read_only")["blocker"] == "network_destination_not_allowlisted"
    assert authorize_network_operation(phase_id="provider", policy=policy, destination="https://example.test/a", requested_mode="bounded_read_only", tls_verification=False)["blocker"] == "network_tls_verification_disabled"
    assert authorize_network_operation(phase_id="provider", policy=policy, destination="https://example.test/a", requested_mode="bounded_read_only", projected_requests=3)["blocker"] == "network_request_budget_exceeded"
    assert authorize_network_operation(phase_id="provider", policy=policy, destination="https://example.test/a", requested_mode="bounded_read_only", projected_bytes=11)["blocker"] == "network_byte_budget_exceeded"


def test_network_none_maps_to_docker_none_and_rejects_use():
    policy = {"phase_id": "offline", "network_mode": "none", "allowed_network_destinations": [], "allowed_protocols": [], "maximum_requests": 0, "maximum_download_bytes": 0}
    assert docker_network_mode(policy) == "none"
    assert authorize_network_operation(phase_id="offline", policy=policy, destination="https://example.test", requested_mode="none")["blocker"] == "network_use_from_network_none_phase"


def test_execution_authorization_requires_policy_for_network_phase():
    now = datetime.now(timezone.utc)
    value = seal_authorization(ExecutionAuthorization("a", ExecutionScope("c", "a" * 40, ("provider",), "outputs", ("provider",)), "state", "plan", now.isoformat(), (now + timedelta(hours=1)).isoformat(), "nonce", "plan", "events"))
    result = verify_authorization(value, candidate_id="c", candidate_sha="a" * 40, current_state_hash="state", plan_hash="plan", spent_nonces=set())
    assert result["blocker"] == "network_authorization_phase_policy_mismatch"


def test_network_event_hash_chain(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    append_network_event(path, {"phase_id": "p", "status": "PASS"})
    append_network_event(path, {"phase_id": "p", "status": "BLOCK"})
    assert verify_network_event_ledger(path)["checked"] == 2
    rows = path.read_text().splitlines(); row = json.loads(rows[1]); row["status"] = "PASS"; rows[1] = json.dumps(row); path.write_text("\n".join(rows) + "\n")
    assert verify_network_event_ledger(path)["status"] == "BLOCK"


def test_cargo_failure_classification_and_no_false_failure_on_success():
    assert classify_cargo_failure("Updating crates.io index", 0) == "cargo_fetch_pass"
    assert classify_cargo_failure("Could not resolve host", 1) == "cargo_dns_resolution_failed"
    assert classify_cargo_failure("certificate verify failed", 1) == "cargo_tls_verification_failed"
    assert classify_cargo_failure("HTTP 429", 1) == "cargo_http_rate_limited"
    assert classify_cargo_failure("HTTP 503", 1) == "cargo_http_server_error"
    assert classify_cargo_failure("checksum mismatch", 1) == "cargo_manifest_or_lock_error"


def test_cargo_lock_parser_and_safe_crate_extraction(tmp_path: Path):
    lock = tmp_path / "Cargo.lock"
    lock.write_text('version = 3\n[[package]]\nname = "demo"\nversion = "1.0.0"\nsource = "registry+https://github.com/rust-lang/crates.io-index"\nchecksum = "abc"\n')
    assert parse_cargo_lock(lock) == [{"name": "demo", "version": "1.0.0", "source": "registry+https://github.com/rust-lang/crates.io-index", "checksum": "abc"}]
    archive = tmp_path / "demo.crate"
    with tarfile.open(archive, "w:gz") as tf:
        payload = b"[package]\nname='demo'\nversion='1.0.0'\n"; info = tarfile.TarInfo("demo-1.0.0/Cargo.toml"); info.size = len(payload); tf.addfile(info, io.BytesIO(payload))
    result = safe_extract_crate(archive, tmp_path / "vendor/demo-1.0.0", package="demo", version="1.0.0", checksum="abc")
    assert result["status"] == "PASS"
    assert json.loads((tmp_path / "vendor/demo-1.0.0/.cargo-checksum.json").read_text())["package"] == "abc"


def test_safe_crate_extraction_rejects_traversal(tmp_path: Path):
    archive = tmp_path / "bad.crate"
    with tarfile.open(archive, "w:gz") as tf:
        payload = b"bad"; info = tarfile.TarInfo("demo-1.0.0/../escape"); info.size = len(payload); tf.addfile(info, io.BytesIO(payload))
    assert safe_extract_crate(archive, tmp_path / "vendor", package="demo", version="1.0.0", checksum="abc")["status"] == "BLOCK"


def test_observation_driven_posterior_and_unknown_likelihood():
    probe = {"targeted_hypotheses": ["a", "b"], "prior_probabilities": {"a": .5, "b": .5}}
    update = observation_driven_posterior(probe, {"hypothesis_likelihoods": {"a": .9, "b": .1}, "supported_hypotheses": ["a"], "refuted_hypotheses": ["b"]})
    assert update["posterior"]["a"] > update["posterior"]["b"] and update["entropy_after"] < update["entropy_before"]
    unknown = observation_driven_posterior(probe, {})
    assert unknown["likelihoods"] == {"a": "NOT_ESTABLISHED", "b": "NOT_ESTABLISHED"}


def test_board_v4_synchronizes_closed_cells_and_prunes_constraints():
    def cell(cid, branch):
        raw = {"cell_id": cid, "branch_membership": branch, "state": "UNKNOWN", "semantic_state": "UNKNOWN"}
        from controllergate.core.evidence import hash_record
        return {**raw, "state_hash": hash_record(raw)}
    board = {"schema_version": "amds.board.v3", "candidate_id": "c", "branches": {"coverage": {"branch_id": "BUILD-CELL-COVERAGE", "branch_state": "CLOSED"}, "rpds-py": {"branch_id": "BUILD-CELL-RPDS_PY", "branch_state": "REMEDIATION_PENDING"}}, "cells": [cell("BUILD-CELL-COVERAGE", "coverage"), cell("BUILD-CELL-COVERAGE:missing_Cargo", "coverage"), cell("BUILD-CELL-RPDS_PY", "rpds-py"), cell("BUILD-CELL-RPDS_PY:missing_Cargo", "rpds-py"), cell("BUILD-CELL-RPDS_PY:missing_Rust_toolchain", "rpds-py"), cell("BUILD-CELL-RPDS_PY:wheel_tag_or_ABI_mismatch", "rpds-py")], "constraints": [{"constraint_id": "old", "constraint_type": "at_least_one", "members": ["BUILD-CELL-COVERAGE:missing_Cargo"]}]}
    from controllergate.core.evidence import hash_record
    board["board_hash"] = hash_record(board)
    migrated = migrate_board_v4(board, {"cargo": {"status": "PASS", "provider_manifest_hash": "a" * 64}, "builder": {"rust": {"status": "PASS"}}, "ninja": {"sha256": "b" * 64}})
    assert migrated["schema_version"] == "amds.board.v4"
    assert [c for c in migrated["cells"] if c["branch_membership"] == "coverage"][0]["state"] == "RESOLVED"
    assert all(c["constraint_id"] != "old" for c in migrated["constraints"])


def test_semantic_failure_signature_ignores_ansi_and_timing_noise():
    one = "\x1b[31mFAILED\x1b[0m tests/test_cli.py::test_mult[x] - AssertionError path_open.mock_calls\n0.21s setup"
    two = "FAILED tests/test_cli.py::test_mult[x] - AssertionError path_open.mock_calls\n0.97s setup"
    assert semantic_failure_signature(one, collect=False) == semantic_failure_signature(two, collect=False)
