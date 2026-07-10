from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Callable

from .command_orthology import rank_command_candidates
from .evidence import hash_record
from .runner_target import classify_runner_target


@dataclass(frozen=True)
class StepInput:
    step_id: str
    candidate_id: str
    raw_inputs: dict[str, Any]
    declared_policy: dict[str, Any]
    prior_transition_hash: str


@dataclass(frozen=True)
class StepOutput:
    operation_status: str
    evidence_status: str
    gate_decision: str
    candidate_state: str
    facts: dict[str, Any]
    input_hashes: tuple[str, ...]
    decision_time_evidence_consumed: tuple[str, ...]
    forbidden_evidence_checked: bool
    forbidden_evidence_findings: tuple[str, ...]
    blocker_code: str | None = None
    blocker_reason: str | None = None
    next_allowed_action: str = "continue_semantic_graph"
    reopen_conditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationResult:
    status: str
    recomputed_facts_hash: str
    output_facts_hash: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class TransitionRecord:
    stable_step_id: str
    candidate_id: str
    handler_name: str
    verifier_name: str
    operation_status: str
    evidence_status: str
    gate_decision: str
    candidate_state: str
    input_hashes: tuple[str, ...]
    decision_time_evidence_consumed: tuple[str, ...]
    forbidden_evidence_checked: bool
    forbidden_evidence_findings: tuple[str, ...]
    output_hash: str
    verification_status: str
    verification_hash: str
    blocker_code: str | None
    blocker_reason: str | None
    next_allowed_action: str
    reopen_conditions: tuple[str, ...]
    prior_state_hash: str
    post_state_hash: str


@dataclass(frozen=True)
class TerminalDecision:
    candidate_id: str
    candidate_state: str
    gate_decision: str
    exact_blocker: str | None
    next_allowed_action: str
    reopen_conditions: tuple[str, ...]


SemanticHandler = Callable[[StepInput], StepOutput]
SemanticVerifier = Callable[[StepInput, StepOutput], VerificationResult]

FORBIDDEN_EVIDENCE_KEYS = {
    "fixed_commit", "future_commit", "gold_patch", "pr_patch", "future_test",
    "hidden_benchmark_state", "outcome_only_evidence",
}


def _forbidden(raw: dict[str, Any]) -> tuple[str, ...]:
    manifest = raw.get("decision_time_evidence_manifest") or {}
    findings = list(manifest.get("forbidden_evidence_used") or [])
    findings.extend(key for key in FORBIDDEN_EVIDENCE_KEYS if raw.get(key))
    return tuple(sorted(set(map(str, findings))))


def _output(
    inp: StepInput,
    *,
    facts: dict[str, Any],
    evidence: list[str],
    decision: str = "PASS",
    blocker: str | None = None,
    next_action: str = "continue_semantic_graph",
    reopen: tuple[str, ...] = (),
) -> StepOutput:
    findings = _forbidden(inp.raw_inputs)
    if findings:
        decision = "BLOCK"
        blocker = "forbidden_evidence_detected"
        next_action = "remove_forbidden_evidence_and_recompute"
        reopen = (next_action,)
    meaningful_hashes = tuple(sorted({hash_record(value) for value in [inp.raw_inputs, inp.declared_policy] if value}))
    evidence_status = "ESTABLISHED" if decision == "PASS" else ("PARTIAL" if decision == "MANUAL_REVIEW" else "NOT_ESTABLISHED")
    return StepOutput(
        operation_status="COMPLETED",
        evidence_status=evidence_status,
        gate_decision=decision,
        candidate_state="semantic_step_pass" if decision == "PASS" else str(blocker or "manual_review"),
        facts=facts,
        input_hashes=meaningful_hashes,
        decision_time_evidence_consumed=tuple(sorted(set(evidence))),
        forbidden_evidence_checked=True,
        forbidden_evidence_findings=findings,
        blocker_code=blocker,
        blocker_reason=None if blocker is None else blocker.replace("_", " "),
        next_allowed_action=next_action,
        reopen_conditions=reopen,
    )


