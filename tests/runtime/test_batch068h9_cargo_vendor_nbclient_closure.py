from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from controllergate.runtime import cargo_provider as provider_module
from controllergate.runtime import cargo_provider_strategies as strategies
from controllergate.runtime import cargo_provider_verifier as verifier
from controllergate.runtime.cargo_vendor import build_vendor_tree
from controllergate.runtime.per_package_wheel_builder import build_one
import scripts.generate_batch068h9_cargo_vendor_nbclient_detour_closure as h9


H8_STDERR = """Updating crates.io index
warning: failed to save last-use data
unable to open database file: /cargo-cache/.global-cache
failed to create directory /cargo-cache/registry/cache/index.crates.io
Permission denied (os error 13)
"""


def test_exact_h8_permission_failure_precedes_transport_classification():
    assert strategies.classify_cargo_failure(H8_STDERR, 101) == "cargo_cache_not_writable"


@pytest.mark.parametrize("text", ["HTTP 500", "status code 503", "response 502"])
def test_http_server_classification_requires_structured_status(text: str):
    assert strategies.classify_cargo_failure(text, 1) == "cargo_http_server_error"


@pytest.mark.parametrize("text", ["downloaded 500 bytes", "crate 502", "version 503.0", "error 504"])
def test_loose_http_number_does_not_classify_as_server_error(text: str):
    assert strategies.classify_cargo_failure(text, 1) != "cargo_http_server_error"


def test_cache_writability_preflight_is_network_none_and_checks_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        return SimpleNamespace(returncode=0, stdout="cargo-cache-preflight-pass 65534 65534\n", stderr="")

    monkeypatch.setattr(strategies.subprocess, "run", fake_run)
    result = strategies.cargo_cache_writability_preflight(cache=tmp_path / "cargo", python_image="python:test")
    assert result["status"] == "PASS"
    assert "none" in seen["command"]
    assert all(result["checks"].values())


