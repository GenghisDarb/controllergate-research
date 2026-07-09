from __future__ import annotations

from dataclasses import dataclass

REQUIRED_STEP_FIELDS = {
    "required_inputs",
    "allowed_inputs",
    "forbidden_inputs",
    "expected_outputs",
    "output_verifiers",
    "blocker_codes",
    "terminal_states",
    "reopen_conditions",
}

DEFAULT_CANDIDATE_STEPS = [
    "source_acquisition_step",
    "harness_origin_step",
    "workspace_purity_step",
    "provider_materialization_step",
    "command_translation_step",
    "pre_repair_replay_step",
    "diagnostic_replay_step",
    "source_topology_step",
    "patch_license_step",
    "patch_gate_step",
    "post_repair_replay_step",
    "duplicate_replay_step",
    "count_gate_step",
    "proof_ledger_step",
    "public_summary_step",
    "terminal_state_step",
]


@dataclass(frozen=True)
class ContractValidationResult:
    status: str
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "errors": list(self.errors)}


def default_step_record(step: str) -> dict[str, object]:
    return {
        "required_inputs": ["candidate_id", "decision_time_evidence"],
        "allowed_inputs": ["hash_pinned_metadata", "verified_runtime_record"],
        "forbidden_inputs": ["fixed_commit", "gold_patch", "future_commit", "unverified_prompt_text"],
        "expected_outputs": [f"{step}_record"],
        "output_verifiers": [f"verify_{step}_record"],
        "blocker_codes": [f"{step}_blocked"],
        "terminal_states": ["manual_review", "unrecoverable_under_current_policy"],
        "reopen_conditions": ["new_decision_time_safe_evidence"],
    }


def build_default_contract() -> dict[str, object]:
    blockers = sorted({f"{step}_blocked" for step in DEFAULT_CANDIDATE_STEPS})
    return {
        "schema_version": "batch067.step_contracts.v1",
        "known_steps": DEFAULT_CANDIDATE_STEPS,
        "known_blocker_codes": blockers,
        "steps": {step: default_step_record(step) for step in DEFAULT_CANDIDATE_STEPS},
    }


def validate_step_contract(contract: dict[str, object]) -> ContractValidationResult:
    errors: list[str] = []
    known_steps = set(contract.get("known_steps") or DEFAULT_CANDIDATE_STEPS)
    known_blockers = set(contract.get("known_blocker_codes") or [])
    steps = contract.get("steps")
    if not isinstance(steps, dict):
        return ContractValidationResult("FAIL", ("steps_missing_or_not_object",))
    unknown_steps = sorted(set(steps) - known_steps)
    if unknown_steps:
        errors.append(f"unknown_steps:{','.join(unknown_steps)}")
    missing_steps = sorted(set(DEFAULT_CANDIDATE_STEPS) - set(steps))
    if missing_steps:
        errors.append(f"missing_steps:{','.join(missing_steps)}")
    for step, record in steps.items():
        if not isinstance(record, dict):
            errors.append(f"{step}:record_not_object")
            continue
        missing = sorted(REQUIRED_STEP_FIELDS - set(record))
        if missing:
            errors.append(f"{step}:missing_fields:{','.join(missing)}")
        expected_outputs = record.get("expected_outputs")
        verifiers = record.get("output_verifiers")
        if not expected_outputs:
            errors.append(f"{step}:expected_outputs_empty")
        if not verifiers:
            errors.append(f"{step}:output_verifiers_empty")
        blockers = record.get("blocker_codes") or []
        for blocker in blockers:
            if known_blockers and blocker not in known_blockers:
                errors.append(f"{step}:unknown_blocker:{blocker}")
    return ContractValidationResult("PASS" if not errors else "FAIL", tuple(errors))
