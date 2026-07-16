from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


OUTPUT_NAME = "post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure"
MANIFESTS = ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=f"outputs/{OUTPUT_NAME}")
    parser.add_argument("--require-cross-platform", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    failures: list[str] = []
    ingest = read_json(output / "batch092_artifact_ingest.json")
    reference = read_json(output / "batch091_reference_copy_identity.json")
    expected_red = read_json(output / "batch093_pre_fix_structured_rpir_and_role_cohort_expected_failure.json")
    source = read_json(output / "reactome_release97_structured_source_manifest.json")
    source_decision = read_json(output / "reactome_release97_structured_source_decision.json")
    structured = read_json(output / "reactome_structured_count_reconciliation.json")
    field_state = read_json(output / "reactome_field_state_coverage.json")
    participants = read_json(output / "reactome_participant_coverage.json")
    edges = read_json(output / "reactome_stable_edge_resolution.json")
    migration = read_json(output / "rpir_v1_to_v2_migration.json")
    semantic = read_json(output / "rpir_v2_semantic_completeness_decision.json")
    translation = read_json(output / "reactome_translation_structural_coverage.json")
    distinctness = read_json(output / "reactome_translation_distinctness_audit.json")
    firewall = read_json(output / "reactome_translation_authority_firewall_v2.json")
    primitive = read_json(output / "primitive_execution_coverage_v2.json")
    primitive_distinct = read_json(output / "primitive_semantic_distinctness_audit.json")
    source_binding = read_json(output / "reactome_source_to_scenario_traceability.json")
    cross = read_json(output / "reactome_cross_platform_equivalence_v2.json")
    reachability = read_json(output / "canonical_reactome_stage_reachability.json")
    role = read_json(output / "role_measurement_quality_gate.json")
    future_scan = read_json(output / "future_and_outcome_evidence_scan.json")
    amds = read_json(output / "amds_historical_quality_gate_v2.json")
    downstream = read_json(output / "batch093_downstream_gate_status.json")
    approval = read_json(output / "external_human_authorization_receipt.json")
    critic = read_json(output / "internal_release_evidence_decision_v2.json")
    mutations = read_json(output / "resigned_raw_semantic_mutation_results_v2.json")
    decision = read_json(output / "batch093_internal_release_decision.json")
    claim = read_json(output / "batch093_claim_boundary.json")

    require(ingest["status"] == "PASS" and ingest["artifact"]["artifact_id"] == 8358022260, "Batch092 artifact ingest failed", failures)
    require(ingest["artifact"]["sha256"] == "bd3f1de0e64c8d2f8de5d76eb78bc5179543239b16b47a3b594214ac2a3443c1", "Batch092 artifact identity mismatch", failures)
    require(reference["status"] == "PASS" and reference["classification"] == "IDENTICAL_REFERENCE_COPY" and reference["second_authoritative_ingest_performed"] is False, "Batch091 reference boundary failed", failures)
    require(expected_red["status"] == "BATCH093_PRE_FIX_AUDIT_FAIL_EXPECTED" and expected_red["finding_count"] >= 27, "expected-red Batch093 review missing", failures)
    require(source["status"] == "PASS" and source["release"] == 97 and source["zenodo_record_id"] == 21383214, "release-97 structured custody failed", failures)
    require(source_decision["decision"] == "REACTOME_RELEASE97_STRUCTURED_SOURCE_VERIFIED" and source_decision["release_substitution_count"] == 0, "structured source admission failed", failures)
    require(structured["status"] == "PASS" and structured["reaction_occurrence_count"] == 16814 and structured["pathway_occurrence_count"] == 2916, "structured occurrence counts failed", failures)
    require(structured["unique_reaction_stable_id_count"] == 16107 and structured["silent_omission_count"] == 0 and structured["duplicate_inflation_count"] == 0, "stable identity reconciliation failed", failures)
    expected_states = {"SOURCE_VALUE", "SOURCE_EXPLICITLY_EMPTY", "SOURCE_NOT_APPLICABLE", "SOURCE_NOT_EXPOSED_BY_FORMAT", "PARSER_FAILED", "UNRESOLVED_REFERENCE"}
    require(set(field_state["field_state_counts"]) <= expected_states and field_state["unknown_state_count"] == 0, "RPIR field-state vocabulary or completeness failed", failures)
    require(participants["physical_entity_count"] > 0 and participants["input_role_count"] > 0 and participants["output_role_count"] > 0, "structured participants missing", failures)
    require(edges["status"] == "PASS" and edges["title_only_unresolved_edge_count"] == 0 and edges["comma_corruption_count"] == 0, "stable edge resolution failed", failures)
    require(migration["status"] == "PASS" and migration["idempotent"] is True and migration["missing_count"] == 0, "RPIR v1-to-v2 migration failed", failures)
    require(semantic["status"] == "PASS_WITH_FORMAT_SCOPED_ABSENCE_STATES", "RPIR v2 semantic completeness boundary failed", failures)
    require(translation["status"] == "PASS" and translation["translation_candidate_count"] == 16814 and translation["silent_omission_count"] == 0, "structural translation coverage failed", failures)
    require(translation["automatic_rejection_count"] == 0 and translation["rejection_without_ablation_count"] == 0, "unauthorized translation rejection occurred", failures)
    require(distinctness["five_sentence_template_count"] == 0 and distinctness["distinct_source_graph_hash_count"] == 16107, "translation distinctness failed", failures)
    require(firewall["keyword_authority_count"] == 0 and firewall["repair_authority_count"] == 0 and firewall["production_promotion_count"] == 0, "translation authority firewall failed", failures)
    require(primitive["status"] == "PASS" and primitive["executed"] == primitive["expected"] == 46, "primitive execution incomplete", failures)
    require(primitive_distinct["status"] == "PASS" and primitive_distinct["append_only_primitive_count"] == 0, "primitive distinctness failed", failures)
    require(source_binding["status"] == "PASS" and source_binding["chapter_count"] == 29, "chapter source binding failed", failures)
    windows = rows(output / "reactome_chapter_scenario_results_windows.jsonl") if (output / "reactome_chapter_scenario_results_windows.jsonl").is_file() else []
    linux = rows(output / "reactome_chapter_scenario_results_linux.jsonl") if (output / "reactome_chapter_scenario_results_linux.jsonl").is_file() else []
    require(len(windows) == 30 and all(row["status"] == "PASS" and row["installed_site_packages_origin"] is True for row in windows), "Windows installed canonical scenarios failed", failures)
    if args.require_cross_platform:
        require(len(linux) == 30 and all(row["status"] == "PASS" and row["installed_site_packages_origin"] is True for row in linux), "Linux installed canonical scenarios failed", failures)
        require(cross["status"] == "PASS", "cross-platform equivalence failed", failures)
    else:
        require(cross["status"] in {"PASS", "PENDING_OTHER_PLATFORM"}, "cross-platform status invalid", failures)
    require(reachability["stage_id"] == "plan_maturation" and reachability["new_stage_added"] is False and reachability["unbrokered_external_operation_count"] == 0, "canonical stage reachability failed", failures)
    require(role["status"] == "BLOCK" and role["eligible_cohort_count"] == 0 and role["probe_execution_count"] == 0, "AMDS cohort was not honestly blocked", failures)
    admitted_future_hits = sum(bool(row.get("forbidden_pattern_hits")) and row.get("admitted_to_batch093_builder") is True for row in future_scan["records"])
    require(admitted_future_hits == 0, "future/outcome decision-time contamination found", failures)
    require(amds["executed_episode_count"] == 0 and amds["probe_count"] == 0 and amds["actual_baselines"] == "NOT_RUN", "AMDS executed after cohort block", failures)
    require(downstream["patch_operation_count"] == 0 and downstream["historical_count_increment"] == 0 and downstream["package_slot_switch"] == "NOT_RUN", "downstream actuation ran after block", failures)
    require(approval["status"] == "HUMAN_AUTHORIZATION_BLOCKED_EXACT" and approval["repository_generated_approval"] is False, "human authorization was synthesized", failures)
    require(critic["status"] == "PASS_INTERNAL_CRITIC_WITH_RELEASE_BLOCKERS" and critic["finding_count"] > 0, "standalone critic failed or hid blockers", failures)
    require(mutations["status"] == "PASS" and mutations["executed"] == mutations["rejected"], "physical semantic mutation campaign failed", failures)
    require(decision["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT" and claim["status"] == "PRODUCT_BETA_RC_BLOCKED_EXACT", "release boundary overclaimed", failures)
    require(claim["protocol"] == "v2.19" and claim["package_version"] == "0.2.0b2.dev0", "protocol or package changed", failures)
    require(claim["issue_derived_repair_count"] == 6 and claim["native_external_repair_count"] == 4 and claim["historical_increment"] == 0, "repair counts changed", failures)
    require(claim["full_scoring"] == "NOT_RUN/disallowed" and claim["production_readiness"] is False and claim["self_maintaining_software"] == "false/not demonstrated", "claim boundary overclaimed", failures)

    for manifest_name in MANIFESTS:
        manifest_rows = [line for line in (output / manifest_name).read_text(encoding="utf-8").splitlines() if line]
        names = [line.split("  ", 1)[1] for line in manifest_rows]
        require(manifest_name not in names, f"{manifest_name} contains an invalid self entry", failures)
        for line in manifest_rows:
            expected, name = line.split("  ", 1)
            require((output / name).is_file() and sha(output / name) == expected, f"manifest mismatch: {manifest_name}:{name}", failures)
    forbidden_suffixes = {".zip", ".pdf", ".whl", ".pyc", ".tar", ".tgz", ".sqlite", ".sqlite3", ".owl"}
    require(not [path for path in output.rglob("*") if path.is_file() and path.suffix.lower() in forbidden_suffixes], "forbidden raw/runtime payload in main output", failures)
    require((output / "reactome_translation_candidates_v2.jsonl").stat().st_size < 100_000_000, "candidate ledger exceeds GitHub per-file boundary", failures)
    result = {
        "status": "PASS" if not failures else "FAIL", "producer": "scripts/audit_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure.py",
        "execution_depth": "complete Batch093 evidence, authority, manifest, and claim audit", "semantic_scope": "Batch093 internal evidence",
        "authority_allowed": "internal audit", "authority_forbidden": "external release approval", "require_cross_platform": args.require_cross_platform,
        "failure_count": len(failures), "failures": failures,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
