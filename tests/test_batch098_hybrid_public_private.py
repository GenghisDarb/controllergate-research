from __future__ import annotations

import json
import sys
from pathlib import Path

from controllergate.amds.opaque_plan_v1 import compile_opaque_plans, verify_opaque_plans
from controllergate.amds.stage_runtime_v7 import run_dpp14
from controllergate.evidence.provider_parity import load_provider_contracts, public_provider_negative_controls, verify_provider_observation
from controllergate.evidence.public_artifact_v1 import private_marker_hits
from controllergate.evidence.roles_v2 import produce_roles, role_quality_gate, verify_role_receipts
from controllergate.topology.pre_tld_frame_v1 import canonical_hash, verify_pre_tld_frame
from scripts.batch098_workflow_stage import incident_verify
from scripts.audit_batch098_public_topology_layer import audit_layer
from scripts.run_batch098_public_truth_blind import ARM_COMPONENTS, BASELINE_COMPONENTS, components_for_arm


ROOT = Path(__file__).resolve().parents[1]


def provider_contracts() -> list[dict]:
    return load_provider_contracts(ROOT / "configs" / "frozen_provider_environment_contracts_v1.jsonl")


def frame(candidate: str = "candidate") -> dict:
    probe = {
        "probe_id": f"probe:{candidate}", "candidate_id": candidate, "run_id": "run", "frame_id": "frame",
        "source_cell_or_edge_or_region": "cell", "exact_argv": ["{python}", "-c", "import json;print(json.dumps({'kind':'boundary_dimension','subject':'cell','subject_hash':'x','diagnosis_label_present':False}))"],
        "installed_operation_id": "controllergate evidence execute-probe", "cwd_compartment": "EXECUTION_WORKSPACE", "environment_delta": {},
        "counterfactual_pair_id": None, "predicted_neutral_partitions": {"yes": ["h1"], "no": ["h2"]},
        "semantic_verifier_id": "structured-schema-v1", "required_raw_outputs": ["process_observation"], "budgets": {"timeout_seconds": 30},
        "timeout_seconds": 30, "single_use_nonce": canonical_hash([candidate, "nonce"])[:32], "controls": {}, "forbidden_outputs": ["terminal_class"],
        "reopen_condition": "execute", "probe_kind": "boundary_dimension",
        "structured_result_schema": {"type": "object", "required": ["kind", "subject", "subject_hash", "diagnosis_label_present"]},
        "partition_rule": {"rule_id": "boundary-v1", "positive_when": "present", "negative_when": "absent"},
    }
    value = {
        "schema": "PreTLDDecisionFrameV1", "candidate_id": candidate, "run_id": "run", "frame_id": "frame", "candidate_contract_hash": "a" * 64,
        "board_identity": "b" * 64, "board_cells": [], "board_edges": [], "causal_regions": [], "boundary_cells": [], "environment_exhausted_handoff": None,
        "projection_pairs": [], "modalities": {}, "hypotheses": [], "constraints": [], "legal_probes": [probe], "budgets": {"timeout_seconds": 30},
        "observer_state": "ACTIVE_PROVISIONAL", "observer_identity": "c" * 64, "provisional_branch_identity": "d" * 64,
        "tld_join_state": "PENDING_PRIVATE_DIRECT_SOURCE_JOIN", "private_tld_source_access_count": 0, "truth_access_count": 0,
        "authority_allowed": "private TLD continuation input", "authority_forbidden": ["final frame freeze", "terminal", "source ownership", "repair", "count", "release"],
        "producer": "controllergate.topology.pre_tld_frame_v1.build_pre_tld_frame", "execution_depth": "verified_topology_and_decision_time_evidence",
        "semantic_scope": "public truth-blind pre-TLD continuation frame",
    }
    value["pre_tld_frame_hash"] = canonical_hash(value)
    return value


def test_exact_provider_contracts_and_negative_controls() -> None:
    rows = provider_contracts()
    assert len(rows) == 8
    assert {row["provider_exact_version"] for row in rows} == {"3.7.17", "3.11.15", "3.13.14"}
    assert all(row["provider_os_family"] == "linux" and row["provider_architecture"] == "x86_64" for row in rows)
    poetry = next(row for row in rows if row["candidate_id"] == "incident_poetry_10974_init_duplicate_name")
    assert poetry["provider_platform_tag"] == "linux-x86_64"
    assert all(control["status"] == "PASS" for row in rows for control in public_provider_negative_controls(row))


