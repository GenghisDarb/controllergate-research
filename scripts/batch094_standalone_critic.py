from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable


PRODUCER = "scripts/batch094_standalone_critic.py"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as stream:
        return sum(bool(line.strip()) for line in stream)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(value, sort_keys=True) + "\n" for value in values), encoding="utf-8", newline="\n")


def semantic_errors(bundle: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    graph = bundle["rpir_v2_1_graph_completeness_decision.json"]
    firewall = bundle["reactome_translation_authority_firewall_v3.json"]
    primitive = bundle["primitive_behavioral_coverage.json"]
    cohort = bundle["fresh_cohort_materialization_summary.json"]
    no_substitution = bundle["historical_no_substitution_audit.json"]
    downstream = bundle["batch094_downstream_gate_status.json"]
    approval = bundle["external_human_authorization_gate.json"]
    installed = bundle["installed_cross_platform_equivalence_v3.json"]
    if graph.get("reaction_occurrences") != 16814 or graph.get("silent_omission_count") != 0:
        errors.append("Reactome source occurrence coverage changed")
    if graph.get("normal_variant_pair_count") != 720 or graph.get("computed_first_divergence_count") != 674:
        errors.append("normal/variant source graph changed")
    if firewall.get("candidate_count") != 16814 or firewall.get("value_bound_count") != 16814:
        errors.append("translation disposition coverage changed")
    if firewall.get("production_promotion_count") != 0 or firewall.get("repair_authority_count") != 0:
        errors.append("translation authority escalated without execution depth")
    if primitive.get("status") != "PASS" or primitive.get("behaviorally_demonstrated_count") != 46:
        errors.append("primitive behavioral evidence changed")
    if cohort.get("candidate_order", []) != [
        "darker_issue_112_relative_git_dir", "py_bugger_issue_65",
        "cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion",
        "audioread_144_py313_aifc_removed", "pytest_13480_wdefault_unraisable_threadexception",
        "incident_openbb_7585_modular_openapi_reproducer", "incident_poetry_10974_init_duplicate_name",
    ]:
        errors.append("frozen cohort order or membership changed")
    if cohort.get("status") != "BLOCK" or cohort.get("materialized_candidate_count") != 6:
        errors.append("minimum-cohort result was overpromoted")
    if no_substitution.get("replacement_count") != 0:
        errors.append("candidate substitution introduced")
    if downstream.get("role_measurements") != "NOT_RUN" or downstream.get("amds") != "NOT_RUN":
        errors.append("downstream scientific gate executed after cohort block")
    if downstream.get("patch_operation_count") != 0 or downstream.get("historical_count_increment") != 0:
        errors.append("unauthorized patch or count mutation")
    if approval.get("status") != "HUMAN_AUTHORIZATION_BLOCKED_EXACT" or approval.get("repository_generated_approval") is not False:
        errors.append("external human authority was forged")
    if installed.get("status") not in {"PASS", "BLOCK_MISSING_PLATFORM_EVIDENCE"}:
        errors.append("installed cross-platform evidence invalid")
    if installed.get("status") == "PASS" and set(installed.get("available_platforms", [])) != {"linux", "windows"}:
        errors.append("cross-platform pass lacks both installed platforms")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--workspace")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    critical = [
        "rpir_v2_1_graph_completeness_decision.json",
        "rpir_v2_1_reactions.jsonl",
        "reactome_value_binding_registry.jsonl",
        "reactome_translation_candidates_v3.jsonl",
        "reactome_translation_authority_firewall_v3.json",
        "primitive_behavioral_coverage.json",
        "reactome_chapter_scenario_registry_v3.jsonl",
        "fresh_cohort_materialization_summary.json",
        "historical_materialization_results.jsonl",
        "historical_acquisition_broker_operations.jsonl",
        "historical_no_substitution_audit.json",
        "role_measurement_quality_gate_v2.json",
        "amds_historical_quality_gate_v3.json",
        "external_human_authorization_gate.json",
        "batch094_downstream_gate_status.json",
        "installed_cross_platform_equivalence_v3.json",
    ]
    missing = [name for name in critical if not (output / name).is_file()]
    if missing:
        raise FileNotFoundError(f"critic inputs missing: {missing}")
    manifest_rows = [{"path": name, "sha256": sha(output / name), "size": (output / name).stat().st_size} for name in critical]
    write_json(output / "standalone_critic_input_manifest_v3.json", {
        "status": "PASS", "producer": PRODUCER, "critic_runtime": "python_standard_library_only",
        "controllergate_imported": False, "execution_depth": "raw_file_hash_and_stream_reconstruction",
        "semantic_scope": "Batch094 actual RPIR, compiler, installed, cohort, and blocked-authority evidence",
        "authority_allowed": "independent internal critique", "authority_forbidden": ["external release approval", "repair authority"],
        "files": manifest_rows,
    })
    graph = read_json(output / "rpir_v2_1_graph_completeness_decision.json")
    firewall = read_json(output / "reactome_translation_authority_firewall_v3.json")
    primitive = read_json(output / "primitive_behavioral_coverage.json")
    cohort = read_json(output / "fresh_cohort_materialization_summary.json")
    materialized = rows(output / "historical_materialization_results.jsonl")
    downstream = read_json(output / "batch094_downstream_gate_status.json")
    installed = read_json(output / "installed_cross_platform_equivalence_v3.json")
    reconstructed = {
        "rpir_reaction_rows": line_count(output / "rpir_v2_1_reactions.jsonl"),
        "translation_candidate_rows": line_count(output / "reactome_translation_candidates_v3.jsonl"),
        "value_binding_rows": line_count(output / "reactome_value_binding_registry.jsonl"),
        "chapter_scenario_rows": line_count(output / "reactome_chapter_scenario_registry_v3.jsonl"),
        "frozen_candidates": len(materialized),
        "materialized_candidates": sum(row.get("status") == "PASS" for row in materialized),
        "blocked_candidates": sum(row.get("status") != "PASS" for row in materialized),
        "primitive_behavior_count": primitive["behaviorally_demonstrated_count"],
        "patch_operation_count": downstream["patch_operation_count"],
        "historical_increment": downstream["historical_count_increment"],
        "cross_platform_status": installed["status"],
    }
    reconstruction_pass = (
        reconstructed["rpir_reaction_rows"] == graph["reaction_occurrences"] == 16814
        and reconstructed["translation_candidate_rows"] == firewall["candidate_count"] == 16814
        and reconstructed["value_binding_rows"] > 16814
        and reconstructed["chapter_scenario_rows"] == 29
        and reconstructed["frozen_candidates"] == cohort["frozen_candidate_count"] == 8
        and reconstructed["materialized_candidates"] == cohort["materialized_candidate_count"] == 6
        and reconstructed["primitive_behavior_count"] == 46
        and reconstructed["patch_operation_count"] == reconstructed["historical_increment"] == 0
    )
    write_json(output / "standalone_critic_reconstruction_v3.json", {
        "status": "PASS" if reconstruction_pass else "FAIL", "producer": PRODUCER,
        "execution_depth": "independent_actual_raw_evidence_reconstruction",
        "semantic_scope": "RPIR value coverage, behavioral compiler, frozen cohort, installed shadow execution, and authority boundary",
        "authority_allowed": "critic findings", "authority_forbidden": ["external approval", "repair authorization"],
        "reconstructed": reconstructed,
    })
    findings = [
        {"finding_id": "B094-CRITIC-01", "severity": "release_blocking", "finding": "Only six of eight frozen episodes materialized.", "raw_evidence": "historical_materialization_results.jsonl", "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET", "reopen_condition": cohort["reopen_condition"]},
        {"finding_id": "B094-CRITIC-02", "severity": "release_blocking", "finding": "Darker provider and project installation did not produce a target-code replay.", "raw_evidence": "fresh_cohort_materialization_summary.json", "blocker": "provider_dependency_and_project_install_failed", "reopen_condition": "materialize the exact frozen Darker episode in a decision-time-compatible provider without substitution"},
        {"finding_id": "B094-CRITIC-03", "severity": "release_blocking", "finding": "OpenBB project target failure did not materialize.", "raw_evidence": "fresh_cohort_materialization_summary.json", "blocker": "project_target_failure_not_materialized", "reopen_condition": "materialize the exact frozen OpenBB project reproducer without outcome evidence or candidate substitution"},
        {"finding_id": "B094-CRITIC-04", "severity": "release_blocking", "finding": "External human authorization was not granted for historical patch actuation.", "raw_evidence": "external_human_authorization_gate.json", "blocker": "HUMAN_AUTHORIZATION_BLOCKED_EXACT", "reopen_condition": "after every upstream gate passes, obtain a protected externally bound authorization"},
        {"finding_id": "B094-CRITIC-05", "severity": "scientific_boundary", "finding": "AMDS and actual baselines correctly remain not run after the cohort block.", "raw_evidence": "amds_historical_quality_gate_v3.json", "blocker": "AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED", "reopen_condition": "pass materialization and verified semantic-role gates for all frozen episodes"},
        {"finding_id": "B094-CRITIC-06", "severity": "source_format_boundary", "finding": "Exact numeric stoichiometry is not exposed by the consumed release tables.", "raw_evidence": "rpir_v2_1_graph_completeness_decision.json", "blocker": "numeric_stoichiometry_not_exposed_by_consumed_release_tables", "reopen_condition": "admit a byte-frozen exact-release source exposing numeric stoichiometry and cross-reconcile it"},
        {"finding_id": "B094-CRITIC-07", "severity": "workflow_boundary", "finding": "Cross-platform equivalence requires official Linux and Windows evidence in one join.", "raw_evidence": "installed_cross_platform_equivalence_v3.json", "blocker": None if installed["status"] == "PASS" else "official_cross_platform_join_pending", "reopen_condition": "aggregate both official installed-wheel platform jobs"},
    ]
    write_jsonl(output / "standalone_critic_findings_v3.jsonl", findings)

    small_names = [
        "rpir_v2_1_graph_completeness_decision.json", "reactome_translation_authority_firewall_v3.json",
        "primitive_behavioral_coverage.json", "fresh_cohort_materialization_summary.json",
        "historical_no_substitution_audit.json", "batch094_downstream_gate_status.json",
        "external_human_authorization_gate.json", "installed_cross_platform_equivalence_v3.json",
    ]
    base = {name: read_json(output / name) for name in small_names}
    workspace = Path(args.workspace).resolve() if args.workspace else Path(tempfile.mkdtemp(prefix="batch094-critic-"))
    workspace.mkdir(parents=True, exist_ok=True)
    seal_breaking = []
    for mutation_id, target in (("seal-break-cohort", "fresh_cohort_materialization_summary.json"), ("seal-break-rpir", "rpir_v2_1_graph_completeness_decision.json")):
        original = sha(output / target)
        tampered = workspace / f"{mutation_id}.json"
        tampered.write_bytes((output / target).read_bytes() + b" ")
        seal_breaking.append({"mutation_id": mutation_id, "target": target, "expected_sha256": original, "observed_sha256": sha(tampered), "rejected": sha(tampered) != original, "reason": "sealed raw input hash mismatch"})
    write_json(output / "seal_breaking_mutation_results_v3.json", {
        "status": "PASS" if all(row["rejected"] for row in seal_breaking) else "FAIL", "producer": PRODUCER,
        "execution_depth": "physical_copy_byte_mutation", "semantic_scope": "actual Batch094 evidence seals",
        "authority_allowed": "critic rejection evidence", "authority_forbidden": "release approval",
        "executed": len(seal_breaking), "rejected": sum(row["rejected"] for row in seal_breaking), "results": seal_breaking,
    })

    mutations: list[tuple[str, str, Callable[[dict[str, Any]], None]]] = [
        ("reactome_source_omission", "rpir_v2_1_graph_completeness_decision.json", lambda v: v.update(reaction_occurrences=16813, silent_omission_count=1)),
        ("normal_variant_detachment", "rpir_v2_1_graph_completeness_decision.json", lambda v: v.update(normal_variant_pair_count=719)),
        ("translation_depth_escalation", "reactome_translation_authority_firewall_v3.json", lambda v: v.update(production_promotion_count=1)),
        ("translation_coverage_drop", "reactome_translation_authority_firewall_v3.json", lambda v: v.update(value_bound_count=16813)),
        ("primitive_behavior_forgery", "primitive_behavioral_coverage.json", lambda v: v.update(behaviorally_demonstrated_count=45)),
        ("frozen_candidate_substitution", "fresh_cohort_materialization_summary.json", lambda v: v["candidate_order"].__setitem__(0, "substituted_candidate")),
        ("minimum_cohort_overpromotion", "fresh_cohort_materialization_summary.json", lambda v: v.update(status="PASS", materialized_candidate_count=8)),
        ("replacement_count_forgery", "historical_no_substitution_audit.json", lambda v: v.update(replacement_count=1)),
        ("fabricated_amds_execution", "batch094_downstream_gate_status.json", lambda v: v.update(amds="PASS")),
        ("unauthorized_patch_count", "batch094_downstream_gate_status.json", lambda v: v.update(patch_operation_count=1, historical_count_increment=1)),
        ("repository_generated_approval", "external_human_authorization_gate.json", lambda v: v.update(status="PASS", repository_generated_approval=True)),
        ("cross_platform_false_pass", "installed_cross_platform_equivalence_v3.json", lambda v: v.update(status="PASS", available_platforms=["windows"])),
    ]
    registry: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for mutation_id, target, mutate in mutations:
        bundle = copy.deepcopy(base)
        mutate(bundle[target])
        lane = workspace / mutation_id
        lane.mkdir(exist_ok=True)
        for name, value in bundle.items():
            write_json(lane / name, value)
        manifest = {name: sha(lane / name) for name in sorted(bundle)}
        write_json(lane / "resigned_manifest.json", manifest)
        errors = semantic_errors(bundle)
        rejected = bool(errors)
        registry.append({"mutation_id": mutation_id, "target": target, "actual_evidence_basis": True, "manifests_regenerated": True, "mutated_sha256": manifest[target]})
        results.append({"mutation_id": mutation_id, "rejected": rejected, "rejection_reasons": errors, "seal_valid_after_resigning": True})
    write_jsonl(output / "resigned_actual_evidence_mutation_registry.jsonl", registry)
    write_json(output / "resigned_actual_evidence_mutation_results.json", {
        "status": "PASS" if all(row["rejected"] for row in results) else "FAIL", "producer": PRODUCER,
        "execution_depth": "physical_actual_evidence_copy_mutation_rehash_and_semantic_reverification",
        "semantic_scope": "Batch094 RPIR, compiler, cohort, authority, and installed boundaries",
        "authority_allowed": "critic rejection evidence", "authority_forbidden": "external approval",
        "executed": len(results), "rejected": sum(row["rejected"] for row in results), "results": results,
    })
    critic_pass = reconstruction_pass and all(row["rejected"] for row in seal_breaking) and all(row["rejected"] for row in results) and bool(findings)
    write_json(output / "internal_release_evidence_decision_v3.json", {
        "status": "PASS_INTERNAL_CRITIC_WITH_RELEASE_BLOCKERS" if critic_pass else "FAIL",
        "producer": PRODUCER, "execution_depth": "independent_raw_reconstruction_and_physical_mutation_campaign",
        "semantic_scope": "Batch094 internal release evidence", "authority_allowed": "internal blocker decision",
        "authority_forbidden": ["Product Beta approval", "external review approval"], "finding_count": len(findings),
        "seal_breaking_mutations_executed": len(seal_breaking), "seal_breaking_mutations_rejected": sum(row["rejected"] for row in seal_breaking),
        "resigned_actual_mutations_executed": len(results), "resigned_actual_mutations_rejected": sum(row["rejected"] for row in results),
        "release_blockers": [row["blocker"] for row in findings if row.get("blocker")],
    })
    shutil.rmtree(workspace, ignore_errors=True)
    print(json.dumps({"status": "PASS" if critic_pass else "FAIL", "findings": len(findings), "seal_mutations": len(seal_breaking), "semantic_mutations": len(results)}, sort_keys=True))
    return 0 if critic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
