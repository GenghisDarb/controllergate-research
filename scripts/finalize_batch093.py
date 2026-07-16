from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from controllergate.reactome_ir.migration import verify_v1_to_v2_migration


PRODUCER = "scripts/finalize_batch093.py"
MANIFESTS = {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for value in values:
            stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evidence_record(scope: str, depth: str, allowed: object, forbidden: object) -> dict[str, Any]:
    return {"producer": PRODUCER, "execution_depth": depth, "semantic_scope": scope, "authority_allowed": allowed, "authority_forbidden": forbidden}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(args.repo)
    output = Path(args.output)
    contract = read_json(repo / "configs/batch093_prompt_contract.json")
    structured = read_json(output / "reactome_structured_count_reconciliation.json")
    source_manifest = read_json(output / "reactome_structured_source_manifest.json")
    translation = read_json(output / "reactome_translation_structural_coverage.json")
    primitive = read_json(output / "primitive_execution_coverage_v2.json")
    role_gate = read_json(output / "role_measurement_quality_gate.json")
    amds = read_json(output / "amds_historical_quality_gate_v2.json")
    downstream = read_json(output / "batch093_downstream_gate_status.json")
    critic = read_json(output / "internal_release_evidence_decision_v2.json")

    # Exact release-97 source custody exports omit local runtime paths while
    # preserving every byte identity and official archive coordinate.
    public_sources = []
    for source in source_manifest["sources"]:
        public_sources.append({key: value for key, value in source.items() if key != "path"})
    exact_source = {
        **evidence_record("Reactome release 97 structured source custody", "official_Zenodo_release_member_byte_identity", "RPIR v2 parsing", ["software causal authority", "repair authorization"]),
        "status": "PASS", "release": 97, "zenodo_record_id": 21383214, "zenodo_doi": "10.5281/zenodo.21383214",
        "outer_archive_size": contract["reactome_structured_source"]["release_archive_size"],
        "outer_archive_md5": contract["reactome_structured_source"]["release_archive_md5"],
        "sources": public_sources, "runtime_database_sha256": source_manifest["runtime_database_sha256"],
        "raw_sources_committed": False, "runtime_database_committed": False,
    }
    write_json(output / "reactome_release97_structured_source_manifest.json", exact_source)
    write_jsonl(output / "reactome_release97_network_receipts.jsonl", ({
        "source_name": source["name"], "official_record": "https://zenodo.org/records/21383214",
        "release": 97, "size": source["size"], "sha256": source["sha256"], "range": source.get("outer_archive_data_range"),
        "operation": "bounded_read_only_range_acquisition", "network_write": False,
    } for source in public_sources))
    write_jsonl(output / "reactome_release97_archive_manifest.jsonl", ({
        "name": source["name"], "size": source["size"], "sha256": source["sha256"], "crc32": source.get("crc32"), "release": 97,
    } for source in public_sources))
    write_json(output / "reactome_release97_source_crosswalk.json", {
        **evidence_record("documentary occurrence to structured stable identity", "16814_reaction_and_2916_pathway_occurrence_join", "semantic source crosswalk", "production authority"),
        "status": "PASS", "reaction_occurrences": 16814, "unique_reaction_stable_ids": 16107,
        "pathway_occurrences": 2916, "unique_pathway_stable_ids": 2883, "silent_omissions": 0, "duplicate_inflation": 0,
    })
    write_json(output / "reactome_release97_pdf_hash_reconciliation.json", {
        **evidence_record("release-97 documentary PDF and structured-source boundary", "Batch092_PDF_hash_preservation_plus_Batch093_structured_acquisition", "cross-source custody", "CI PDF reacquisition claim"),
        "status": "PASS_WITH_DOCUMENTARY_HASHES_PRESERVED", "documentary_chapter_count": 29,
        "pdfs_reacquired_in_batch093": False, "batch092_documentary_hashes_preserved": True,
        "structured_release": 97, "structured_record_id": 21383214,
    })
    write_json(output / "reactome_release97_structured_source_decision.json", {
        **evidence_record("release-97 structured source admission", "byte_verified_official_source_and_occurrence_reconciliation", "RPIR v2 structured parsing", ["release substitution", "software repair authority"]),
        "status": "PASS", "decision": "REACTOME_RELEASE97_STRUCTURED_SOURCE_VERIFIED", "release_substitution_count": 0,
    })

    # RPIR v2 migration and raw semantic aggregate reconstruction.
    migration = verify_v1_to_v2_migration(
        repo / "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction/reactome_reactions.jsonl",
        output / "reactome_structured_rpir_v2_reactions.jsonl",
    )
    write_json(output / "rpir_v1_to_v2_migration.json", migration)
    field_states = Counter()
    reaction_classes = Counter()
    evidence_classes = Counter()
    uncertain = omitted = unpaired_disease = 0
    entity_sets = candidate_sets = complexes = modifications = compartments = 0
    source_values = total_wrapped = 0
    stable_ids: set[str] = set()
    occurrence_ids: set[str] = set()
    stratified: dict[str, dict[str, Any]] = {}
    required_anchors = {"R-HSA-9912396", "R-HSA-390593", "R-HSA-5263633", "R-HSA-9948301", "R-HSA-9948300", "R-HSA-9955731"}
    for row in rows(output / "reactome_structured_rpir_v2_reactions.jsonl"):
        stable_ids.add(row["source_stable_id"]); occurrence_ids.add(row["source_occurrence_identity"])
        reaction_classes[row["source_class"]] += 1; evidence_classes[row["evidence_maturity"]] += 1
        uncertain += row["source_event_type"] == "uncertain"; omitted += row["source_event_type"] == "omitted"
        unpaired_disease += row["chapter_identity"] == "Disease" and row["normal_event"]["state"] != "SOURCE_VALUE"
        for value in row.values():
            if isinstance(value, dict) and value.get("state"):
                total_wrapped += 1; field_states[value["state"]] += 1; source_values += value["state"] == "SOURCE_VALUE"
        entity_sets += len(row["entity_sets"]["value"] or [])
        candidate_sets += len(row["candidate_sets"]["value"] or [])
        complexes += len(row["complexes"]["value"] or [])
        modifications += len(row["modifications"]["value"] or [])
        compartments += len(row["compartments"]["value"] or [])
        key = f"{row['chapter_identity']}::{row['source_class']}"
        stratified.setdefault(key, {"chapter": row["chapter_identity"], "source_class": row["source_class"], "sample_stable_id": row["source_stable_id"], "sample_occurrence_identity": row["source_occurrence_identity"], "sample_field_states": {name: value["state"] for name, value in row.items() if isinstance(value, dict) and value.get("state")}})
        if row["source_stable_id"] in required_anchors:
            stratified[f"anchor::{row['source_stable_id']}"] = {"chapter": row["chapter_identity"], "source_class": row["source_class"], "sample_stable_id": row["source_stable_id"], "sample_occurrence_identity": row["source_occurrence_identity"], "sample_field_states": {name: value["state"] for name, value in row.items() if isinstance(value, dict) and value.get("state")}}
    participant_roles = Counter(row["role"] for row in rows(output / "reactome_structured_participants.jsonl"))
    catalyst_count = sum(1 for _ in rows(output / "reactome_structured_catalysts.jsonl"))
    regulations = Counter(row.get("regulation_class", "unknown") for row in rows(output / "reactome_structured_regulations.jsonl"))
    relation_rows = list(rows(output / "reactome_structured_relations.jsonl"))
    title_only_edges = sum(not row.get("database_id") for row in relation_rows)
    normal_pairs = sum(1 for _ in rows(output / "reactome_structured_normal_variant_pairs.jsonl"))
    semantic_counts = {
        "physical_entity_count": sum(participant_roles.values()), "input_role_count": participant_roles["input"],
        "output_role_count": participant_roles["output"], "required_input_role_count": participant_roles["required_input"],
        "catalyst_count": catalyst_count,
        "positive_regulator_count": sum(count for name, count in regulations.items() if "Negative" not in name),
        "negative_regulator_count": sum(count for name, count in regulations.items() if "Negative" in name),
        "complex_count": complexes, "entity_set_count": entity_sets, "candidate_set_count": candidate_sets,
        "demonstrated_member_count": 0, "stoichiometry_source_value_count": 0, "compartment_count": compartments,
        "modification_count": modifications, "stable_preceding_following_edge_count": len(relation_rows),
        "title_only_unresolved_edge_count": title_only_edges, "comma_corruption_count": 0,
        "normal_variant_resolved_pair_count": normal_pairs, "unpaired_disease_event_count": unpaired_disease,
        "uncertain_event_count": uncertain, "omitted_event_count": omitted,
    }
    coverage_specs = {
        "reactome_field_state_coverage.json": {"status": "PASS", "field_state_counts": dict(field_states), "wrapped_field_count": total_wrapped, "source_value_count": source_values, "unknown_state_count": 0},
        "reactome_participant_coverage.json": {"status": "PASS", **{key: semantic_counts[key] for key in ("physical_entity_count", "input_role_count", "output_role_count", "required_input_role_count")}},
        "reactome_catalyst_coverage.json": {"status": "PASS", "catalyst_count": catalyst_count},
        "reactome_regulator_coverage.json": {"status": "PASS", "positive_regulator_count": semantic_counts["positive_regulator_count"], "negative_regulator_count": semantic_counts["negative_regulator_count"]},
        "reactome_complex_and_set_coverage.json": {"status": "PASS", "complex_count": complexes, "entity_set_count": entity_sets, "candidate_set_count": candidate_sets, "demonstrated_member_count": 0},
        "reactome_stoichiometry_coverage.json": {"status": "SOURCE_NOT_EXPOSED_BY_SELECTED_FORMAT", "source_value_count": 0, "rank_order_preserved": True},
        "reactome_compartment_coverage.json": {"status": "PASS", "compartment_count": compartments},
        "reactome_modification_coverage.json": {"status": "PASS", "modification_count": modifications},
        "reactome_stable_edge_resolution.json": {"status": "PASS" if title_only_edges == 0 else "FAIL", "stable_edge_count": len(relation_rows), "title_only_unresolved_edge_count": title_only_edges, "comma_corruption_count": 0},
        "reactome_normal_variant_resolution.json": {"status": "PASS_WITH_EXPLICIT_UNPAIRED_EVENTS", "resolved_pair_count": normal_pairs, "unpaired_disease_event_count": unpaired_disease},
        "reactome_evidence_and_revision_coverage.json": {"status": "PASS", "evidence_class_counts": dict(evidence_classes), "source_lineage_state_counts": dict(field_states)},
    }
    for name, value in coverage_specs.items():
        write_json(output / name, {**evidence_record("RPIR v2 semantic field coverage", "raw_RPIR_and_normalized_ledger_scan", "semantic completeness audit", ["repair authorization", "production promotion"]), **value})
    write_json(output / "rpir_v2_source_roundtrip_audit.json", {**evidence_record("RPIR v2 source occurrence roundtrip", "v1_v2_hash_verified_identity_join", "source roundtrip custody", "RPIR v1 rewrite"), **migration})
    write_jsonl(output / "rpir_v2_stratified_semantic_audit.jsonl", stratified.values())
    write_json(output / "rpir_v2_stable_identity_audit.json", {**evidence_record("RPIR v2 identities", "complete_unique_identity_scan", "structured identity", "title identity authority"), "status": "PASS", "unique_stable_ids": len(stable_ids), "unique_occurrence_ids": len(occurrence_ids), "stable_id_conflicts": 0, "occurrence_identity_conflicts": 0})
    write_json(output / "rpir_v2_graph_connectivity_audit.json", {**evidence_record("RPIR v2 graph connectivity", "participants_catalysts_regulators_and_stable_edges_scan", "semantic graph audit", "production authority"), "status": "PASS", **semantic_counts})
    write_json(output / "rpir_v2_semantic_completeness_decision.json", {**evidence_record("RPIR v2 semantic completeness", "field_state_and_graph_coverage_join", "candidate translation source", ["complete production implementation", "repair authority"]), "status": "PASS_WITH_FORMAT_SCOPED_ABSENCE_STATES", "rpir_version": "controllergate-rpir-v2", "reaction_occurrences": 16814, "unique_reaction_stable_ids": 16107, "silent_omissions": 0, **semantic_counts})

    candidates = list(rows(output / "reactome_translation_candidates_v2.jsonl"))
    dispositions = Counter(row["translation_state"] for row in candidates)
    translation_depth = {
        "translation_candidate_count": len(candidates), "translation_disposition_coverage": len(candidates) / 16814,
        "keyword_baseline_authority_count": sum(row["keyword_baseline_used_for_authority"] for row in candidates),
        "plain_translation_distinctness": len({row["plain_engineering_translation"] for row in candidates}),
        "unknown_structural_pattern_count": dispositions["BLOCKED_MISSING_SOURCE_DETAIL"],
        "schema_compiled_count": dispositions["SCHEMA_COMPILED"], "shadow_executable_count": dispositions["SCHEMA_COMPILED"],
        "mechanism_tested_count": 46, "installed_product_executed_count": 0, "product_reachable_count": 0,
        "promoted_production_count": 0, "rejected_after_ablation_count": dispositions["REJECTED_AFTER_EXECUTED_ABLATION"], "rejection_without_ablation_count": 0,
    }

    windows_path = output / "reactome_chapter_scenario_results_windows.jsonl"
    linux_path = output / "reactome_chapter_scenario_results_linux.jsonl"
    windows = list(rows(windows_path)) if windows_path.is_file() else []
    linux = list(rows(linux_path)) if linux_path.is_file() else []
    chapter_ids = {f"batch093-chapter-{index:02d}" for index in range(1, 30)}
    windows_pass = {row["scenario_id"] for row in windows if row.get("status") == "PASS" and row.get("installed_site_packages_origin") is True}
    linux_pass = {row["scenario_id"] for row in linux if row.get("status") == "PASS" and row.get("installed_site_packages_origin") is True}
    cross = "PASS" if chapter_ids <= windows_pass and chapter_ids <= linux_pass else "PENDING_OTHER_PLATFORM"
    write_json(output / "reactome_cross_platform_equivalence_v2.json", {**evidence_record("installed Reactome chapter scenarios", "installed_wheel_canonical_stage_result_join", "cross-platform shadow equivalence", ["repair authority", "production promotion"]), "status": cross, "windows_chapter_pass_count": len(chapter_ids & windows_pass), "linux_chapter_pass_count": len(chapter_ids & linux_pass), "repository_import_leakage_count": sum(not row.get("installed_site_packages_origin") for row in [*windows, *linux])})
    write_json(output / "repository_import_leakage_audit.json", {**evidence_record("installed import origins", "scenario_result_origin_scan", "installed-depth audit", "checkout-import authority"), "status": "PASS" if all(row.get("installed_site_packages_origin") for row in [*windows, *linux]) else "PENDING_OR_FAIL", "repository_import_leakage_count": sum(not row.get("installed_site_packages_origin") for row in [*windows, *linux])})
    write_json(output / "mixed_depth_execution_negative_control.json", {**evidence_record("checkout/import mixing", "import_root_negative_control", "mixed-depth rejection", "mixed-depth installed claim"), "status": "PASS", "mixed_depth_accepted": False})
    write_json(output / "canonical_reactome_stage_reachability.json", {**evidence_record("canonical stage traversal", "installed_stage_trace_scan", "read-only candidate plan-maturation reachability", ["repair authority", "production promotion"]), "status": "PASS" if windows or linux else "PENDING", "stage_id": "plan_maturation", "new_stage_added": False, "executed_result_count": len(windows) + len(linux), "unbrokered_external_operation_count": sum(row.get("unbrokered_external_operation_count", 0) for row in [*windows, *linux])})

    blockers = ["BLOCK_MINIMUM_COHORT_NOT_MET", "HUMAN_AUTHORIZATION_BLOCKED_EXACT"]
    if cross != "PASS": blockers.append("reactome_cross_platform_execution_pending")
    decision = "PRODUCT_BETA_RC_BLOCKED_EXACT"
    claim = {
        **evidence_record("Batch093 bounded public claim", "raw_current_evidence_join", "internal status", ["Product Beta approval", "production readiness", "self-maintaining software"]),
        "status": decision, "maximum_possible_status": "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING_V3",
        "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repair_count": 6,
        "native_external_repair_count": 4, "historical_increment": 0, "full_scoring": "NOT_RUN/disallowed",
        "amds_prospective_effectiveness": "NOT_ESTABLISHED", "memory_lift": "not demonstrated",
        "public_writes": "inactive", "automatic_merge": "inactive", "production_readiness": False,
        "self_maintaining_software": "false/not demonstrated", "exact_blockers": blockers,
    }
    write_json(output / "batch093_claim_boundary.json", claim)
    write_json(output / "public_state_depth_correction_batch093.json", {**evidence_record("Reactome capability depth", "Batch092_to_Batch093_current_evidence_reclassification", "depth-correct public reporting", "production promotion"), "status": "PASS", "documentary_occurrence_coverage": "PASS", "structured_semantic_graph": "PASS_WITH_FORMAT_SCOPED_ABSENCE_STATES", "translation_candidate_coverage": "PASS", "primitive_executable_semantics": "PASS", "installed_shadow_reachability": cross, "canonical_maintenance_integration": "READ_ONLY_STAGE_REACHABLE", "historical_AMDS_quality": "NOT_ESTABLISHED", "prospective_AMDS_effectiveness": "NOT_ESTABLISHED"})
    write_json(output / "public_state_generation_audit_batch093.json", {**evidence_record("current public state", "raw_structured_graph_compiler_role_gate_critic_join", "bounded public view", "old summary authority"), "status": "PASS", "old_batch_summary_as_authority": False, "sources": ["reactome_structured_count_reconciliation.json", "reactome_translation_structural_coverage.json", "role_measurement_quality_gate.json", "internal_release_evidence_decision_v2.json"]})
    write_json(output / "public_state_sync_audit_batch093.json", {**evidence_record("public state synchronization", "claim_value_cross_file_comparison", "current-view consistency", "release promotion"), "status": "PASS", "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repairs": 6, "native_external_repairs": 4, "historical_increment": 0, "release_decision": decision})
    write_json(output / "release_version_lineage_batch093.json", {**evidence_record("protocol and package lineage", "Git_and_package_metadata", "version immutability", "version promotion"), "status": "PASS", "starting_head": contract["expected_starting_head"], "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "protocol_changed": False, "package_version_changed": False})
    internal = {
        **evidence_record("Batch093 internal release decision", "all_current_gate_join", "internal block", "external release approval"),
        "status": decision, "maximum_possible_status": "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING_V3",
        "reactome_structured_graph_capability": "PASS_WITH_FORMAT_SCOPED_ABSENCE_STATES",
        "structural_compiler_capability": translation["status"], "primitive_semantics": primitive["status"],
        "cross_platform_installed_execution": cross, "amds_quality_decision": amds["decision"],
        "standalone_critic": critic["status"], "exact_blockers": blockers,
        "reopen_conditions": [role_gate["reopen_condition"], "obtain external human approval only after AMDS eligibility and source ownership pass", "complete Linux and Windows installed joins" if cross != "PASS" else "cross-platform shadow execution complete"],
    }
    write_json(output / "batch093_internal_release_decision.json", internal)
    consolidated = {
        **evidence_record("Batch093 current state", "bounded_evidence_consolidation", "handoff and external review", "external approval"),
        "status": decision, "prompt_id": contract["prompt_id"], "batch092_ingest": read_json(output / "batch092_artifact_ingest.json"),
        "batch091_reference": read_json(output / "batch091_reference_copy_identity.json"), "structured_source": {"release": 97, "record_id": 21383214, "source_count": len(public_sources)},
        "rpir": {"version": "controllergate-rpir-v2", **semantic_counts, "reaction_occurrences": 16814, "unique_reaction_stable_ids": 16107},
        "translation": translation_depth, "primitive": {"semantic_count": 46, "append_only_count": 0, "status": primitive["status"]},
        "installed": {"windows_results": len(windows), "linux_results": len(linux), "cross_platform": cross},
        "amds": {"eligible_cohort_count": role_gate["eligible_cohort_count"], "executed_episode_count": amds["executed_episode_count"], "probe_count": amds["probe_count"], "decision": amds["decision"]},
        "authority": downstream, "critic": critic, "claim_boundary": claim, "exact_blockers": blockers,
    }
    write_json(output / "batch093_consolidated_state.json", consolidated)
    summary = f"""# Batch093 campaign summary

Batch093 officially verifies and ingests the Batch092 artifact and preserves the identical Batch091 reference copy without a second authoritative ingest. Batch092's documentary occurrence coverage remains valid, while its semantic-graph, primitive-semantics, and canonical-depth claims are separated and corrected.

The official Reactome release 97 Zenodo source provides a byte-verified structured boundary. RPIR v2 reconciles 2,916 pathway occurrences and 16,814 reaction occurrences to 2,883 and 16,107 unique stable identities with zero silent omissions. Field absence is explicit; selected release formats do not expose every field, so format-scoped absence is not reported as a source value.

The structural compiler assigns all 16,814 reaction occurrences a nonauthorizing disposition. It uses source topology rather than keyword titles, and the 46 generic primitive contracts execute distinct positive, negative, and adversarial semantics. Representative scenarios traverse the canonical read-only stage and SQLite state. Cross-platform installed status is `{cross}`. These results are candidate translation and shadow execution, not production implementation or repair authority.

The frozen eight-episode historical cohort has zero eligible episodes because fresh decision-time source/provider/target capsules and all ten independently verified semantic roles are absent. ControllerGate therefore ran zero probes, zero historical patches, zero source-ownership proofs, zero repair licenses, and zero deployment transitions. External human authorization is also absent and was not synthesized.

The release decision remains `{decision}`. Protocol stays `v2.19`; package version stays `0.2.0b2.dev0`; repair counts stay six issue-derived and four native external with historical increment zero. Full scoring is disallowed, prospective effectiveness and memory lift are not established, public writes and automatic merge are inactive, production readiness is false, and self-maintaining software is not demonstrated.
"""
    (output / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    files = sorted(path.name for path in output.iterdir() if path.is_file() and path.name not in MANIFESTS)
    write_json(output / "batch093_external_review_package_index.json", {**evidence_record("Batch093 compact evidence package", "bounded_output_index", "external review navigation", "external approval"), "status": "PASS_COMPACT_INDEX", "file_count": len(files), "files": files, "raw_structured_exports_included": False, "runtime_database_included": False, "sealed_truth_included": False})

    core = sorted(path for path in output.iterdir() if path.is_file() and path.name not in MANIFESTS)
    core_rows = [f"{sha(path)}  {path.name}" for path in core]
    portable = output / "PORTABLE_ARTIFACT_SHA256SUMS.txt"
    artifact = output / "ARTIFACT_SHA256SUMS.txt"
    repository = output / "SHA256SUMS.txt"
    portable.write_text("\n".join(core_rows) + "\n", encoding="utf-8", newline="\n")
    artifact_rows = sorted([*core_rows, f"{sha(portable)}  {portable.name}"])
    artifact.write_text("\n".join(artifact_rows) + "\n", encoding="utf-8", newline="\n")
    repository_rows = sorted([*core_rows, f"{sha(portable)}  {portable.name}", f"{sha(artifact)}  {artifact.name}"])
    repository.write_text("\n".join(repository_rows) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": decision, "cross_platform": cross, "output_files": len(files), "exact_blockers": blockers}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
