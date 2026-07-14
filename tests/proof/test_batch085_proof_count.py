from __future__ import annotations

from controllergate.proof.count_service import decide_count, public_counts
from controllergate.proof.service import REQUIRED_REPAIR_PROOFS, append_proof
from controllergate.state.repository import ControllerStateRepository


def test_count_is_proof_derived_duplicate_safe_and_historical_noncounting(tmp_path):
    repo = ControllerStateRepository(tmp_path / "state.db")
    repo.create_run("run", "candidate", {})
    last = None
    for kind in sorted(REQUIRED_REPAIR_PROOFS):
        last = append_proof(repo.connection, run_id="run", candidate_id="candidate", proof_type=kind, payload={"status": "PASS"})
    assert decide_count(repo.connection, candidate_id="candidate", repair_class="issue_derived", proof_hash=last)["decision"] == "COUNT"
    assert decide_count(repo.connection, candidate_id="candidate", repair_class="issue_derived", proof_hash=last)["blocker"] == "duplicate_count_rejected"
    assert public_counts(repo.connection) == {"issue_derived": 7, "native_external": 4}
    assert decide_count(repo.connection, candidate_id="historical", repair_class="native_external", proof_hash="unused", historical_non_counting=True)["decision"] == "NON_COUNTING_HISTORICAL"
