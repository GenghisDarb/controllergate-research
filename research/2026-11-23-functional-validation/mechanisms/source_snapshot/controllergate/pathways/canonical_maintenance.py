from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from controllergate.reactions.token_kernel import ReactionToken, require_tokens
from controllergate.state.integrity import canonical_hash


REFERENCE_ANCHORS = (
    "candidate_incident_identity",
    "source_and_test_tree_identity",
    "provider_runtime_abi_identity",
    "target_and_command_authority",
    "proof_claim_release_parent",
)

NATIVE_CONTACTS = (
    "candidate_identity", "incident_snapshot", "source_revision", "source_test_immutability",
    "runtime_attestation", "provider_closure", "command_authority", "target_reproducer_provenance",
    "runner_origin", "harness_origin", "duplicate_failure_reproduction", "normal_incident_divergence",
    "causal_ownership_ast_contact", "rollback_proof_count_path",
)

LICENSING_CONDITIONS = (
    "single_causal_family_after_executed_probes",
    "non_source_alternatives_excluded",
    "ast_source_contact_localized",
    "source_only_bounded_test_immutable",
    "validation_and_duplicate_replay_executable",
    "rollback_proof_nonduplication_claim_ready",
)

STAGES = (
    ("candidate_identity", "CANDIDATE_IDENTITY_VERIFIED_TOKEN", ()),
    ("source_acquisition", "SOURCE_ACQUIRED_TOKEN", ("CANDIDATE_IDENTITY_VERIFIED_TOKEN",)),
    ("runtime_attestation", "RUNTIME_ATTESTED_TOKEN", ("SOURCE_ACQUIRED_TOKEN",)),
    ("provider_execution", "PROVIDER_EXECUTION_READY_TOKEN", ("RUNTIME_ATTESTED_TOKEN",)),
    ("target_provenance", "TARGET_OR_REPRODUCER_VERIFIED_TOKEN", ("PROVIDER_EXECUTION_READY_TOKEN",)),
    ("command_authority", "COMMAND_AUTHORITY_VERIFIED_TOKEN", ("TARGET_OR_REPRODUCER_VERIFIED_TOKEN",)),
    ("duplicate_failure", "DUPLICATE_FAILURE_REPRODUCED_TOKEN", ("COMMAND_AUTHORITY_VERIFIED_TOKEN",)),
    ("causal_ownership", "CAUSAL_OWNERSHIP_TOKEN", ("DUPLICATE_FAILURE_REPRODUCED_TOKEN",)),
    ("ast_contact", "AST_CONTACT_DOMAIN_TOKEN", ("CAUSAL_OWNERSHIP_TOKEN",)),
    ("repair_license", "REPAIR_LICENSE_TOKEN", ("AST_CONTACT_DOMAIN_TOKEN",)),
    ("patch_application", "PATCH_APPLIED_TOKEN", ("REPAIR_LICENSE_TOKEN",)),
    ("validation", "VALIDATION_PASSED_TOKEN", ("PATCH_APPLIED_TOKEN",)),
    ("duplicate_clean_replay", "DUPLICATE_CLEAN_REPLAY_TOKEN", ("VALIDATION_PASSED_TOKEN",)),
    ("proof_append", "PROOF_APPENDED_TOKEN", ("DUPLICATE_CLEAN_REPLAY_TOKEN",)),
)


@dataclass(frozen=True)
class PathwayStage:
    stage_id: str
    output_token_type: str
    required_input_token_types: tuple[str, ...]
    reaction_type: str = "verified_maintenance_transition"
    catalyst_identity: str = "controllergate.pathways.canonical_maintenance.execute_stage"
    source_compartment: str = "sealed_candidate_workspace"
    destination_compartment: str = "sealed_candidate_workspace"
    network_mode: str = "none"
    allowed_mutation_scope: str = "none_unless_patch_stage_authorized"
    independent_verifier: str = "controllergate.pathways.canonical_maintenance.verify_stage"
    failure_terminal: str = "SAFE_ABSTENTION"
    reopen_condition: str = "new_decision_time_safe_direct_evidence"
    rollback_target: str = "five_anchor_checkpoint"

    def record(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "ordinary_inputs": [],
            "positive_regulators": ["verified_same_run_input_tokens", "five_anchor_identity_stable"],
            "negative_regulators": ["forbidden_evidence", "identity_drift", "unbrokered_external_operation"],
            "expected_outputs": [self.output_token_type],
            "forbidden_outputs": ["manual_pass_authority", "cross_candidate_token"],
            "proof_obligations": list(NATIVE_CONTACTS),
        }


