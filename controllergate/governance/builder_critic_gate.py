from __future__ import annotations

from typing import Any


REQUIRED_COORDINATES = ("artifact_identity", "outer_manifest", "internal_manifest", "execution_ledger", "decision_report", "independent_audit", "claim_boundary", "workflow_head", "checked_out_head", "runner_source_hashes")


def builder_critic_agreement(builder: dict[str, Any], critic: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED_COORDINATES if key not in builder or key not in critic]
    disagreements = [key for key in REQUIRED_COORDINATES if key not in missing and builder[key] != critic[key]]
    if missing:
        status = "BUILDER_OUTPUT_PENDING_CRITIC_VERIFICATION"
    elif disagreements:
        status = "CRITIC_VERIFICATION_DISAGREES_BUILDER_OUTPUT"
    else:
        status = "PASS"
    return {"status": status, "missing": missing, "disagreements": disagreements}
