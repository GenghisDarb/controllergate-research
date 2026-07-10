from __future__ import annotations

import hashlib
import json
from pathlib import Path

from controllergate.runtime.collection_decomposition import classify_raw_failure, phase_plan
from controllergate.runtime.log_custody import normalize_output, record_completed_command, secret_scan

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"


def load(name: str): return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_lossless_raw_log_custody_and_hashes(tmp_path: Path) -> None:
    stdout = "alpha\r\nbeta\n"; stderr = "error\n"
    record = record_completed_command(tmp_path, "probe_run0", argv=["python", "-V"], cwd="/source", env={}, container_identity="c", image_digest="image@sha256:" + "a"*64, timeout_seconds=3, returncode=2, stdout=stdout, stderr=stderr, started_at="s", stopped_at="e")
    combined = stdout + "\n" + stderr
    assert (tmp_path / "probe_run0_combined.txt").read_bytes() == combined.encode()
    assert record["hashes"]["raw_combined_sha256"] == hashlib.sha256(combined.encode()).hexdigest()


def test_secret_scan_blocks_packaging(tmp_path: Path) -> None:
    token = "ghp_" + "A"*30
    record = record_completed_command(tmp_path, "probe_run1", argv=["x"], cwd="/", env={}, container_identity=None, image_digest=None, timeout_seconds=1, returncode=1, stdout=token, stderr="", started_at="s", stopped_at="e")
    assert record["secret_scan"]["status"] == "BLOCK"
    assert (tmp_path / "probe_run1_stdout.txt").read_text() == "REDACTED_SECRET_DETECTED"


def test_output_normalization_scrubs_paths() -> None:
    assert "<WORKSPACE>" in normalize_output("/home/runner/work/repo/repo/file.py")


def test_failure_classification_is_evidence_based() -> None:
    assert classify_raw_failure("ModuleNotFoundError: no module named x") == "provider_import_failure"
    assert classify_raw_failure("opaque failure") == "unclassified_collection_failure"


def test_phase_plan_is_ordered_and_collection_only() -> None:
    plan = phase_plan()
    assert [item["phase"] for item in plan] == list(range(9))
    assert all(item["test_bodies_allowed"] is False for item in plan)


def test_tmpfs_runtime_environment_policy() -> None:
    manifest = load("runtime_environment_variable_manifest_batch068h1.json")
    assert manifest["all_writable_paths_tmpfs_bound"] is True
    assert manifest["environment"]["PYTHONDONTWRITEBYTECODE"] == "1"


def test_first_failure_stops_later_phases_when_executed() -> None:
    results = load("collection_phase_results_batch068h1.json")["results"]
    blocked = next((i for i, item in enumerate(results) if item.get("operation_status") == "COMPLETED" and item.get("gate_decision") == "BLOCK"), None)
    if blocked is not None:
        assert all(item["operation_status"] == "NOT_RUN" for item in results[blocked+1:])


def test_zero_test_body_execution() -> None:
    final = load("batch068h1_final_decision.json")
    assert final["test_bodies_executed"] == final["target_tests_executed"] == 0