def test_failed_cache_then_verified_vendor_is_authoritative(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lock = tmp_path / "Cargo.lock"
    lock.write_text("version = 3\n", encoding="utf-8")
    vendor_root = tmp_path / "vendor"
    config = tmp_path / ".cargo" / "config.toml"
    config.parent.mkdir(); config.write_text('directory = "/opt/cargo-vendor"\n', encoding="utf-8")
    generated = {
        "status": "PASS", "vendor_hash": "a" * 64, "vendor_root": str(vendor_root),
        "config_path": str(config), "packages": [{"name": "x"}], "acquisitions": [],
    }
    monkeypatch.setattr(provider_module, "generate_direct_vendor", lambda **kwargs: generated)
    monkeypatch.setattr(provider_module, "verify_vendor_manifest", lambda value: {"status": "PASS", "package_count": 1, "file_count": 2})
    monkeypatch.setattr(provider_module, "run_offline_cargo_metadata", lambda **kwargs: {"status": "PASS", "executed": True})
    result = provider_module.resolve_cargo_provider(
        failed_cache_attempt={"status": "BLOCK", "blocker": "cargo_cache_not_writable"},
        lock_path=lock, source_root=tmp_path, manifest_relative="Cargo.toml",
        vendor_root=vendor_root, cutoff="2024-07-03T12:05:28Z", rust_image="rust:test",
        phase_id="test", policy={}, ledger_path=tmp_path / "events.jsonl",
    )
    assert result["status"] == "PASS"
    assert result["selected_method"] == "direct_lock_vendor"
    assert result["strategy_attempts"][0]["status"] == "BLOCK"
    assert result["offline_metadata_status"] == "PASS"


def test_verified_vendor_capsule_is_supported_after_direct_vendor_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lock = tmp_path / "Cargo.lock"; lock.write_text("version = 3\n", encoding="utf-8")
    root = tmp_path / "capsule"; root.mkdir(); config = tmp_path / "config.toml"; config.write_text("", encoding="utf-8")
    capsule = {"vendor_root": str(root), "config_path": str(config), "vendor_hash": "b" * 64, "cargo_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest()}
    monkeypatch.setattr(provider_module, "generate_direct_vendor", lambda **kwargs: {"status": "BLOCK", "blocker": "direct_vendor_unavailable"})
    monkeypatch.setattr(provider_module, "verify_vendor_manifest", lambda value: {"status": "PASS", "package_count": 2, "file_count": 3})
    monkeypatch.setattr(provider_module, "run_offline_cargo_metadata", lambda **kwargs: {"status": "PASS", "executed": True})
    result = provider_module.resolve_cargo_provider(
        failed_cache_attempt={"status": "BLOCK"}, lock_path=lock, source_root=tmp_path,
        manifest_relative="Cargo.toml", vendor_root=tmp_path / "vendor", cutoff="2024-07-03T12:05:28Z",
        rust_image="rust:test", phase_id="test", policy={}, ledger_path=tmp_path / "events.jsonl",
        verified_vendor_capsule=capsule,
    )
    assert result["status"] == "PASS"
    assert result["selected_method"] == "verified_vendor_capsule"


def test_incomplete_cache_pass_does_not_bypass_provider_closure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lock = tmp_path / "Cargo.lock"; lock.write_text("version = 3\n", encoding="utf-8")
    monkeypatch.setattr(provider_module, "generate_direct_vendor", lambda **kwargs: {"status": "BLOCK", "blocker": "direct_vendor_unavailable"})
    result = provider_module.resolve_cargo_provider(
        failed_cache_attempt={"status": "PASS", "provider_file_count": 0}, lock_path=lock,
        source_root=tmp_path, manifest_relative="Cargo.toml", vendor_root=tmp_path / "vendor",
        cutoff="2024-07-03T12:05:28Z", rust_image="rust:test", phase_id="test",
        policy={}, ledger_path=tmp_path / "events.jsonl",
    )
    assert result["status"] == "BLOCK"
    assert result["strategy_attempts"][0]["blocker"] == "cargo_fetch_cache_closure_incomplete"


def test_vendor_config_uses_container_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lock = tmp_path / "Cargo.lock"
    lock.write_text("version = 3\n", encoding="utf-8")
    result = build_vendor_tree(
        lock_path=lock, vendor_root=tmp_path / "vendor", cutoff="2024-07-03T12:05:28Z",
        phase_id="test", policy={}, ledger_path=tmp_path / "events.jsonl",
    )
    assert result["status"] == "PASS"
    assert '/opt/cargo-vendor' in Path(result["config_path"]).read_text(encoding="utf-8")
    assert str(tmp_path) not in Path(result["config_path"]).read_text(encoding="utf-8")


def test_vendor_manifest_verifier_detects_byte_drift(tmp_path: Path):
    root = tmp_path / "vendor"; root.mkdir(); payload = root / "file"; payload.write_bytes(b"one")
    row = {"path": "file", "sha256": hashlib.sha256(b"one").hexdigest(), "size": 3}
    provider = {
        "vendor_root": str(root), "vendor_manifest": [row],
        "vendor_hash": hashlib.sha256(json.dumps([row], sort_keys=True).encode()).hexdigest(),
        "packages": [{"name": "x"}],
        "acquisitions": [{"checksum": "c", "crate_sha256": "c", "vendor": {"status": "PASS"}}],
    }
    assert verifier.verify_vendor_manifest(provider)["status"] == "PASS"
    payload.write_bytes(b"two")
    assert verifier.verify_vendor_manifest(provider)["status"] == "BLOCK"


def test_offline_metadata_is_an_executed_network_none_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "src"; source.mkdir(); vendor = tmp_path / "vendor"; vendor.mkdir()
    config = tmp_path / "config.toml"; config.write_text("", encoding="utf-8")
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(verifier.subprocess, "run", fake_run)
    result = verifier.run_offline_cargo_metadata(
        rust_image="rust:test", source_root=source, manifest_relative="Cargo.toml",
        vendor_root=vendor, cargo_config=config,
    )
    assert result["status"] == "PASS" and result["executed"] is True
    command = " ".join(seen["command"])
    assert "--network none" in command
    assert "metadata --locked --offline" in command


def test_wheel_builder_consumes_vendor_config_with_network_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    artifact_store = tmp_path / "artifacts"; artifact_store.mkdir(); artifact = artifact_store / "demo.tar.gz"; artifact.write_bytes(b"x")

    def fake_run(command, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="expected test stop")

    monkeypatch.setattr("controllergate.runtime.per_package_wheel_builder.subprocess.run", fake_run)
    result = build_one(package="demo", version="1", artifact=artifact, artifact_store=artifact_store, output_dir=tmp_path / "built", image_digest="builder:test")
    command = " ".join(result["command"])
    assert "--network none" in command
    assert "/opt/cargo-config.toml" in command
    assert "CARGO_NET_OFFLINE=true" in command


def test_nbclient_mock_mismatch_retires_without_source_patch(monkeypatch: pytest.MonkeyPatch):
    run = {
        "status": "PASS", "semantic_signature_hash": "a" * 64,
        "semantic_failure_signature": {"mock_call_mismatch": True, "failed_node_ids": ["test_mult", "test_output"]},
        "stdout": "AssertionError path_open.mock_calls", "stderr": "",
    }
    monkeypatch.setattr(h9, "_run_pytest_arm", lambda *args, **kwargs: dict(run))
    result = h9.ownership({})
    assert result["classification"] == "interpreter_mock_behavior_change"
    assert result["source_repair_admissible"] is False


def test_final_claims_preserve_counts_and_route_to_batch070(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(h9, "OUT", tmp_path)
    h9.finalize({
        "status": "PASS", "blocker": None,
        "provider": {"status": "PASS", "selected_method": "direct_lock_vendor"},
        "recovery": {"status": "PASS"},
        "ownership": {"classification": "interpreter_mock_behavior_change", "source_repair_admissible": False},
        "detour": {"retired_from_source_only_repair_queue": True, "duplicate_clean_replay": "NOT_RUN", "count_gate": "NOT_RUN"},
    })
    final = json.loads((tmp_path / "batch068h9_final_decision.json").read_text(encoding="utf-8"))
    assert final["issue_derived_repair_count"] == 4
    assert final["native_external_repair_count"] == 4
    assert final["next_major_action"] == "batch070"
    assert final["validated_protocol"] == "v2.18"
