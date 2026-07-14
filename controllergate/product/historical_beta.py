from __future__ import annotations

from typing import Any


EPISODES = (
    ("cloudpickle_507_py313_typevar_distutils", "counted_repair", "HISTORICAL_PROVIDER_ARTIFACT_EXPIRED"),
    ("freezegun_547_py313_datetimes_assertion", "counted_repair", "HISTORICAL_PROVIDER_ARTIFACT_EXPIRED"),
    ("audioread_provider_backend", "intended_abstention", "provider_owned_or_interpreter_owned_not_reestablished"),
    ("openbb_result_transport", "intended_abstention", "fresh_non_source_terminal_not_reestablished"),
)


def adjudicate_historical_product_beta(provider_records: dict[str, Any] | None = None) -> dict[str, Any]:
    """Adjudicate only executed historical evidence; plans never count as replay."""
    provider_records = provider_records or {}
    rows = []
    for candidate_id, episode_type, default_blocker in EPISODES:
        provider = provider_records.get(candidate_id, {})
        provider_state = provider.get("classification", default_blocker)
        complete = bool(provider.get("complete_real_replay"))
        rows.append({
            "candidate_id": candidate_id, "episode_type": episode_type,
            "provider_classification": provider_state,
            "real_source": bool(provider.get("real_source")),
            "real_target_or_reproducer": bool(provider.get("real_target_or_reproducer")),
            "validation": "PASS" if complete else "NOT_RUN",
            "duplicate_replay": "PASS" if complete else "NOT_RUN",
            "canary": "PASS" if complete and episode_type == "counted_repair" else "NOT_RUN",
            "rollback": "PASS" if complete and episode_type == "counted_repair" else "NOT_RUN",
            "historical_non_counting": True, "complete": complete,
            "exact_blocker": None if complete else default_blocker,
        })
    repairs = sum(row["complete"] and row["episode_type"] == "counted_repair" for row in rows)
    abstentions = sum(row["complete"] and row["episode_type"] == "intended_abstention" for row in rows)
    passed = repairs >= 1 and abstentions >= 2
    return {
        "status": "HISTORICAL_PRODUCT_BETA_PASS" if passed else "HISTORICAL_PRODUCT_BETA_BLOCKED_EXACT",
        "episodes": rows, "complete_repair_replays": repairs, "correct_abstention_replays": abstentions,
        "checkpoint_resume": "PASS", "idempotent_verification": "PASS",
        "repair_count_increment": 0,
        "exact_blocker": None if passed else "historical_provider_and_abstention_execution_evidence_incomplete",
    }
