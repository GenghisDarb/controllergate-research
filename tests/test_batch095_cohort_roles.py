from __future__ import annotations

import json
from pathlib import Path

from scripts.join_batch095_cohort_and_roles import ORDER, main


def lane(candidate_id: str, passing: bool = True) -> dict:
    digest = "a" * 64
    return {
        "candidate_id": candidate_id,
        "status": "PASS" if passing else "BLOCK",
        "exact_blockers": [] if passing else ["typed_incident_not_materialized"],
        "provider_recipe": {
            "recipe_hash": digest,
            "provider_identity": "provider-" + candidate_id,
            "abi_tags": ["cp311"],
            "platform_tags": ["linux_x86_64"],
            "project_target_command": ["python", "target"],
            "working_directory_policy": "source_root",
            "environment_allowlist": ["PATH"],
            "network_acquisition_policy": "none",
            "semantic_outcome_contract_id": "contract-" + candidate_id,
            "dependency_lock_identity": digest,
        },
        "provider_verification": {"status": "PASS"},
        "observed_provider": {"python": {"version": "3.11"}, "package_graph_hash": digest, "provider_install_return_code": 0},
        "source_capsule": {"repository": "https://example.invalid/repo", "observed_commit": "b" * 40, "object_type": "commit", "source_tree_hash": digest, "identity_record_hash": digest},
        "source_test_immutability": {"status": "PASS", "source_tree_before": digest, "source_tree_after": digest, "test_tree_before": digest, "test_tree_after": digest, "source_mutated": False, "tests_mutated": False},
        "process": {"record_hash": digest, "stdout_sha256": digest, "stderr_sha256": digest, "return_code": 1},
        "product": {"producer_operation_hash": digest},
        "controls": {"positive": {"status": "PASS"}, "negative": {"status": "PASS"}},
        "typed_incident_verification": {"status": "PASS" if passing else "BLOCK", "outcome_family": "NONZERO_FAILURE", "raw_evidence_hash": digest},
        "service_lifecycle": {"status": "PASS"} if "openbb" in candidate_id else None,
        "cleanup": {"status": "PASS", "workspace_removed": True, "orphan_process": False},
        "patch_operation_count": 0,
        "count_increment": 0,
    }


def write_lanes(root: Path, *, blocked: str | None = None) -> None:
    for candidate_id in ORDER:
        target = root / candidate_id
        target.mkdir(parents=True)
        (target / "candidate_lane_result.json").write_text(json.dumps(lane(candidate_id, candidate_id != blocked)), encoding="utf-8")


def test_eight_pass_lanes_produce_80_executed_and_verified_roles(tmp_path: Path, monkeypatch) -> None:
    inputs = tmp_path / "inputs"; output = tmp_path / "output"
    write_lanes(inputs)
    monkeypatch.setattr("sys.argv", ["join", "--inputs-root", str(inputs), "--output", str(output)])
    assert main() == 0
    gate = json.loads((output / "historical_eight_episode_materialization_gate.json").read_text())
    roles = json.loads((output / "role_measurement_quality_gate_v3.json").read_text())
    assert gate["status"] == "EIGHT_EPISODE_SEMANTIC_MATERIALIZATION_PASS"
    assert roles["status"] == "EIGHT_EPISODE_TEN_ROLE_BOUNDARY_PASS"
    assert roles["execution_receipt_count"] == roles["verification_receipt_count"] == 80


def test_blocked_lane_stops_before_role_receipt_generation(tmp_path: Path, monkeypatch) -> None:
    inputs = tmp_path / "inputs"; output = tmp_path / "output"
    write_lanes(inputs, blocked=ORDER[0])
    monkeypatch.setattr("sys.argv", ["join", "--inputs-root", str(inputs), "--output", str(output)])
    assert main() == 0
    roles = json.loads((output / "role_measurement_quality_gate_v3.json").read_text())
    assert roles["status"] == "NOT_RUN"
    assert not (output / "role_measurement_execution_receipts_v3.jsonl").exists()
    assert not (output / "role_measurement_verification_receipts_v3.jsonl").exists()
