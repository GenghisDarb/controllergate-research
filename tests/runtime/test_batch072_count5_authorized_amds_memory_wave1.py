from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from controllergate.core.batch072_count5_amds_wave1 import BATCH, PATCH_SHA256, metamorphic_checks
from controllergate.core.evidence import hash_record, sha256_file
from controllergate.runtime.candidate_execution_authorization import CandidateExecutionAuthorization, seal_candidate_authorization, verify_candidate_authorization
from controllergate.runtime.candidate_execution_plan import CandidateExecutionPlan, CandidatePhase, seal_candidate_plan, verify_candidate_plan
from controllergate.runtime.evidence_ownership import classify_failure_from_evidence
from controllergate.runtime.generic_patch_plan import execute_patch_plan
from controllergate.runtime.maintenance_dispatcher import dispatch_candidate_manifest

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / BATCH


def test_manifest_cannot_self_authorize(tmp_path: Path) -> None:
    manifest = {"candidate_id": "c", "candidate_sha": "a" * 40}
    result = dispatch_candidate_manifest(manifest=manifest, checkpoint_path=tmp_path / "checkpoint.json", event_ledger_path=tmp_path / "events.jsonl", authorization_store=tmp_path / "nonces.json")
    assert result == {"status": "BLOCK", "blocker": "execution_authorization_manifest_required"}


def test_candidate_plan_phase_and_test_mutation_guards(tmp_path: Path) -> None:
    plan = CandidateExecutionPlan("p", "c", "a" * 40, "b" * 64, str(tmp_path), (CandidatePhase("source", "x", network_mode="bounded_read_only"), CandidatePhase("replay", "y", ("source",))), str(tmp_path / "context.json"))
    sealed = seal_candidate_plan(plan)
    assert verify_candidate_plan(sealed, allowed_output_root=tmp_path)["status"] == "PASS"
    sealed["phases"][1]["test_mutation_allowed"] = True
    sealed["plan_hash"] = hash_record({key: value for key, value in sealed.items() if key != "plan_hash"})
    assert verify_candidate_plan(sealed, allowed_output_root=tmp_path)["blocker"] == "candidate_execution_plan_test_mutation_forbidden"


def test_authorization_enforces_network_budgets_and_nonce(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc)
    auth = CandidateExecutionAuthorization("a", "c", "a" * 40, "b" * 64, "c" * 64, ("source",), ("source",), {"source": ("github.com",)}, {"source": 2}, {"source": 1000}, {"source": False, "tests": False}, {"seconds": 10}, str(tmp_path), now.isoformat(), (now + timedelta(minutes=5)).isoformat(), "nonce")
    sealed = seal_candidate_authorization(auth)
    kwargs = dict(candidate_id="c", candidate_sha="a" * 40, current_state_hash="b" * 64, plan_hash="c" * 64, output_root=tmp_path)
    assert verify_candidate_authorization(sealed, spent_nonces=set(), **kwargs)["status"] == "PASS"
    assert verify_candidate_authorization(sealed, spent_nonces={"nonce"}, **kwargs)["blocker"] == "candidate_execution_authorization_nonce_spent"


def test_generic_patch_plan_executes_only_hashed_source_file(tmp_path: Path) -> None:
    source = tmp_path / "pkg.py"; source.write_text("value = 1\n", encoding="utf-8")
    plan = {"candidate_id": "c", "candidate_sha": "a" * 40, "operations": [{"operation": "replace_text", "path": "pkg.py", "precondition_sha256": sha256_file(source), "before": "1", "after": "2"}]}
    plan["plan_hash"] = hash_record(plan)
    result = execute_patch_plan(plan, source_root=tmp_path, candidate_id="c", candidate_sha="a" * 40)
    assert result["status"] == "PASS" and source.read_text() == "value = 2\n"


def test_generic_ownership_classifier_abstains_without_topology(tmp_path: Path) -> None:
    result = classify_failure_from_evidence(failure_log="AssertionError", source_root=tmp_path, target_path="tests/test_x.py", candidate_package_roots=["pkg"])
    assert result["classification"] == "insufficient_evidence"
    assert result["candidate_specific_rule_used"] is False


def test_count_five_patch_identity_and_metamorphic_invariants() -> None:
    identity = json.loads((OUT / "batch071_patch_identity_preservation.json").read_text(encoding="utf-8"))
    assert identity["sha256"] == PATCH_SHA256
    assert metamorphic_checks()["status"] == "PASS"


def test_wave1_is_frozen_partial_and_claim_bounded() -> None:
    cohort = json.loads((OUT / "batch072_fresh_candidate_cohort.json").read_text(encoding="utf-8"))
    decisions = json.loads((OUT / "batch072_completion_decisions.json").read_text(encoding="utf-8"))
    assert cohort["frozen_before_outcomes"] and cohort["status"] == "PARTIAL"
    assert decisions["AMDS_PROSPECTIVE_EFFECTIVENESS"] == "NOT_ESTABLISHED"
    assert decisions["MEMORY_LIFT"] == "not_demonstrated"
    assert decisions["SELF_MAINTAINING_SOFTWARE"] == "false/not_demonstrated"