def test_wrong_microrelease_and_windows_never_pass() -> None:
    contract = provider_contracts()[0]
    observation = {
        "implementation": "cpython", "python_version": "3.13.0", "cache_tag": contract["provider_cache_tag"],
        "soabi": contract["provider_soabi_pattern"], "platform_tag": "win-amd64", "os_family": "windows", "architecture": "amd64",
        "abi_tag": contract["provider_abi_tag"], "runner_image": "windows-2025", "runner_image_version": "2025",
        "libc_identity": "none", "kernel_identity": "windows", "source_commit": contract["source_commit"],
        "dependency_graph_hash": contract["dependency_graph_hash"], "runner_identity": contract["runner_identity"],
        "harness_identity": contract["harness_identity"], "command_identity": contract["command_identity"],
    }
    assert verify_provider_observation(contract, observation)["status"] == "BLOCK"


def test_pre_tld_frame_is_not_final_authority() -> None:
    value = frame()
    assert verify_pre_tld_frame(value)["status"] == "PASS"
    value["final_complete_frame_hash"] = "e" * 64
    value["pre_tld_frame_hash"] = canonical_hash({key: item for key, item in value.items() if key != "pre_tld_frame_hash"})
    assert verify_pre_tld_frame(value)["status"] == "BLOCK"


def test_opaque_plans_cover_only_legal_probes() -> None:
    frames = [frame(f"candidate-{index}") for index in range(8)]
    plans = compile_opaque_plans(frames, bundle_sha256="a" * 64, requirement_registry_sha256="b" * 64, created_at_utc="2026-07-18T00:00:00Z")
    assert verify_opaque_plans(plans, frames)["status"] == "PASS"
    assert len(plans) == 80
    text = json.dumps(plans).casefold()
    assert "notebook heading" not in text
    assert "c:\\" not in text


def test_planned_probe_order_executes_through_canonical_dpp14() -> None:
    value = frame()
    terminal, produced, verified = run_dpp14({
        "candidate_id": value["candidate_id"], "run_id": value["run_id"], "frame_id": value["frame_id"],
        "topology_probes": value["legal_probes"], "topology_constraints": [], "planned_probe_order": [value["legal_probes"][0]["probe_id"]],
    })
    assert terminal["terminal_writer"] == "controllergate.amds.stage_runtime_v7.ControllerAudit"
    assert len(produced) == len(verified) == 14
    assert all(row["status"] == "PASS" for row in verified)


def test_workflows_and_local_boundary_are_explicit() -> None:
    decision = (ROOT / ".github/workflows/controllergate_batch098_public_decision_time_evidence.yml").read_text(encoding="utf-8")
    truth_blind = (ROOT / ".github/workflows/controllergate_batch098_public_truth_blind_execution.yml").read_text(encoding="utf-8")
    local = (ROOT / "scripts/run_batch098_with_local_tld_sources.ps1").read_text(encoding="utf-8")
    assert "incident_poetry_10974_init_duplicate_name, provider_python: \"3.11.15\"" in decision
    assert "runs-on: ubuntu-22.04" in decision
    assert "CG_RUNTIME: ${{ runner.temp }}" not in decision + truth_blind
    assert "$CG_RUNTIME" not in decision + truth_blind
    assert "$RUNNER_TEMP/controllergate-runtime" in decision + truth_blind
    assert "build_batch098_candidate_contracts.py" in decision
    assert "--output \"$RUNNER_TEMP/controllergate-runtime/contracts/candidate_execution_contracts_v2.jsonl\"" in decision
    assert "cmp configs/frozen_provider_environment_contracts_v1.jsonl" in decision
    assert "public_decision_time_artifact_id" in truth_blind and "opaque_plan_commit_sha" in truth_blind
    assert "PublicDecisionEvidenceArtifactId" in local and "PublicTruthBlindExecutionArtifactId" in local
    assert "LOCAL_WINDOWS_DIAGNOSTIC_NONPARITY" in local
    assert "materialize-candidate" not in local


