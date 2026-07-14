from __future__ import annotations

import json
from pathlib import Path

import pytest

from controllergate.amds.dpp14.blind_runtime import run_blind_episode
from controllergate.pathways.canonical_maintenance import CANONICAL_PATHWAY, LICENSING_CONDITIONS, NATIVE_CONTACTS, generated_proof_matrix
from controllergate.state.integrity import canonical_hash
from controllergate.state.repository import ControllerStateRepository
from scripts.audit_installed_product_reachability import scan


def test_static_graph_blocks_direct_external_operation_and_current_graph_passes():
    assert scan()["status"] == "PASS"
    injected = "import subprocess\n"
    result = scan(injected_source=injected)
    assert result["status"] == "FAIL"
    assert result["unbrokered_external_operation_count"] >= 1


def test_sqlite_json_migration_is_one_way_and_idempotent(tmp_path: Path):
    source = tmp_path / "legacy.json"
    source.write_text(json.dumps({"run_id": "fixture-migration", "candidate_id": "fixture"}), encoding="utf-8")
    repository = ControllerStateRepository(tmp_path / "state.sqlite3")
    first = repository.migrate_json_state(source); second = repository.migrate_json_state(source)
    assert first["status"] == second["status"] == "PASS"
    assert first["source_hash"] == second["source_hash"]
    assert second["idempotent"] is True
    assert source.read_text(encoding="utf-8").startswith("{")


def test_worker_lease_rejects_competing_worker(tmp_path: Path):
    repository = ControllerStateRepository(tmp_path / "state.sqlite3")
    repository.create_run("lease-run", "candidate", {})
    assert repository.acquire_lease("lease-run", "worker-a", 60)
    assert not repository.acquire_lease("lease-run", "worker-b", 60)
    assert repository.release_lease("lease-run", "worker-a")


def test_pathway_and_matrix_are_generated_from_tokens():
    assert len(CANONICAL_PATHWAY) == len(NATIVE_CONTACTS) == 14
    assert len(LICENSING_CONDITIONS) == 6
    tokens = [{"token_type": stage.output_token_type, "token_hash": canonical_hash(stage.stage_id), "producer_event": stage.stage_id} for stage in CANONICAL_PATHWAY]
    contacts = {name: canonical_hash(name) for name in NATIVE_CONTACTS}
    matrix = generated_proof_matrix(candidate_id="candidate", run_id="run", tokens=tokens, contact_proofs=contacts)
    assert matrix["status"] == "PASS" and matrix["cell_count"] == 196
    assert {cell["status"] for cell in matrix["cells"]} == {"PASS_WITH_PROOF"}


def test_failed_or_wrong_run_tokens_cannot_grant_authority(tmp_path: Path):
    stage = CANONICAL_PATHWAY[1]
    from controllergate.reactions.token_kernel import ReactionToken
    wrong = ReactionToken.mint(token_type="CANDIDATE_IDENTITY_VERIFIED_TOKEN", candidate_id="other", run_id="run",
                               producer_event="candidate", input_tokens=(), payload={}, independent_verifier="verifier")
    anchors = {"anchor_hash": canonical_hash("anchors")}
    from controllergate.pathways.canonical_maintenance import execute_stage
    with pytest.raises(ValueError):
        execute_stage(stage, candidate_id="candidate", run_id="run", prior_tokens=[wrong], anchors=anchors,
                      direct_output={"status": "PASS", "verified": True, "anchor_hash": anchors["anchor_hash"]})


def test_blind_dpp_rejects_terminal_and_label_injection(tmp_path: Path):
    anchors = {"source_and_test_tree_identity": canonical_hash("tree")}
    leaked = {"candidate_id": "c", "run_id": "r", "anchors": anchors, "expected_terminal": "source_owned", "probes": []}
    assert run_blind_episode(leaked, tmp_path)["blocker"] == "decision_bundle_future_or_terminal_label_rejected"
    labeled = {"candidate_id": "c", "run_id": "r", "anchors": anchors,
               "probes": [{"probe_id": "p", "script": "print('source_contact=true')", "classification": "source_owned"}]}
    assert run_blind_episode(labeled, tmp_path)["blocker"] == "label_fed_probe_rejected"


def test_blind_dpp_raw_probe_is_brokered_and_deterministic(tmp_path: Path):
    anchors = {"source_and_test_tree_identity": canonical_hash("tree")}
    frame = {"candidate_id": "c", "run_id": "r", "anchors": anchors,
             "probes": [{"probe_id": "p", "script": "print('provider_failure=true')"}]}
    first = run_blind_episode(frame, tmp_path / "a"); second = run_blind_episode(frame, tmp_path / "b")
    assert first["terminal"] == second["terminal"] == "provider_owned"
    assert first["observations"][0]["broker_record_hash"]
    assert first["label_leakage_count"] == first["decision_time_truth_overlap"] == 0


def test_tld_registry_is_shadow_only_and_complete():
    root = Path(__file__).resolve().parents[1]
    records = [json.loads(line) for line in (root / "configs/notebooklm_tld_requirements_registry.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(records) == 44
    assert all(item["may_authorize"] is False for item in records)


def test_batch087_runner_uses_platform_temp_directory():
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts/run_batch087_canonical_execution_blind_dpp14_product_beta_revalidation.py").read_text(encoding="utf-8")
    assert "tempfile.gettempdir()" in source
    assert 'os.environ.get("TEMP", "C:/Temp")' not in source