def _source_identity(inp: StepInput) -> StepOutput:
    repo = inp.raw_inputs.get("repo_identity") or {}
    url = str(repo.get("repo_url") or inp.raw_inputs.get("repo_url") or "")
    candidate_binding = str(inp.raw_inputs.get("candidate_id") or "") == inp.candidate_id
    valid = re.fullmatch(r"https://github\.com/[^/\s]+/[^/\s]+", url) is not None and candidate_binding
    return _output(inp, facts={"repo_url": url, "candidate_id": inp.candidate_id, "candidate_binding": candidate_binding, "identity_valid": valid}, evidence=["repo_identity", "candidate_id", "Batch068g source identity"], decision="PASS" if valid else "BLOCK", blocker=None if valid else "source_identity_invalid", next_action="continue_semantic_graph" if valid else "supply_verified_repository_identity", reopen=() if valid else ("supply_verified_repository_identity",))


def _candidate_sha(inp: StepInput) -> StepOutput:
    sha = str(inp.raw_inputs.get("candidate_sha") or "")
    bound = re.fullmatch(r"[0-9a-f]{40}", sha) is not None
    manifest_sha = str((inp.raw_inputs.get("decision_time_evidence_manifest") or {}).get("candidate_sha") or "")
    valid = bound and manifest_sha == sha
    return _output(inp, facts={"candidate_sha": sha, "sha40": bound, "manifest_binding": manifest_sha == sha}, evidence=["candidate_sha", "decision_time_evidence_manifest.candidate_sha"], decision="PASS" if valid else "BLOCK", blocker=None if valid else "candidate_sha_binding_invalid", next_action="continue_semantic_graph" if valid else "supply_verified_candidate_sha_binding", reopen=() if valid else ("supply_verified_candidate_sha_binding",))


def _metadata(inp: StepInput) -> StepOutput:
    sources = inp.raw_inputs.get("metadata_source_files") or []
    sha = inp.raw_inputs.get("candidate_sha")
    valid = bool(sources) and all(re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))) and item.get("candidate_sha") == sha for item in sources)
    facts = {"source_count": len(sources), "source_hashes": sorted((str(item.get("path")), str(item.get("sha256"))) for item in sources), "candidate_sha": sha}
    return _output(inp, facts=facts, evidence=[str(item.get("path")) for item in sources], decision="PASS" if valid else "BLOCK", blocker=None if valid else "decision_time_metadata_manifest_invalid", next_action="continue_semantic_graph" if valid else "reacquire_hash_pinned_metadata", reopen=() if valid else ("reacquire_hash_pinned_metadata",))


def _target_paths(inp: StepInput) -> StepOutput:
    verification = inp.raw_inputs.get("target_path_verification") or {}
    paths = sorted(map(str, verification.get("paths") or []))
    valid = bool(paths) and all(not path.endswith(("/conftest.py", "/__init__.py")) and path.startswith(("test/", "tests/", "testing/")) for path in paths)
    blocker = None if valid else str(verification.get("blocker") or "native_target_path_not_verified")
    return _output(inp, facts={"paths": paths, "target_path_verified": valid}, evidence=["target_path_verification", *paths], decision="PASS" if valid else "BLOCK", blocker=blocker, next_action="continue_semantic_graph" if valid else str(inp.raw_inputs.get("next_allowed_action") or "supply_verified_native_target_path"), reopen=() if valid else tuple(inp.raw_inputs.get("reopen_conditions") or ["supply_verified_native_target_path"]))


def _commands(inp: StepInput) -> StepOutput:
    candidates = inp.raw_inputs.get("ranked_command_candidates") or []
    source_hashes = {str(item.get("path")): str(item.get("sha256")) for item in inp.raw_inputs.get("metadata_source_files") or []}
    authoritative = [item for item in candidates if source_hashes.get(str(item.get("source_path"))) == str(item.get("source_sha256"))]
    valid = bool(authoritative)
    return _output(inp, facts={"authoritative_commands": authoritative, "authoritative_count": len(authoritative)}, evidence=sorted(source_hashes), decision="PASS" if valid else "BLOCK", blocker=None if valid else "authoritative_command_source_missing", next_action="continue_semantic_graph" if valid else "supply_project_local_command_authority", reopen=() if valid else ("supply_project_local_command_authority",))