def test_independent_incident_verification_preserves_scientific_blocks(tmp_path: Path) -> None:
    for index in range(8):
        candidate = f"candidate-{index}"
        root = tmp_path / "cohort" / candidate
        root.mkdir(parents=True)
        incident = {
            "status": "PASS" if index == 0 else "BLOCK",
            "typed_incident_materialized": index == 0,
            "reasons": [] if index == 0 else ["target_behavior_absent"],
            "verification_receipt": canonical_hash([candidate, "incident"]),
            "structured_product_parents": [canonical_hash([candidate, "product"])],
        }
        (root / "typed_incident_verification.json").write_text(json.dumps(incident), encoding="utf-8")
        (root / "candidate_lane_result_v2.json").write_text(
            json.dumps({"candidate_id": candidate, "typed_incident": incident}), encoding="utf-8"
        )
    result = incident_verify(tmp_path / "cohort", tmp_path / "verified")
    assert result == {
        "status": "PASS_VERIFICATION_EXECUTED",
        "count": 8,
        "materialized_count": 1,
        "scientific_block_count": 7,
        "authority_forbidden": ["incident PASS aggregation", "terminal", "repair", "count", "release"],
    }


def test_role_execution_preserves_unavailable_incident_role() -> None:
    digest = "a" * 64
    evidence = {
        "candidate_id": "candidate", "run_id": "run", "frame_id": "frame", "source_commit": digest,
        "contract_hash": digest, "source_manifest_hash_before": digest, "source_manifest_hash_after": digest,
        "test_manifest_hash_before": digest, "test_manifest_hash_after": digest,
        "neutral_observation": {
            "provider_identity": digest, "producer_installed_code_hash": digest, "probe_id": "probe",
            "stdout_sha256": digest, "stderr_sha256": digest, "parent_broker_record": digest,
            "argv": ["python"], "runner_identity": "runner", "harness_identity": "harness",
        },
        "typed_incident": {"status": "BLOCK", "verification_receipt": digest, "reasons": ["absent"]},
    }
    produced = produce_roles(evidence, preserve_blocked=True)
    verified = verify_role_receipts(produced)
    assert len(produced) == len(verified) == 10
    assert sum(row["status"] == "BLOCK" for row in produced) == 1
    assert sum(row["status"] == "BLOCK" for row in verified) == 1
    assert role_quality_gate(produced, verified, 1)["status"] == "BLOCK"


def test_projection_audit_preserves_no_executable_pair_as_scientific_block(tmp_path: Path) -> None:
    source = tmp_path / "verified"
    for index in range(8):
        root = source / f"candidate-{index}"
        root.mkdir(parents=True)
        (root / "topology_verification_summary.json").write_text(
            json.dumps({"candidate_id": f"candidate-{index}", "status": "PASS"}), encoding="utf-8"
        )
        rows = [] if index == 0 else [{"pair_id": f"pair-{index}", "status": "PASS"}]
        (root / "projection_pair_verification_receipts_v2.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )
    audit = audit_layer(source, tmp_path / "audit", "projection")
    assert audit["status"] == "PASS_EXECUTION_WITH_SCIENTIFIC_BLOCKS"
    assert audit["scientific_block_count"] == 1
    assert audit["rows"][0]["status"] == "SCIENTIFIC_BLOCK_NO_EXECUTABLE_PROJECTION_PAIR"


def test_public_scanner_allows_forbidden_field_metadata_but_blocks_patch_content(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"forbidden_fields": ["gold_patch"]}), encoding="utf-8")
    assert private_marker_hits([metadata]) == []
    leaked = tmp_path / "leaked.json"
    leaked.write_text(json.dumps({"payload": "gold_patch_content"}), encoding="utf-8")
    assert private_marker_hits([leaked]) == [{"path": leaked.as_posix(), "marker": "gold_patch_content"}]


def test_all_architecture_arms_and_baselines_have_explicit_components() -> None:
    assert set(ARM_COMPONENTS) == set("ABCDEF")
    assert set(BASELINE_COMPONENTS) == set("GHIJ")
    assert all(components_for_arm(arm_id) for arm_id in "ABCDEFGHIJ")
