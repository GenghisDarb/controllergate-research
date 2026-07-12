from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from controllergate.core.batch073_count5_frozen_wave1 import BATCH, CANDIDATE_ID, CANDIDATE_SHA, H72, PATCH_SHA
from controllergate.core.evidence import hash_record, sha256_file
from controllergate.runtime.candidate_execution_authorization import CandidateExecutionAuthorization, seal_candidate_authorization, verify_candidate_authorization
from controllergate.runtime.candidate_execution_plan import CandidateExecutionPlan, CandidatePhase, seal_candidate_plan, verify_candidate_plan
from controllergate.runtime.count_gate import existing_count_hardening_gate, new_repair_count_gate, terminal_proof_event
from controllergate.runtime.live_authorized_maintenance import build_amds_board_from_evidence, recompute_dependency_lock_evidence, recompute_target_ast_evidence
from controllergate.runtime.network_authorization import authorize_network_operation

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / BATCH


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_h72_reconciliation_preserves_fixed_lead_frame_without_replenishment() -> None:
    reconciliation = load("batch072_lead_frame_vs_cohort_reconciliation.json")
    frozen = [json.loads(line)["candidate_id"] for line in (ROOT / "outputs" / H72 / "batch072_weak_lead_registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert reconciliation["lead_ids_in_order"] == frozen
    assert reconciliation["H72_admitted_cohort_status"] == "NOT_YET_DERIVED"
    assert reconciliation["commit_resolution_attempts_completed_in_H72"] == 0
    assert reconciliation["replacement_or_replenishment"] is False


def test_all_twenty_leads_receive_terminal_dispositions_after_issue_screening() -> None:
    dispositions = rows("batch073_lead_execution_registry.jsonl")
    issues = {item["candidate_id"]: item for item in rows("batch073_issue_contamination_registry.jsonl")}
    assert len(dispositions) == 20
    assert [item["position"] for item in dispositions] == list(range(20))
    assert all(item["status"] == "REJECT" and item["terminal_blocker"] and not item["replacement_used"] for item in dispositions)
    screened = [item for item in dispositions if item["terminal_blocker"] not in {"prior_controllergate_outcome_or_count_excluded", "issue_identity_missing"}]
    assert screened and all(issues[item["candidate_id"]]["body_read"] and issues[item["candidate_id"]]["comments_read"] for item in screened)


def test_independent_commit_resolution_is_reachable_and_before_cutoff() -> None:
    resolved = [item for item in rows("batch073_commit_resolution_registry.jsonl") if item["status"] == "PASS"]
    assert resolved
    assert all(item["reported_sha_trusted"] is False and item["reachable_by_fetch"] and item["commit_object"] == "commit" for item in resolved)
    assert all(datetime.fromisoformat(item["commit_timestamp"].replace("Z", "+00:00")) <= datetime.fromisoformat(item["cutoff"].replace("Z", "+00:00")) for item in resolved)


def test_executed_empty_cohort_has_complete_blocker_counts_and_no_arms() -> None:
    cohort = load("batch073_admitted_cohort.json")
    arms = load("batch073_prospective_arm_execution.json")
    assert cohort["status"] == "EXECUTED_EMPTY_COHORT" and cohort["candidate_count"] == 0
    assert sum(cohort["terminal_blocker_counts"].values()) == 20
    assert arms["status"] == "NOT_RUN_EXECUTED_EMPTY_COHORT"
    assert arms["candidate_arms_executed"] == arms["probe_executions"] == arms["posterior_updates"] == 0


def test_cutoff_wheelhouse_and_two_capsules_are_identity_locked() -> None:
    provider = load("connexion_cutoff_provider_verification.json")
    wheelhouse = load("connexion_hardened_wheelhouse_manifest.json")
    capsules = load("connexion_two_capsule_registry_batch073.json")
    assert provider["status"] == "PASS" and provider["package_count"] == 63 and provider["post_cutoff_selected_artifact_count"] == 0
    assert len(wheelhouse["artifacts"]) == 63 and all(len(item["sha256"]) == 64 for item in wheelhouse["artifacts"])
    assert capsules["same_provider_store"] and len(capsules["capsules"]) == 4
    assert all(item["provider_lock_hash"] == wheelhouse["provider_lock_hash"] and item["source_sha"] == CANDIDATE_SHA and item["network"] == "none" and item["import_origins_verified"] for item in capsules["capsules"])


def test_existing_count_hardening_does_not_recount_and_rejects_tampering() -> None:
    record = {"candidate_id": CANDIDATE_ID, "candidate_sha": CANDIDATE_SHA, "patch_sha256": PATCH_SHA}
    passed = existing_count_hardening_gate(record=record, registry=[record], prerequisites={"duplicate": True})
    assert passed["status"] == "PASS" and passed["count_increment"] == 0
    assert existing_count_hardening_gate(record=record, registry=[record, record], prerequisites={"duplicate": True})["status"] == "BLOCK"
    assert existing_count_hardening_gate(record={**record, "patch_sha256": "0" * 64}, registry=[record], prerequisites={"duplicate": True})["status"] == "BLOCK"


def test_new_count_uniqueness_and_terminal_proof_are_mandatory() -> None:
    record = {"candidate_id": CANDIDATE_ID, "candidate_sha": CANDIDATE_SHA, "patch_sha256": PATCH_SHA}
    assert new_repair_count_gate(record=record, registry=[record], prerequisites={"duplicate": True})["status"] == "BLOCK"
    decision = new_repair_count_gate(record={**record, "candidate_id": "new"}, registry=[record], prerequisites={"duplicate": True})
    assert decision["status"] == "PASS" and decision["count_increment"] == 1
    event = terminal_proof_event(prior_event_hash="a" * 64, decision=decision)
    unsigned = dict(event); supplied = unsigned.pop("event_hash")
    assert supplied == hash_record(unsigned) and event["decision_hash"] == hash_record(decision)


def test_authorization_expiry_nonce_output_and_test_mutation_guards(tmp_path: Path) -> None:
    phases = (CandidatePhase("source", "acquire_source", network_mode="bounded_read_only"),)
    plan = seal_candidate_plan(CandidateExecutionPlan("p", "c", "a" * 40, "b" * 64, str(tmp_path), phases, str(tmp_path / "context.json")))
    now = datetime.now(timezone.utc)
    auth = CandidateExecutionAuthorization("a", "c", "a" * 40, "b" * 64, plan["plan_hash"], ("source",), ("source",), {"source": ("github.com",)}, {"source": 1}, {"source": 100}, {"source": False, "tests": False}, {"seconds": 10}, str(tmp_path), now.isoformat(), (now + timedelta(minutes=1)).isoformat(), "nonce")
    sealed = seal_candidate_authorization(auth)
    kwargs = dict(candidate_id="c", candidate_sha="a" * 40, current_state_hash="b" * 64, plan_hash=plan["plan_hash"], output_root=tmp_path)
    assert verify_candidate_authorization(sealed, spent_nonces=set(), **kwargs)["status"] == "PASS"
    assert verify_candidate_authorization(sealed, spent_nonces={"nonce"}, **kwargs)["blocker"] == "candidate_execution_authorization_nonce_spent"
    outside = dict(plan); outside["output_root"] = str(tmp_path.parent / "outside"); outside["plan_hash"] = hash_record({key: value for key, value in outside.items() if key != "plan_hash"})
    assert verify_candidate_plan(outside, allowed_output_root=tmp_path)["blocker"] == "candidate_execution_output_root_outside_authority"
    mutated = dict(plan); mutated["phases"] = [dict(plan["phases"][0])]; mutated["phases"][0]["test_mutation_allowed"] = True; mutated["plan_hash"] = hash_record({key: value for key, value in mutated.items() if key != "plan_hash"})
    assert verify_candidate_plan(mutated, allowed_output_root=tmp_path)["blocker"] == "candidate_execution_plan_test_mutation_forbidden"


def test_network_allowlist_request_and_byte_budgets() -> None:
    policy = {"phase_id": "source", "network_mode": "bounded_read_only", "allowed_network_destinations": ["github.com"], "allowed_protocols": ["https"], "maximum_requests": 1, "maximum_download_bytes": 10, "tls_verification_policy": "required", "redirect_policy": "allowlisted_hosts_only"}
    assert authorize_network_operation(phase_id="source", policy=policy, destination="https://github.com/x", requested_mode="bounded_read_only", projected_requests=1, projected_bytes=10)["status"] == "PASS"
    assert authorize_network_operation(phase_id="source", policy=policy, destination="https://example.com/x", requested_mode="bounded_read_only")["blocker"] == "network_destination_not_allowlisted"
    assert authorize_network_operation(phase_id="source", policy=policy, destination="https://github.com/x", requested_mode="bounded_read_only", projected_requests=2)["blocker"] == "network_request_budget_exceeded"
    assert authorize_network_operation(phase_id="source", policy=policy, destination="https://github.com/x", requested_mode="bounded_read_only", projected_bytes=11)["blocker"] == "network_byte_budget_exceeded"


def test_live_contacts_require_real_rollback_and_proof_records() -> None:
    manifest = {"candidate_id": "c", "candidate_sha": "a" * 40, "execution_mode": "live", "artifact_custody": {"status": "PASS"}, "activation_gates": {}}
    context = {"candidate_manifest": manifest, "candidate_identity": {"status": "PASS"}, "source_acquisition": {"head": "a" * 40, "outside_live_repo": True}, "prerepair_replay": {"failure_signature_hash": "b" * 64}, "harness_origin": {"status": "PASS"}, "command_authority": {"status": "PASS"}, "runner_target_origin": {"status": "PASS"}, "provider_closure": {"status": "PASS"}, "environment": {"status": "PASS"}, "failure_topology": {"status": "PASS"}}
    blocked = build_amds_board_from_evidence(context)["context_updates"]
    assert blocked["live_contact_resolution"]["rollback_and_proof_path"] is False
    assert all(len(item["evidence_record_hash"]) == 64 for item in blocked["live_contact_evidence"].values())
    context.update({"rollback": {"status": "PASS"}, "proof_ledger_update": {"status": "PASS"}})
    passed = build_amds_board_from_evidence(context)["context_updates"]
    assert passed["live_contact_resolution"]["rollback_and_proof_path"] is True


def test_ast_and_provider_semantic_evidence_is_recomputed(tmp_path: Path) -> None:
    source = tmp_path / "source"; target = source / "tests" / "test_target.py"; target.parent.mkdir(parents=True)
    target.write_text("def test_target():\n    assert 1 == 2\n", encoding="utf-8")
    wheelhouse = tmp_path / "wheelhouse"; wheelhouse.mkdir(); wheel = wheelhouse / "demo.whl"; wheel.write_bytes(b"provider")
    context = {"source_root": str(source), "candidate_manifest": {"native_target_paths": ["tests/test_target.py::test_target"]}, "prerepair_replay": {"failure_signature_hash": "f" * 64}, "environment": {"wheelhouse": str(wheelhouse)}, "provider_closure": {"selected_artifacts": [{"filename": wheel.name, "sha256": sha256_file(wheel)}], "dependency_graph_hash": "d" * 64}}
    assert recompute_target_ast_evidence(context)["target_path"] == "tests/test_target.py"
    assert recompute_dependency_lock_evidence(context)["status"] == "PASS"
    wheel.write_bytes(b"tampered")
    assert recompute_dependency_lock_evidence(context)["status"] == "BLOCK"


def test_claim_boundaries_remain_conservative() -> None:
    final = load("batch073_final_decision.json")
    assert final["historical_issue_derived_repair_count"] == 5 and final["native_external_count"] == 4
    assert final["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert final["memory_lift"] == "not_demonstrated"
    assert final["full_scoring"] == "NOT_RUN/disallowed"
    assert final["self_maintaining_software"] == "false/not_demonstrated"
    assert final["live_connectors"] == "inactive"
