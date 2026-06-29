from __future__ import annotations

import json
from pathlib import Path

from controllergate.core.clean_repair import matched_null_ensemble_score


BATCH005 = Path("outputs/clean_replication_batch_005")


def _read(path: Path):
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


def test_batch005_public_claim_boundaries_remain_closed():
    claim = _read(BATCH005 / "claim_boundary.json")

    assert claim["full_scoring"] == "NOT_RUN/disallowed"
    assert claim["memory_lift"] == "undemonstrated_equal_performance"
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
        "RNA " + "primase",
        "Meta" + "-cell",
        "Klein " + "twist",
        "meta" + "phorical",
    ]
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/replication_protocol.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("configs/clean_replication_batch_005.json"),
    ]
    hits = []
    for path in public_paths:
        text = path.read_text(encoding="utf-8")
        hits.extend(term for term in blocked_terms if term in text)

    assert hits == []