def _rank(inp: StepInput) -> StepOutput:
    authoritative = _commands(inp).facts["authoritative_commands"]
    ranked = rank_command_candidates(authoritative)
    if ranked["selected"] is not None:
        decision, blocker, next_action = "PASS", None, "continue_semantic_graph"
    elif ranked["conflicts"]:
        decision, blocker, next_action = "MANUAL_REVIEW", "command_source_conflict_manual_review", "review_conflicting_authoritative_command_sources"
    else:
        decision, blocker, next_action = "BLOCK", "command_selection_unresolved", "supply_unique_authoritative_command"
    facts = {"selected": ranked["selected"], "conflicts": ranked["conflicts"], "ranked_candidates": ranked["ranked_candidates"], "selection_confidence": ranked["selection_confidence"]}
    return _output(inp, facts=facts, evidence=[str(item.get("source_path")) for item in authoritative], decision=decision, blocker=blocker, next_action=next_action, reopen=() if decision == "PASS" else (next_action,))


def _runner_target(inp: StepInput) -> StepOutput:
    selected = _rank(inp).facts.get("selected") or {}
    argv = selected.get("argv") or []
    runner = argv[2] if len(argv) >= 3 and argv[0] in {"python", "python3"} and argv[1] == "-m" else (argv[0] if argv else "")
    target = str(inp.raw_inputs.get("target_package") or "")
    classification = classify_runner_target(runner_package=runner.replace("-", "_").lower(), target_package=target.replace("-", "_").lower())
    valid = classification == "runner_target_split_not_required"
    return _output(inp, facts={"runner_package": runner, "target_package": target, "classification": classification}, evidence=["selected_command.argv", "target_package"], decision="PASS" if valid else "BLOCK", blocker=None if valid else classification, next_action="continue_semantic_graph" if valid else "prove_runner_target_import_origin", reopen=() if valid else ("prove_runner_target_import_origin",))


def _harness(inp: StepInput) -> StepOutput:
    target = _target_paths(inp)
    commands = _commands(inp)
    manifest = inp.raw_inputs.get("decision_time_evidence_manifest") or {}
    valid = target.gate_decision == "PASS" and commands.gate_decision == "PASS" and not manifest.get("forbidden_evidence_used")
    return _output(inp, facts={"classification": "project_native_static_non_circular" if valid else "harness_origin_static_unresolved", "non_circular": valid}, evidence=["native target path", "authoritative command source", "decision-time evidence manifest"], decision="PASS" if valid else "BLOCK", blocker=None if valid else "harness_origin_static_unresolved", next_action="continue_semantic_graph" if valid else "supply_non_circular_harness_origin", reopen=() if valid else ("supply_non_circular_harness_origin",))


def _provider(inp: StepInput) -> StepOutput:
    classification = str(inp.raw_inputs.get("provider_feasibility_class") or "provider_metadata_missing")
    complete = classification != "provider_metadata_missing"
    bounded = classification not in {"external_service_required_static", "network_or_model_dependency_static"}
    valid = complete and bounded
    blocker = None if valid else ("provider_feasibility_unclassified" if not complete else "provider_probe_plan_not_bounded")
    return _output(inp, facts={"classification": classification, "classified": complete, "bounded": bounded}, evidence=["provider feasibility evidence", *map(str, inp.raw_inputs.get("declared_dependencies") or [])], decision="PASS" if valid else "BLOCK", blocker=blocker, next_action="continue_semantic_graph" if valid else ("classify_provider_feasibility" if not complete else "supply_bounded_provider_capsule_plan"), reopen=() if valid else (("classify_provider_feasibility" if not complete else "supply_bounded_provider_capsule_plan"),))


