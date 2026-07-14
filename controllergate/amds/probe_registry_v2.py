from __future__ import annotations

from .hypothesis_space_v2 import HYPOTHESES
from .probe_contract_v2 import ProbeContractV2


CONTACTS = (
    "artifact_custody",
    "source_identity",
    "failure_signature",
    "target_reproducer",
    "command_authority",
    "provider_closure",
    "runtime_platform",
    "harness_origin",
    "workspace_boundary",
    "source_topology",
    "rollback_proof_readiness",
    "alternative_cause_elimination",
)


def default_registry() -> list[ProbeContractV2]:
    return [
        ProbeContractV2(
            probe_id=f"probe-{index:02d}-{contact}",
            evidence_contact=contact,
            required_inputs=(f"{contact}_evidence",),
            possible_observation_classes=(f"{contact}_verified", f"{contact}_blocked"),
            hypotheses_distinguished=HYPOTHESES,
            expected_information_value=None,
            execution_cost=float(1 + index % 3),
            manual_review_cost=float(index % 2),
            security_risk=0.0 if contact not in {"provider_closure", "runtime_platform"} else 1.0,
            provider_rebuild_requirement=contact == "provider_closure",
            platform_requirement=None,
            authorization_requirement="decision_time_evidence_only",
            direct_evidence_produced=(f"{contact}_observation",),
            forbidden_evidence=("fixed_source", "future_commit", "gold_patch", "outcome_label"),
            stop_conditions=("direct_terminal_evidence", "alternatives_excluded", "safe_abstention", "budget_exhausted"),
        )
        for index, contact in enumerate(CONTACTS, 1)
    ]
