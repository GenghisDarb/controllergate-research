from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping


ALIASES = {
    "source_owned", "provider_owned", "environment_owned", "platform_owned", "runner_owned", "harness_owned",
    "transport_owned", "expectation_owned", "mixed_failure", "safe_abstention", "insufficient_evidence",
    "gold_terminal", "sourceownership", "providerownership",
}
PROVENANCE_KEYS = {"candidate_id", "project_id", "repository", "repo_url", "source_commit"}


def _tokens(value: str) -> set[str]:
    return {token.lower() for token in re.split(r"[^A-Za-z0-9_]+", value) if token}


def lint_probe(probe: Mapping[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    def visit(value: Any, path: str, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                child_path = f"{path}.{child_key}" if path else str(child_key)
                if child_key not in PROVENANCE_KEYS and _tokens(str(child_key)).intersection(ALIASES):
                    findings.append({"path": child_path, "reason": "causal_family_encoded_in_output_key"})
                visit(child, child_path, str(child_key))
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]", key)
        elif isinstance(value, str) and key not in PROVENANCE_KEYS:
            if _tokens(value).intersection(ALIASES):
                findings.append({"path": path, "reason": "causal_family_or_terminal_alias_encoded_in_probe"})

    visit(probe, "")
    return {"status": "REJECTED" if findings else "PASS", "findings": findings, "rejection_count": len(findings), "linter": "ProbeNeutralityLinterV1"}


def reproducibility_conflict(first: Mapping[str, Any], second: Mapping[str, Any], *, environment_parity: bool, observer_state_parity: bool) -> dict[str, Any]:
    ignored = {"observation_id", "started_at", "ended_at", "operation_id", "parent_broker_record"}
    left = {key: value for key, value in first.items() if key not in ignored}
    right = {key: value for key, value in second.items() if key not in ignored}
    different = left != right
    if different:
        conflict_id = "probe-reproducibility:" + hashlib.sha256(json.dumps([left, right], sort_keys=True, default=str).encode()).hexdigest()
        return {"status": "PROBE_REPRODUCIBILITY_CONFLICT", "conflict_id": conflict_id, "first_observation": first.get("observation_id"), "second_observation": second.get("observation_id"), "environment_parity": environment_parity, "observer_state_parity": observer_state_parity, "next_action": "compile_reproducibility_probe_or_safe_abstention", "terminal_selected": False}
    return {"status": "PASS", "conflict_id": None, "terminal_selected": False}


def source_counterfactual_allowed(record: Mapping[str, Any]) -> bool:
    required = ("frozen_before_target", "decision_time_safe", "independently_custodied", "candidate_contract_permitted", "nonauthorizing")
    return all(record.get(key) is True for key in required) and not any(record.get(key) for key in ("future_fixed_revision", "gold_patch", "post_repair_source"))