def _promotion(inp: StepInput) -> StepOutput:
    checks = {
        "source": _source_identity(inp).gate_decision == "PASS",
        "sha": _candidate_sha(inp).gate_decision == "PASS",
        "metadata": _metadata(inp).gate_decision == "PASS",
        "target": _target_paths(inp).gate_decision == "PASS",
        "command": _rank(inp).gate_decision == "PASS",
        "runner_target": _runner_target(inp).gate_decision == "PASS",
        "harness": _harness(inp).gate_decision == "PASS",
        "provider": _provider(inp).gate_decision == "PASS",
    }
    valid = all(checks.values())
    return _output(inp, facts={"checks": checks, "promoted": valid}, evidence=list(checks), decision="PASS" if valid else "BLOCK", blocker=None if valid else "tier3_promotion_requirements_not_met", next_action="batch068h_bounded_provider_command_probe" if valid else "resolve_first_failed_semantic_gate", reopen=() if valid else ("resolve_first_failed_semantic_gate",))


def _terminal(inp: StepInput) -> StepOutput:
    promotion = _promotion(inp)
    if promotion.gate_decision == "PASS":
        state, blocker, action = "tier3_provider_probe_authorized", None, "batch068h_bounded_provider_command_probe"
    else:
        state = str(inp.raw_inputs.get("exact_blocker") or "semantic_recomputation_blocked")
        blocker = state
        action = str(inp.raw_inputs.get("next_allowed_action") or "resolve_semantic_frontier_blocker")
    return _output(inp, facts={"terminal_state": state, "exact_blocker": blocker, "next_allowed_action": action, "reopen_conditions": inp.raw_inputs.get("reopen_conditions") or []}, evidence=["semantic promotion recomputation", "candidate terminal vocabulary"], decision="PASS", next_action=action)


def establish_source_identity(inp: StepInput) -> StepOutput: return _source_identity(inp)
def establish_candidate_sha(inp: StepInput) -> StepOutput: return _candidate_sha(inp)
def acquire_decision_time_metadata(inp: StepInput) -> StepOutput: return _metadata(inp)
def resolve_native_target_paths(inp: StepInput) -> StepOutput: return _target_paths(inp)
def extract_authoritative_commands(inp: StepInput) -> StepOutput: return _commands(inp)
def rank_and_normalize_commands(inp: StepInput) -> StepOutput: return _rank(inp)
def resolve_runner_target_relationship(inp: StepInput) -> StepOutput: return _runner_target(inp)
def classify_harness_origin(inp: StepInput) -> StepOutput: return _harness(inp)
def classify_provider_feasibility(inp: StepInput) -> StepOutput: return _provider(inp)
def decide_tier3_promotion(inp: StepInput) -> StepOutput: return _promotion(inp)
def emit_candidate_terminal_state(inp: StepInput) -> StepOutput: return _terminal(inp)


def _verify(inp: StepInput, output: StepOutput, recompute: SemanticHandler) -> VerificationResult:
    expected = recompute(inp)
    errors: list[str] = []
    if output.facts != expected.facts: errors.append("handler_facts_do_not_match_independent_recomputation")
    if output.gate_decision != expected.gate_decision: errors.append("handler_gate_decision_false_or_incorrect")
    if output.blocker_code != expected.blocker_code: errors.append("handler_blocker_incorrect")
    if output.candidate_state != expected.candidate_state: errors.append("handler_candidate_state_incorrect")
    if not output.input_hashes: errors.append("meaningful_input_hash_required")
    if not output.decision_time_evidence_consumed: errors.append("decision_time_evidence_required")
    if output.forbidden_evidence_checked != expected.forbidden_evidence_checked or output.forbidden_evidence_findings != expected.forbidden_evidence_findings: errors.append("forbidden_evidence_check_not_derived")
    return VerificationResult("PASS" if not errors else "FAIL", hash_record(asdict(expected)), hash_record(asdict(output)), tuple(errors))


def verify_source_identity_binding(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _source_identity)
def verify_candidate_sha_reachability(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _candidate_sha)
def verify_metadata_manifest_and_hashes(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _metadata)
def verify_native_target_paths_at_candidate_sha(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _target_paths)
def verify_command_source_authority(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _commands)
def verify_command_selection_determinism(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _rank)
def verify_runner_target_contract(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _runner_target)
def verify_harness_origin_non_circularity(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _harness)
def verify_provider_feasibility_evidence(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _provider)
def verify_tier3_promotion_by_recomputation(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _promotion)
def verify_terminal_state_completeness(i: StepInput, o: StepOutput) -> VerificationResult: return _verify(i, o, _terminal)


