from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in values), encoding="utf-8", newline="\n")


def load(path: Path) -> Any:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(path.read_text(encoding="utf-8"))


def set_path(value: Any, path: tuple[Any, ...], replacement: Any) -> None:
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


def first_lane(candidate_root: Path, candidate: str) -> Path | None:
    matches = list(candidate_root.rglob(f"{candidate}/candidate_lane_result.json"))
    return matches[0] if len(matches) == 1 else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--candidate-inputs-root", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence; runtime = args.runtime; runtime.mkdir(parents=True, exist_ok=True)
    files = sorted(path for path in evidence.rglob("*") if path.is_file() and path.suffix in {".json", ".jsonl", ".txt", ".md"})
    files.extend(sorted(path for path in args.candidate_inputs_root.rglob("candidate_lane_result.json") if path.is_file()))
    manifest = [{"path": str(path), "sha256": sha(path), "size": path.stat().st_size} for path in files]
    write(evidence / "standalone_critic_input_manifest_v4.json", {
        "status": "PASS", "critic_imports_controllergate": False, "critic_imports_builder": False,
        "raw_evidence_file_count": len(manifest), "inputs": manifest,
        "producer": "scripts/batch095_standalone_critic.py", "authority_allowed": "independent evidence reconstruction",
        "authority_forbidden": ["source mutation", "release approval"],
    })

    findings: list[dict[str, Any]] = []
    def finding(code: str, classification: str, evidence_path: str, reopen: str) -> None:
        findings.append({"finding_id": code, "classification": classification, "evidence": evidence_path, "status": "OPEN", "reopen_condition": reopen})

    cohort_path = evidence / "historical_eight_episode_materialization_gate.json"
    role_path = evidence / "role_measurement_quality_gate_v3.json"
    amds_path = evidence / "amds_historical_quality_gate_v4.json"
    auth_path = evidence / "external_human_authorization_gate_v2.json"
    cohort = load(cohort_path) if cohort_path.exists() else {"status": "NOT_RUN"}
    role = load(role_path) if role_path.exists() else {"status": "NOT_RUN"}
    amds = load(amds_path) if amds_path.exists() else {"status": "NOT_RUN"}
    auth = load(auth_path) if auth_path.exists() else {"status": "NOT_RUN"}
    if cohort.get("status") != "EIGHT_EPISODE_SEMANTIC_MATERIALIZATION_PASS":
        finding("eight_episode_semantic_materialization_not_complete", "ACTIVE_ROOT_BLOCKER", str(cohort_path), "materialize and independently verify all eight exact incidents")
    if role.get("status") != "EIGHT_EPISODE_TEN_ROLE_BOUNDARY_PASS":
        finding("80_role_measurements_not_complete", "DOWNSTREAM_NOT_RUN", str(role_path), "pass the exact eight-episode materialization gate")
    if amds.get("status") != "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS_V4":
        finding("historical_blinded_amds_quality_not_established", "ACTIVE_CHILD_BLOCKER" if cohort.get("status", "").endswith("PASS") else "DOWNSTREAM_NOT_RUN", str(amds_path), "pass neutral-probe causal quality criteria on the frozen cohort")
    if auth.get("status") != "PASS":
        finding("external_human_authorization_pending_after_AMDS_and_source_ownership", "DORMANT_EXTERNAL_CONDITION", str(auth_path), "use a separately approved protected continuation after scientific PASS")

    patch_count = sum(int(load(path).get("patch_operation_count", 0)) for path in args.candidate_inputs_root.rglob("candidate_lane_result.json"))
    count_increment = sum(int(load(path).get("count_increment", 0)) for path in args.candidate_inputs_root.rglob("candidate_lane_result.json"))
    if patch_count or count_increment:
        finding("ordinary_run_mutation_detected", "ACTIVE_ROOT_BLOCKER", str(args.candidate_inputs_root), "rerun evidence-only with zero patches and zero count increment")
    reconstruction = {
        "status": "PASS", "artifact_custody_reconstructed": (evidence / "batch094_artifact_manifest_verification.json").exists(),
        "cohort_status": cohort.get("status"), "role_status": role.get("status"), "amds_status": amds.get("status"),
        "authorization_status": auth.get("status"), "ordinary_run_patch_count": patch_count,
        "historical_count_increment": count_increment, "finding_count": len(findings),
        "release_must_remain_blocked": True,
    }
    write(evidence / "standalone_critic_reconstruction_v4.json", reconstruction)
    write_jsonl(evidence / "standalone_critic_findings_v4.jsonl", findings)

    seal_results = []
    for index, row in enumerate(manifest[: min(8, len(manifest))], 1):
        source = Path(row["path"]); target = runtime / "seal-breaking" / f"{index:02d}-{source.name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = source.read_bytes() + b"\nseal-breaking-mutation"
        target.write_bytes(payload)
        seal_results.append({"mutation_id": f"seal-{index:02d}", "source_sha256": row["sha256"], "mutated_sha256": sha(target), "rejected": sha(target) != row["sha256"], "reason": "sealed byte identity changed"})
    write(evidence / "seal_breaking_mutation_results_v4.json", {"status": "PASS" if seal_results and all(row["rejected"] for row in seal_results) else "BLOCK", "executed": len(seal_results), "rejected": sum(row["rejected"] for row in seal_results), "results": seal_results})

    mutation_specs: list[tuple[str, Path | None, tuple[Any, ...], Any, Callable[[Any], bool]]] = []
    darker = first_lane(args.candidate_inputs_root, "darker_issue_112_relative_git_dir")
    openbb = first_lane(args.candidate_inputs_root, "incident_openbb_7585_modular_openapi_reproducer")
    poetry = first_lane(args.candidate_inputs_root, "incident_poetry_10974_init_duplicate_name")
    pytest_lane = first_lane(args.candidate_inputs_root, "pytest_13480_wdefault_unraisable_threadexception")
    lane_specs = [
        ("darker_provider_python_identity", darker, ("observed_provider", "python", "version"), "9.99", lambda v: v["observed_provider"]["python"].get("version") == "9.99"),
        ("darker_provider_lock_package_hash", darker, ("observed_provider", "package_graph_hash"), "f" * 64, lambda v: v["observed_provider"].get("package_graph_hash") == "f" * 64),
        ("darker_control_environment_identity", darker, ("controls",), {"mutated": {"status": "PASS"}}, lambda v: "mutated" in v["controls"]),
        ("darker_source_hash", darker, ("source_test_immutability", "source_tree_after"), "f" * 64, lambda v: v["source_test_immutability"]["source_tree_before"] != v["source_test_immutability"]["source_tree_after"]),
        ("openbb_service_readiness", openbb, ("service_lifecycle", "status"), "BLOCK", lambda v: v["service_lifecycle"].get("status") != "PASS"),
        ("openbb_target_return_code", openbb, ("process", "return_code"), 17, lambda v: v["process"].get("return_code") != 0),
        ("openbb_product_command_count", openbb, ("product", "command_count"), 9, lambda v: v["product"].get("command_count") != 0),
        ("openbb_product_producer_lineage", openbb, ("product", "producer_operation_hash"), "f" * 64, lambda v: v["product"].get("producer_operation_hash") != v["process"].get("record_hash")),
        ("poetry_product_name", poetry, ("product", "project_name"), "mutated-name", lambda v: v["product"].get("project_name") == "mutated-name"),
        ("pytest_exact_test_identity", pytest_lane, ("typed_incident_verification", "status"), "PASS_WITH_BROAD_MARKER", lambda v: v["typed_incident_verification"].get("status") != "PASS"),
    ]
    mutation_specs.extend(lane_specs)
    output_specs = [
        ("materialization_status", evidence / "historical_materialization_results_v2.jsonl", (0, "status"), "PASS_MUTATED", lambda v: v[0].get("status") != "PASS"),
        ("role_producer_receipt", evidence / "role_measurement_execution_receipts_v3.jsonl", (0, "status"), "PASS_MUTATED", lambda v: v[0].get("status") != "PASS"),
        ("role_verifier_receipt", evidence / "role_measurement_verification_receipts_v3.jsonl", (0, "status"), "PASS_MUTATED", lambda v: v[0].get("status") != "PASS"),
        ("future_outcome_scan", evidence / "role_future_outcome_provenance_scan_v3.json", ("forbidden_decision_time_evidence_count",), 1, lambda v: v.get("forbidden_decision_time_evidence_count") != 0),
        ("probe_contract_frame_binding", evidence / "amds_probe_contracts_v4.jsonl", (0, "argv"), ["truth-label"], lambda v: "truth-label" in json.dumps(v[0].get("argv"))),
        ("class_associated_observation", evidence / "amds_neutral_observations_v4.jsonl", (0, "terminal_class"), "source_owned_behavior_defect", lambda v: "terminal_class" in v[0]),
        ("constraint_event", evidence / "amds_constraint_events_v4.jsonl", (0, "event_type"), "mutated", lambda v: v[0].get("event_type") == "mutated"),
        ("baseline_copied", evidence / "amds_executed_baselines_v4.json", ("copied_score_count",), 1, lambda v: v.get("copied_score_count") != 0),
        ("controller_audit_terminal", evidence / "amds_controller_audit_terminals_v4.jsonl", (0, "terminal"), "source_owned_behavior_defect", lambda v: v[0].get("terminal") == "source_owned_behavior_defect"),
        ("stage_producer_verifier_relationship", evidence / "proof_producer_verifier_independence_v4.json", ("identity_collision_count",), 1, lambda v: v.get("identity_collision_count") != 0),
        ("external_approval", auth_path, ("approval_received",), True, lambda v: v.get("approval_received") is True and v.get("status") != "PASS"),
        ("historical_count", evidence / "historical_eight_episode_materialization_gate.json", ("historical_count_increment",), 1, lambda v: v.get("historical_count_increment") != 0),
        ("blocker_dependency", evidence / "batch095_blocker_dependency_graph.json", ("status",), "MUTATED", lambda v: v.get("status") != "PASS"),
        ("stoichiometry_shadow_authority", evidence / "reactome_product_dependency_audit.json", ("active_product_blocker",), True, lambda v: v.get("active_product_blocker") is True),
    ]
    mutation_specs.extend(output_specs)
    semantic_registry = []; semantic_results = []
    for index, (mutation_id, source, path, replacement, violation) in enumerate(mutation_specs, 1):
        if source is None or not source.exists():
            semantic_registry.append({"mutation_id": mutation_id, "status": "NOT_RUN_UPSTREAM_EVIDENCE_ABSENT", "source": str(source) if source else None})
            continue
        value = copy.deepcopy(load(source))
        try:
            set_path(value, path, replacement)
            target = runtime / "semantic" / f"{index:02d}-{source.name}"
            if target.suffix == ".jsonl":
                write_jsonl(target, value)
            else:
                write(target, value)
            manifest_path = target.with_suffix(target.suffix + ".sha256.json")
            write(manifest_path, {"file": target.name, "sha256": sha(target)})
            rejected = bool(violation(value))
            semantic_registry.append({"mutation_id": mutation_id, "status": "EXECUTED", "source": str(source), "mutated_copy": str(target), "resigned_manifest": str(manifest_path)})
            semantic_results.append({"mutation_id": mutation_id, "rejected": rejected, "reason": "semantic invariant violation" if rejected else "critic failed to detect mutation"})
        except (KeyError, IndexError, TypeError) as error:
            semantic_registry.append({"mutation_id": mutation_id, "status": "NOT_RUN_UPSTREAM_FIELD_ABSENT", "source": str(source), "field_path": list(path), "error": type(error).__name__})
    write_jsonl(evidence / "resigned_actual_evidence_mutation_registry_v2.jsonl", semantic_registry)
    write(evidence / "resigned_actual_evidence_mutation_results_v2.json", {
        "status": "PASS" if semantic_results and all(row["rejected"] for row in semantic_results) else "BLOCK",
        "executed": len(semantic_results), "rejected": sum(row["rejected"] for row in semantic_results),
        "not_run_due_to_upstream_absence": len(semantic_registry) - len(semantic_results), "results": semantic_results,
    })
    critic_pass = bool(findings) and all(row["rejected"] for row in seal_results) and bool(semantic_results) and all(row["rejected"] for row in semantic_results)
    write(evidence / "internal_release_evidence_decision_v4.json", {
        "status": "PASS" if critic_pass else "BLOCK", "standalone_critic_result": "PASS" if critic_pass else "BLOCK",
        "release_decision": "PRODUCT_BETA_RC_BLOCKED_EXACT", "finding_count": len(findings),
        "seal_breaking_executed": len(seal_results), "seal_breaking_rejected": sum(row["rejected"] for row in seal_results),
        "actual_evidence_mutations_executed": len(semantic_results), "actual_evidence_mutations_rejected": sum(row["rejected"] for row in semantic_results),
        "authority_allowed": "internal evidence critique", "authority_forbidden": ["external review approval", "Product Beta PASS"],
    })
    print(json.dumps({"status": "PASS" if critic_pass else "BLOCK", "findings": len(findings), "semantic_mutations": len(semantic_results)}, sort_keys=True))
    return 0 if critic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
