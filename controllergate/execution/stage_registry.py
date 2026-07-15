from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class StageDefinition:
    stage_id: str
    executor_identity: str
    verifier_identity: str
    required_tokens: tuple[str, ...]
    ordinary_inputs: tuple[str, ...]
    expected_raw_outputs: tuple[str, ...]
    semantic_output_schema: str
    allowed_mutation: str
    network_policy: str
    resource_budget: int
    failure_terminal: str
    rollback_target: str
    reopen_condition: str

    def record(self) -> dict[str, object]:
        value = asdict(self)
        for key in ("required_tokens", "ordinary_inputs", "expected_raw_outputs"):
            value[key] = list(value[key])
        return value


def _stage(stage_id: str, required: tuple[str, ...] = (), mutation: str = "none") -> StageDefinition:
    return StageDefinition(
        stage_id=stage_id,
        executor_identity=f"controllergate.engine._stage_output:{stage_id}",
        verifier_identity=f"controllergate.pathways.canonical_maintenance.verify:{stage_id}",
        required_tokens=required,
        ordinary_inputs=("run_manifest", "five_anchor_frame"),
        expected_raw_outputs=("stage_output",),
        semantic_output_schema="controllergate.stage-output.v2",
        allowed_mutation=mutation,
        network_policy="none",
        resource_budget=1,
        failure_terminal="SAFE_ABSTENTION",
        rollback_target="latest_committed_checkpoint",
        reopen_condition="new_decision_time_safe_direct_evidence",
    )


STAGE_REGISTRY = {row.stage_id: row for row in (
    _stage("candidate_identity"), _stage("source_acquisition", ("CANDIDATE_IDENTITY_VERIFIED_TOKEN",)),
    _stage("runtime_attestation", ("SOURCE_ACQUIRED_TOKEN",)),
    _stage("provider_execution", ("RUNTIME_ATTESTED_TOKEN",)),
    _stage("target_provenance", ("PROVIDER_EXECUTION_READY_TOKEN",)),
    _stage("command_authority", ("TARGET_OR_REPRODUCER_VERIFIED_TOKEN",)),
    _stage("duplicate_failure", ("COMMAND_AUTHORITY_VERIFIED_TOKEN",)),
    _stage("causal_ownership", ("DUPLICATE_FAILURE_REPRODUCED_TOKEN",)),
    _stage("ast_contact", ("CAUSAL_OWNERSHIP_TOKEN",)),
    _stage("repair_license", ("AST_CONTACT_DOMAIN_TOKEN",)),
    _stage("patch_application", ("REPAIR_LICENSE_TOKEN",), mutation="source_only_patch"),
    _stage("validation", ("PATCH_APPLIED_TOKEN",)),
    _stage("duplicate_clean_replay", ("VALIDATION_PASSED_TOKEN",)),
    _stage("proof_append", ("DUPLICATE_CLEAN_REPLAY_TOKEN",), mutation="proof_append"),
    _stage("plan_maturation"), _stage("brokered_read", ("PLAN_MATURED_TOKEN",)),
    _stage("exactly_once_transport", ("BROKERED_READ_TOKEN",)),
    _stage("contradiction_backtrack", ("TRANSPORT_COMMITTED_TOKEN",)),
    _stage("local_actuation", ("ALTERNATE_PROBE_TOKEN",), mutation="bounded_local_effect"),
    _stage("exact_rollback", ("LOCAL_ACTUATION_TOKEN",), mutation="local_rollback"),
    _stage("non_source_terminal", ("DUPLICATE_FAILURE_REPRODUCED_TOKEN",)),
    _stage("artifact_maturation", mutation="package_build"),
    _stage("canary_install", ("ARTIFACT_MATURED_TOKEN",), mutation="isolated_install"),
    _stage("canary_health", ("CANARY_INSTALLED_TOKEN",)),
    _stage("canary_rollback", ("CANARY_HEALTH_TOKEN",), mutation="exact_local_rollback"),
)}


def registered_stage(stage_id: str) -> StageDefinition:
    try:
        return STAGE_REGISTRY[stage_id]
    except KeyError as error:
        raise ValueError(f"unregistered stage: {stage_id}") from error