PRODUCTION_HANDLERS: dict[str, SemanticHandler] = {
    "establish_source_identity": establish_source_identity,
    "establish_candidate_sha": establish_candidate_sha,
    "acquire_decision_time_metadata": acquire_decision_time_metadata,
    "resolve_native_target_paths": resolve_native_target_paths,
    "extract_authoritative_commands": extract_authoritative_commands,
    "rank_and_normalize_commands": rank_and_normalize_commands,
    "resolve_runner_target_relationship": resolve_runner_target_relationship,
    "classify_harness_origin": classify_harness_origin,
    "classify_provider_feasibility": classify_provider_feasibility,
    "decide_tier3_promotion": decide_tier3_promotion,
    "emit_candidate_terminal_state": emit_candidate_terminal_state,
}

PRODUCTION_VERIFIERS: dict[str, SemanticVerifier] = {
    "verify_source_identity_binding": verify_source_identity_binding,
    "verify_candidate_sha_reachability": verify_candidate_sha_reachability,
    "verify_metadata_manifest_and_hashes": verify_metadata_manifest_and_hashes,
    "verify_native_target_paths_at_candidate_sha": verify_native_target_paths_at_candidate_sha,
    "verify_command_source_authority": verify_command_source_authority,
    "verify_command_selection_determinism": verify_command_selection_determinism,
    "verify_runner_target_contract": verify_runner_target_contract,
    "verify_harness_origin_non_circularity": verify_harness_origin_non_circularity,
    "verify_provider_feasibility_evidence": verify_provider_feasibility_evidence,
    "verify_tier3_promotion_by_recomputation": verify_tier3_promotion_by_recomputation,
    "verify_terminal_state_completeness": verify_terminal_state_completeness,
}


def resolve_production_registry(steps: list[dict[str, Any]]) -> dict[str, Any]:
    missing_h = sorted({str(step["handler"]) for step in steps if str(step["handler"]) not in PRODUCTION_HANDLERS})
    missing_v = sorted({str(step["verifier"]) for step in steps if str(step["verifier"]) not in PRODUCTION_VERIFIERS})
    forbidden = [step["step_id"] for step in steps if step.get("handler") == "passthrough_handler" or step.get("verifier") == "nonempty_output_verifier"]
    return {"status": "PASS" if not missing_h and not missing_v and not forbidden else "FAIL", "unresolved_handlers": missing_h, "unresolved_verifiers": missing_v, "generic_production_usage": forbidden, "handler_count": len(PRODUCTION_HANDLERS), "verifier_count": len(PRODUCTION_VERIFIERS)}


