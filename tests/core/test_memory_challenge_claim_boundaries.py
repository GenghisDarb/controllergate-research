from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.clean_repair import matched_null_ensemble_score, memory_routing_delta


BATCH004 = Path("outputs/clean_replication_batch_004")


def _read(path: Path) -> dict[str, object] | list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(status: str) -> dict[str, object]:
    return {
        "candidate_id": "candidate_x",
        "repo_url": "https://example.test/repo",
        "commit_sha": "a" * 40,
        "target_test_path": "tests/test_target.py",
        "target_validation_status": status,
        "duplicate_replay_status": status,
    }


def test_null_ensemble_success_rate_one_forces_score_zero():
    score = matched_null_ensemble_score(_run("PASS"), [_run("PASS") for _ in range(5)], {"routing_delta_active": True})

    assert score["null_ensemble_success_rate"] == 1.0
    assert score["matched_null_ensemble_separation_score"] == 0.0
    assert score["preliminary_single_candidate_memory_separation_evidence"] is False


def test_passive_memory_routing_forces_score_zero():
    score = matched_null_ensemble_score(
        _run("PASS"),
        [_run("FAIL") for _ in range(5)],
        memory_routing_delta({"relevant_markers": ["PINNED_EDGE"]}),
    )

    assert score["matched_null_ensemble_separation_score"] == 0.0
    assert score["preliminary_single_candidate_memory_separation_evidence"] is False


def test_issue_derived_repair_cannot_claim_native_memory_separation():
    claim = _read(BATCH004 / "claim_boundary.json")

    assert claim["preliminary_single_candidate_memory_separation_evidence"] is False
    assert claim["full_scoring"] == "NOT_RUN/disallowed"
    assert claim["self_maintaining_software"] == "false/not_demonstrated"
    assert claim["technical_validation_release_readiness"] == "not_ready"


def test_public_outputs_do_not_contain_blocked_internal_terms():
    blocked_terms = [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "Klein " + "twist",
        "bio" + "logical",
        "meta" + "phorical",
    ]
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/replication_protocol.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("configs/clean_replication_batch_004.json"),
    ]
    hits = []
    for path in public_paths:
        text = path.read_text(encoding="utf-8")
        hits.extend(term for term in blocked_terms if term in text)

    assert hits == []