CANONICAL_PATHWAY = tuple(PathwayStage(stage, token, tuple(required)) for stage, token, required in STAGES)

MECHANISM_REHEARSAL_PATHWAY = (
    PathwayStage("plan_maturation", "PLAN_MATURED_TOKEN", ()),
    PathwayStage("brokered_read", "BROKERED_READ_TOKEN", ("PLAN_MATURED_TOKEN",)),
    PathwayStage("exactly_once_transport", "TRANSPORT_COMMITTED_TOKEN", ("BROKERED_READ_TOKEN",)),
    PathwayStage("contradiction_backtrack", "ALTERNATE_PROBE_TOKEN", ("TRANSPORT_COMMITTED_TOKEN",)),
    PathwayStage("local_actuation", "LOCAL_ACTUATION_TOKEN", ("ALTERNATE_PROBE_TOKEN",)),
    PathwayStage("exact_rollback", "EXACT_ROLLBACK_TOKEN", ("LOCAL_ACTUATION_TOKEN",)),
)
HISTORICAL_NON_SOURCE_PATHWAY = CANONICAL_PATHWAY[:7] + (
    PathwayStage("non_source_terminal", "NON_SOURCE_TERMINAL_TOKEN", ("DUPLICATE_FAILURE_REPRODUCED_TOKEN",)),
)
CANARY_PATHWAY = (
    PathwayStage("artifact_maturation", "ARTIFACT_MATURED_TOKEN", ()),
    PathwayStage("canary_install", "CANARY_INSTALLED_TOKEN", ("ARTIFACT_MATURED_TOKEN",)),
    PathwayStage("canary_health", "CANARY_HEALTH_TOKEN", ("CANARY_INSTALLED_TOKEN",)),
    PathwayStage("canary_rollback", "CANARY_ROLLBACK_TOKEN", ("CANARY_HEALTH_TOKEN",)),
)
ROLLBACK_PATHWAY = (PathwayStage("exact_rollback", "EXACT_ROLLBACK_TOKEN", ()),)


def pathway_for_mode(mode: str, requested: list[str] | None = None) -> tuple[PathwayStage, ...]:
    pathways = {
        "historical_repair": CANONICAL_PATHWAY,
        "mechanism_rehearsal": MECHANISM_REHEARSAL_PATHWAY,
        "historical_non_source": HISTORICAL_NON_SOURCE_PATHWAY,
        "canary": CANARY_PATHWAY,
        "rollback": ROLLBACK_PATHWAY,
    }
    if mode not in pathways:
        raise ValueError(f"unregistered execution mode: {mode}")
    pathway = pathways[mode]
    if not requested:
        return pathway
    by_id = {stage.stage_id: stage for stage in pathway}
    if any(stage_id not in by_id for stage_id in requested):
        raise ValueError("requested stage is not registered for mode")
    selected = tuple(by_id[stage_id] for stage_id in requested)
    available: set[str] = set()
    for stage in selected:
        if not set(stage.required_input_token_types).issubset(available):
            raise ValueError("requested stages violate token dependency order")
        available.add(stage.output_token_type)
    return selected


def freeze_anchors(frame: dict[str, Any]) -> dict[str, Any]:
    anchors = {name: frame.get(name) for name in REFERENCE_ANCHORS}
    missing = [name for name, value in anchors.items() if value in (None, "", {})]
    if missing:
        raise ValueError(f"five reference anchors incomplete: {','.join(missing)}")
    return {"anchors": anchors, "anchor_hash": canonical_hash(anchors), "status": "PASS"}