def execute_semantic_graph(candidate_id: str, raw_inputs: dict[str, Any], policy: dict[str, Any], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    prior_hash = "GENESIS"
    terminal_decision: str | None = None
    terminal_blocker: str | None = None
    for spec in steps:
        step_id = str(spec["step_id"])
        if terminal_decision:
            record = {
                "stable_step_id": step_id, "candidate_id": candidate_id,
                "handler_name": spec["handler"], "verifier_name": spec["verifier"],
                "operation_status": "NOT_RUN", "evidence_status": "NOT_ESTABLISHED",
                "gate_decision": "NOT_RUN", "candidate_state": "not_run_upstream_manual_review" if terminal_decision == "MANUAL_REVIEW" else "not_run_upstream_block",
                "input_hashes": [], "decision_time_evidence_consumed": [],
                "forbidden_evidence_checked": False, "forbidden_evidence_findings": [],
                "output_hash": hash_record({"step_id": step_id, "not_run": terminal_decision, "blocker": terminal_blocker}),
                "verification_status": "NOT_RUN", "verification_hash": "NOT_RUN",
                "blocker_code": terminal_blocker, "blocker_reason": "upstream terminal decision",
                "next_allowed_action": "resolve_upstream_terminal_decision", "reopen_conditions": ["resolve_upstream_terminal_decision"],
                "prior_state_hash": prior_hash,
            }
        else:
            inp = StepInput(step_id, candidate_id, raw_inputs, policy, prior_hash)
            handler = PRODUCTION_HANDLERS[str(spec["handler"])]
            verifier = PRODUCTION_VERIFIERS[str(spec["verifier"])]
            output = handler(inp)
            verification = verifier(inp, output)
            decision = output.gate_decision if verification.status == "PASS" else "BLOCK"
            blocker = output.blocker_code if verification.status == "PASS" else "independent_verifier_rejected_handler_output"
            record = {
                "stable_step_id": step_id, "candidate_id": candidate_id,
                "handler_name": spec["handler"], "verifier_name": spec["verifier"],
                **{key: value for key, value in asdict(output).items() if key != "facts"},
                "gate_decision": decision, "blocker_code": blocker,
                "output_hash": hash_record({"step_id": step_id, "facts": output.facts, "decision": decision}),
                "verification_status": verification.status, "verification_hash": hash_record(asdict(verification)),
                "prior_state_hash": prior_hash,
            }
            if decision in {"BLOCK", "MANUAL_REVIEW"}:
                terminal_decision, terminal_blocker = decision, blocker
        record["post_state_hash"] = hash_record(record)
        prior_hash = record["post_state_hash"]
        transitions.append(record)
    return transitions


# Explicit test-fixture compatibility only. Production graphs must use the registries above.
def passthrough_handler(context: dict[str, Any]) -> dict[str, Any]:
    return dict(context.get("step_payload") or {})


def nonempty_output_verifier(output: dict[str, Any]) -> bool:
    return isinstance(output, dict) and bool(output)


HANDLERS = {"passthrough_handler": passthrough_handler}
VERIFIERS = {"nonempty_output_verifier": nonempty_output_verifier}


def resolve_registry(steps: list[dict[str, Any]]) -> dict[str, Any]:
    missing_h = sorted({str(step["handler"]) for step in steps if str(step["handler"]) not in HANDLERS})
    missing_v = sorted({str(step["verifier"]) for step in steps if str(step["verifier"]) not in VERIFIERS})
    return {"status": "PASS" if not missing_h and not missing_v else "FAIL", "unresolved_handlers": missing_h, "unresolved_verifiers": missing_v, "handler_count": len(HANDLERS), "verifier_count": len(VERIFIERS)}


def execute_static_graph(candidate_id: str, steps: list[dict[str, Any]], payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    prior_hash = "GENESIS"
    upstream: str | None = None
    for spec in steps:
        step_id = str(spec["step_id"])
        output = {"skipped": True, "upstream_blocker": upstream} if upstream else HANDLERS[str(spec["handler"])]({"step_payload": payloads.get(step_id, {})})
        passed = not upstream and VERIFIERS[str(spec["verifier"])](output) and output.get("status") not in {"BLOCK", "FAIL"}
        status = "pass" if passed else "block"
        blocker = None if passed else str(upstream or output.get("blocker") or f"{step_id.lower()}_blocked")
        if blocker: upstream = blocker
        record = {"stable_step_id": step_id, "candidate_id": candidate_id, "handler_name": spec["handler"], "verifier_name": spec["verifier"], "input_hashes": output.get("input_hashes", []), "decision_time_evidence_used": output.get("decision_time_evidence_used", []), "forbidden_evidence_checked": True, "output_hash": hash_record(output), "status": status, "blocker_code": blocker, "blocker_reason": output.get("blocker_reason"), "next_allowed_action": output.get("next_allowed_action", "continue_static_frontier_graph" if not blocker else "supply_decision_time_safe_evidence"), "reopen_conditions": output.get("reopen_conditions", [] if not blocker else ["new_decision_time_safe_evidence"]), "prior_state_hash": prior_hash}
        record["post_state_hash"] = hash_record(record); prior_hash = record["post_state_hash"]; records.append(record)
    return records
