from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import zipfile

from controllergate.core.artifacts import audit_zip_entries
from controllergate.core.patch_safety_v2 import build_patch_manifest_v2, normalize_patch_path, validate_patch_manifest_v2
from controllergate.core.step_runtime import (
    PRODUCTION_HANDLERS, PRODUCTION_VERIFIERS, StepInput, execute_semantic_graph,
    resolve_production_registry,
)
from controllergate.engine import FrontierEngine
from controllergate.runtime.probe_authorization import build_probe_authorization, verify_probe_authorization

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe"
PRIOR = ROOT / "outputs/post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening"


def load(path: Path): return json.loads(path.read_text(encoding="utf-8"))


def nbclient_raw():
    index = load(PRIOR / "candidate_state_index_batch068g.json")
    item = next(row for row in index["records"] if row["candidate_id"] == "codex_wave3_jupyter_nbclient_issues_316")
    return load(ROOT / item["state_path"])


def specs(): return load(OUT / "semantic_step_contract_v2_batch068h.json")["steps"]


def test_all_semantic_handlers_and_verifiers_resolve() -> None:
    assert len(PRODUCTION_HANDLERS) == len(PRODUCTION_VERIFIERS) == 11
    assert resolve_production_registry(specs())["status"] == "PASS"


def test_production_registry_contains_no_generic_fixtures() -> None:
    assert "passthrough_handler" not in PRODUCTION_HANDLERS
    assert "nonempty_output_verifier" not in PRODUCTION_VERIFIERS


def test_independent_verifier_rejects_handler_false_pass() -> None:
    raw = nbclient_raw(); spec = specs()[0]
    inp = StepInput(spec["step_id"], raw["candidate_id"], raw, {}, "GENESIS")
    output = PRODUCTION_HANDLERS[spec["handler"]](inp)
    forged = replace(output, facts={**output.facts, "identity_valid": False})
    assert PRODUCTION_VERIFIERS[spec["verifier"]](inp, forged).status == "FAIL"


def test_wrong_candidate_binding_blocks() -> None:
    raw = nbclient_raw(); spec = specs()[0]
    inp = StepInput(spec["step_id"], "wrong_candidate", raw, {}, "GENESIS")
    output = PRODUCTION_HANDLERS[spec["handler"]](inp)
    assert output.gate_decision == "BLOCK"


def test_manual_review_stops_downstream() -> None:
    index = load(PRIOR / "candidate_state_index_batch068g.json")
    item = next(row for row in index["records"] if load(ROOT / row["state_path"]).get("exact_blocker") == "command_source_conflict_manual_review")
    raw = load(ROOT / item["state_path"])
    result = execute_semantic_graph(raw["candidate_id"], raw, {}, specs())
    at = next(i for i, row in enumerate(result) if row["gate_decision"] == "MANUAL_REVIEW")
    assert all(row["gate_decision"] == "NOT_RUN" and row["candidate_state"] == "not_run_upstream_manual_review" for row in result[at + 1:])


def test_block_stops_downstream_and_preserves_chain() -> None:
    raw = nbclient_raw(); raw["target_path_verification"] = {"status": "BLOCK", "paths": [], "blocker": "missing_target"}
    result = execute_semantic_graph(raw["candidate_id"], raw, {}, specs())
    at = next(i for i, row in enumerate(result) if row["gate_decision"] == "BLOCK")
    assert all(row["gate_decision"] == "NOT_RUN" for row in result[at + 1:])
    assert all(result[i]["prior_state_hash"] == result[i - 1]["post_state_hash"] for i in range(1, len(result)))


def test_pass_steps_have_hashes_and_evidence() -> None:
    raw = nbclient_raw(); result = execute_semantic_graph(raw["candidate_id"], raw, {}, specs())
    assert all(row["input_hashes"] and row["decision_time_evidence_consumed"] for row in result if row["gate_decision"] == "PASS")


def test_forbidden_evidence_is_derived() -> None:
    raw = nbclient_raw(); raw["future_commit"] = True
    result = execute_semantic_graph(raw["candidate_id"], raw, {}, specs())
    assert result[0]["gate_decision"] == "BLOCK"
    assert "future_commit" in result[0]["forbidden_evidence_findings"]


def test_status_semantics_and_command_counts_are_unambiguous() -> None:
    status = load(OUT / "status_semantics_migration_batch068h.json")
    counts = load(OUT / "command_resolution_counts_batch068h.json")
    assert status["new_aggregate_logic_uses_legacy_status"] is False
    assert counts["command_selection_unresolved_count"] == 18
    assert counts["authoritative_command_conflict_count"] == 18
    assert counts["terminal_command_conflict_count"] == 4