def execute_stage(stage: PathwayStage, *, candidate_id: str, run_id: str,
                  prior_tokens: list[ReactionToken], anchors: dict[str, Any],
                  direct_output: dict[str, Any], verifier: str | None = None) -> ReactionToken:
    require_tokens(prior_tokens, stage.required_input_token_types, candidate_id=candidate_id, run_id=run_id)
    if direct_output.get("status") != "PASS" or direct_output.get("verified") is not True:
        raise ValueError("failed or unverified stage cannot mint success token")
    if direct_output.get("anchor_hash") != anchors.get("anchor_hash"):
        raise ValueError("five-anchor identity drift")
    return ReactionToken.mint(
        token_type=stage.output_token_type,
        candidate_id=candidate_id,
        run_id=run_id,
        producer_event=stage.stage_id,
        input_tokens=prior_tokens,
        payload={"anchors": anchors, "output": direct_output},
        independent_verifier=verifier or stage.independent_verifier,
    )


def execute_simulation_stage(stage: PathwayStage, *, candidate_id: str, run_id: str,
                             source_event: dict[str, Any], mechanism_results: list[dict[str, Any]],
                             anchor_hash: str) -> dict[str, Any]:
    """Execute the canonical nonauthorizing stage producer for installed simulations."""
    if stage.stage_id != "plan_maturation":
        raise ValueError("simulation producer is limited to the registered plan_maturation stage")
    if not source_event.get("source_occurrence_identity"):
        raise ValueError("simulation source occurrence identity missing")
    if not mechanism_results or any(row.get("status") != "PASS" for row in mechanism_results):
        raise ValueError("simulation mechanism results are incomplete")
    raw = {
        "candidate_id": candidate_id,
        "run_id": run_id,
        "stage_id": stage.stage_id,
        "source_event_sha256": canonical_hash(source_event),
        "mechanism_result_sha256s": [canonical_hash(row) for row in mechanism_results],
        "anchor_hash": anchor_hash,
        "authority": "shadow_non_authorizing",
    }
    return {
        **raw,
        "status": "PASS",
        "producer_identity": "controllergate.pathways.canonical_maintenance.execute_simulation_stage",
        "producer_executed": True,
        "raw_output_hash": canonical_hash(raw),
    }


def verify_simulation_stage(stage: PathwayStage, execution: dict[str, Any], *,
                            source_event: dict[str, Any], mechanism_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Independently verify the installed simulation producer's raw output."""
    checks = {
        "registered_stage": stage.stage_id == "plan_maturation" == execution.get("stage_id"),
        "producer_executed": execution.get("producer_executed") is True,
        "source_event": execution.get("source_event_sha256") == canonical_hash(source_event),
        "mechanism_results": execution.get("mechanism_result_sha256s") == [canonical_hash(row) for row in mechanism_results],
        "nonauthorizing": execution.get("authority") == "shadow_non_authorizing",
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "verified": all(checks.values()),
        "checks": checks,
        "execution_raw_output_hash": execution.get("raw_output_hash"),
        "verifier_identity": "controllergate.pathways.canonical_maintenance.verify_simulation_stage",
        "verifier_executed": True,
    }


def generated_proof_matrix(*, candidate_id: str, run_id: str,
                           tokens: list[dict[str, Any]], contact_proofs: dict[str, str]) -> dict[str, Any]:
    rows = [stage.output_token_type for stage in CANONICAL_PATHWAY]
    cells: list[dict[str, Any]] = []
    by_type = {str(token["token_type"]): token for token in tokens}
    for row in rows:
        token = by_type.get(row)
        for contact in NATIVE_CONTACTS:
            proof = contact_proofs.get(contact)
            status = "PASS_WITH_PROOF" if token and proof else "BLOCK"
            cells.append({
                "candidate_id": candidate_id,
                "run_id": run_id,
                "row_token_type": row,
                "row_token_hash": token.get("token_hash") if token else None,
                "contact": contact,
                "contact_proof_hash": proof,
                "verifier_identity": "controllergate.pathways.canonical_maintenance.generated_proof_matrix",
                "parent_event_hash": token.get("producer_event") if token else None,
                "status": status,
                "reason": "database token and proof present" if status == "PASS_WITH_PROOF" else "required token or proof missing",
            })
    return {
        "status": "PASS" if all(cell["status"] == "PASS_WITH_PROOF" for cell in cells) else "BLOCK",
        "rows": len(rows), "columns": len(NATIVE_CONTACTS), "cell_count": len(cells), "cells": cells,
        "derived_from_database_and_proof_ledger": True,
    }