def test_nested_archive_and_cache_fail_artifact_audit(tmp_path: Path) -> None:
    for name in ["inner.zip", "__pycache__/x.pyc", "payload.so"]:
        path = tmp_path / (name.replace("/", "_") + ".zip")
        with zipfile.ZipFile(path, "w") as archive: archive.writestr(name, b"x")
        assert audit_zip_entries(path)["status"] == "FAIL"


def test_patch_manifest_v2_normalizes_and_blocks_risks() -> None:
    assert normalize_patch_path("src\\module.py") == "src/module.py"
    assert normalize_patch_path("../escape.py") is None
    safe = validate_patch_manifest_v2(build_patch_manifest_v2("src/module.py", "+value = 1\n"))
    risky = validate_patch_manifest_v2(build_patch_manifest_v2("src/module.py", "+import subprocess\n+subprocess.run([], shell=True)\n"))
    assert safe["status"] == "PASS"
    assert risky["status"] == "BLOCK"


def test_patch_manifest_blocks_tests_dependencies_symlinks_modes_and_binary() -> None:
    assert validate_patch_manifest_v2(build_patch_manifest_v2("tests/test_x.py", "+assert True\n"))["status"] == "BLOCK"
    assert validate_patch_manifest_v2(build_patch_manifest_v2("requirements.txt", "+x==1\n"))["status"] == "BLOCK"
    assert validate_patch_manifest_v2(build_patch_manifest_v2("src/x.py", "+x=1\n", symlink_status="introduced"))["status"] == "BLOCK"
    assert validate_patch_manifest_v2(build_patch_manifest_v2("src/x.py", "+x=1\n", old_mode="644", new_mode="755"))["status"] == "BLOCK"
    assert validate_patch_manifest_v2(build_patch_manifest_v2("src/x.py", "+x=1\n", binary_status="binary"))["status"] == "BLOCK"


def test_prospective_memory_and_retention_schemas() -> None:
    memory = load(ROOT / "configs/controllergate_prospective_memory_validation_v1.json")
    retention = load(ROOT / "configs/controllergate_evidence_retention_policy.json")
    assert memory["minimum_fresh_incidents"] == 100
    assert memory["minimum_unrelated_repositories"] == 10
    assert memory["minimum_ecosystems_or_languages"] == 3
    assert "current_product_state" in retention["storage_classes"]


def test_v2_14_preserved_and_v2_15_promoted() -> None:
    assert (ROOT / "configs/controllergate_v2_14.yaml").is_file()
    assert (ROOT / "configs/controllergate_v2_15.yaml").is_file()
    decision = load(OUT / "static_planning_protocol_promotion_decision_batch068h.json")
    assert decision["status"] == "PASS"
    assert decision["protocol_after"] == "v2.15"


def test_frontier_current_status_and_plan() -> None:
    engine = FrontierEngine(ROOT)
    assert engine.validate()["status"] == "PASS"
    assert engine.status()["validated_current_protocol"].startswith(("v2.15", "v2.16", "v2.17", "v2.18", "v2.19"))
    assert engine.plan("codex_wave3_jupyter_nbclient_issues_316")["status"] == "PASS"


def test_authorization_bound_probe_and_rejection() -> None:
    state = load(OUT / "candidate_states/codex_wave3_jupyter_nbclient_issues_316.json")
    auth = build_probe_authorization(candidate_id=state["candidate_id"], candidate_sha=state["candidate_sha"], candidate_state_hash=state["state_hash"], source_identity=state["repo_identity"], command_argv=["python", "-m", "pytest", "--collect-only", "tests/test_cli.py"], target_path="tests/test_cli.py", provider_policy_hash="a" * 64, container_policy_hash="b" * 64, allowed_graph_steps=["collection"], patch_authority=False, scope="one_run")
    assert verify_probe_authorization(auth, state)["status"] == "PASS"
    auth["candidate_sha"] = "0" * 40
    assert verify_probe_authorization(auth, state)["status"] == "BLOCK"


def test_no_patch_or_test_execution_claims() -> None:
    final = load(OUT / "batch068h_final_decision.json")
    assert final["patch_generated"] is False
    assert final["patch_applied"] is False
    assert final["target_tests_executed"] == 0
    assert final["test_bodies_executed"] == 0
