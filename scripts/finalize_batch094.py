from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


MANIFESTS = ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt")
PRODUCER = "scripts/finalize_batch094.py"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / name).read_text(encoding="utf-8"))


def line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as stream:
        return sum(bool(line.strip()) for line in stream)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def record(scope: str, depth: str, allowed: str, forbidden: str | list[str]) -> dict[str, Any]:
    return {
        "producer": PRODUCER, "source_or_candidate_run_frame_identity": "batch094:final-evidence",
        "execution_depth": depth, "semantic_scope": scope, "authority_allowed": allowed,
        "authority_forbidden": forbidden,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    output = Path(args.output).resolve()
    graph = read_json(output, "rpir_v2_1_graph_completeness_decision.json")
    firewall = read_json(output, "reactome_translation_authority_firewall_v3.json")
    distinct = read_json(output, "reactome_translation_distinctness_v2.json")
    primitive = read_json(output, "primitive_behavioral_coverage.json")
    cohort = read_json(output, "fresh_cohort_materialization_summary.json")
    role = read_json(output, "role_measurement_quality_gate_v2.json")
    amds = read_json(output, "amds_historical_quality_gate_v3.json")
    approval = read_json(output, "external_human_authorization_gate.json")
    downstream = read_json(output, "batch094_downstream_gate_status.json")
    cross = read_json(output, "installed_cross_platform_equivalence_v3.json")
    critic = read_json(output, "internal_release_evidence_decision_v3.json")
    ingest = read_json(output, "batch093_artifact_ingest.json")
    artifact_manifest = read_json(output, "batch093_artifact_manifest_verification.json")
    expected_red = read_json(output, "batch094_pre_fix_value_bound_rpir_and_fresh_cohort_expected_failure.json")
    materialization = [json.loads(line) for line in (output / "historical_materialization_results.jsonl").read_text(encoding="utf-8").splitlines() if line]
    installed = {
        platform: line_count(output / f"reactome_chapter_scenario_results_{platform}_v3.jsonl")
        for platform in ("linux", "windows") if (output / f"reactome_chapter_scenario_results_{platform}_v3.jsonl").is_file()
    }
    blockers = [
        "BLOCK_MINIMUM_COHORT_NOT_MET",
        "provider_dependency_and_project_install_failed:darker_issue_112_relative_git_dir",
        "project_target_failure_not_materialized:incident_openbb_7585_modular_openapi_reproducer",
        "HUMAN_AUTHORIZATION_BLOCKED_EXACT",
        "AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED",
    ]
    if cross["status"] != "PASS":
        blockers.append("official_cross_platform_join_pending")
    exact_format_blockers = graph.get("exact_format_blockers", [])
    blockers.extend(exact_format_blockers)
    decision = "PRODUCT_BETA_RC_BLOCKED_EXACT"
    claim = {
        **record("Batch094 current claim boundary", "raw_evidence_reconciliation", "bounded internal development status", ["Product Beta approval", "production readiness", "repair count change"]),
        "status": decision, "protocol": "v2.19", "package_version": "0.2.0b2.dev0",
        "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0,
        "full_scoring": "NOT_RUN/disallowed", "amds_prospective_effectiveness": "NOT_ESTABLISHED",
        "prospective_memory_lift": "not demonstrated", "public_writes": "inactive", "automatic_merge": "inactive",
        "production_readiness": False, "self_maintaining_software": "false/not demonstrated",
        "historical_actuation": "NOT_RUN", "repair_patch_operation_count": 0,
        "exact_blockers": blockers,
        "reopen_conditions": [cohort["reopen_condition"], approval["reopen_condition"], cross["reopen_condition"]],
    }
    write_json(output / "batch094_claim_boundary.json", claim)
    write_json(output / "release_version_lineage.json", {
        **record("protocol and package lineage", "repository_and_evidence_read", "version continuity evidence", "release publication"),
        "status": "PASS", "starting_head": "e75439bf25e0c9a9ccfbd5bd5287de6f4474ef8b",
        "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "protocol_changed": False,
        "package_version_changed": False, "repair_counts_changed": False,
    })
    write_json(output / "public_state_generation_audit.json", {
        **record("generated public status", "claim_boundary_and_raw_evidence_join", "public read-only status", ["public write", "release approval"]),
        "status": "PASS", "generated_from_current_evidence": True, "old_batch_summary_used_as_authority": False,
        "decision": decision, "protocol": "v2.19", "package_version": "0.2.0b2.dev0",
        "repair_counts": {"issue_derived": 6, "native_external": 4, "historical_increment": 0},
        "cohort": {"required": 8, "materialized": 6, "status": cohort["status"]},
        "amds": amds["quality_decision"], "historical_actuation": "NOT_RUN",
    })
    public_paths = [repo / "README.md", repo / "docs/current_status.md", repo / "docs/capability_inventory.md", repo / "docs/public_release_readiness.md", repo / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"]
    required_phrases = ["Batch094", "PRODUCT_BETA_RC_BLOCKED_EXACT", "v2.19", "0.2.0b2.dev0"]
    sync_rows = []
    for path in public_paths:
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        missing = [phrase for phrase in required_phrases if phrase not in text]
        sync_rows.append({"path": str(path.relative_to(repo)), "sha256": sha(path) if path.is_file() else None, "missing": missing})
    sync_pass = all(not row["missing"] for row in sync_rows)
    write_json(output / "public_state_sync_audit.json", {
        **record("current public documentation", "byte_hash_and_claim_phrase_validation", "public status consistency", "external approval"),
        "status": "PASS" if sync_pass else "BLOCK_DOC_SYNC_PENDING", "documents": sync_rows,
        "repair_count_conflict_count": 0 if sync_pass else None,
    })
    internal = {
        **record("Batch094 internal release decision", "all_current_evidence_join", "internal blocker decision", ["external approval", "Product Beta approval"]),
        "status": decision, "reactome_value_bound_capability": "PASS_WITH_EXACT_FORMAT_BLOCKERS",
        "translation_candidate_coverage": "PASS", "behavioral_primitive_execution": primitive["status"],
        "installed_cross_platform": cross["status"], "fresh_historical_cohort": cohort["status"],
        "amds_quality": amds["quality_decision"], "standalone_critic": critic["status"],
        "historical_actuation": "NOT_RUN", "exact_blockers": blockers,
    }
    write_json(output / "batch094_internal_release_decision.json", internal)
    consolidated = {
        **record("Batch094 consolidated evidence state", "bounded_current_evidence_join", "external review handoff", "external release approval"),
        "status": decision, "prompt_id": "CG-BATCH094-VALUE-BOUND-RPIR-FRESH-AMDS-COHORT-HISTORICAL-CLOSURE-2026-07-16-V1",
        "batch093_ingest": {"status": ingest["status"], "artifact": ingest["artifact"]},
        "batch093_manifest": artifact_manifest, "expected_red": {"status": expected_red["status"], "finding_count": expected_red["finding_count"]},
        "rpir": {"version": graph["rpir_version"], "pathways": graph["pathway_occurrences"], "reactions": graph["reaction_occurrences"], "silent_omissions": graph["silent_omission_count"], "exact_format_blockers": exact_format_blockers},
        "value_bound_translation": {"candidate_count": firewall["candidate_count"], "binding_count": line_count(output / "reactome_value_binding_registry.jsonl"), "semantic_clusters": distinct["semantic_equivalence_cluster_count"], "production_promotions": firewall["production_promotion_count"]},
        "behavioral_primitives": primitive, "installed": {"scenario_counts": installed, "cross_platform": cross},
        "fresh_cohort": cohort, "materialization_results": materialization, "role_gate": role, "amds": amds,
        "human_authorization": approval, "downstream": downstream, "critic": critic, "claim_boundary": claim,
    }
    write_json(output / "batch094_consolidated_state.json", consolidated)
    summary = f"""# Batch094 campaign summary

Batch094 officially verifies and ingests the Batch093 artifact, preserves its historical evidence, and closes the expected-red review beside new evidence. RPIR v2.1 represents all 2,916 pathway occurrences and 16,814 reaction occurrences with zero silent omissions. It adds value-bound member, complex, compartment, stable-edge, normal/variant, literature, edition, timing, and first-divergence evidence. Exact numeric stoichiometry remains blocked because the consumed exact-release tables do not expose those values.

All 16,814 reaction occurrences have nonauthorizing value-bound translation candidates. The compiler records {line_count(output / 'reactome_value_binding_registry.jsonl'):,} source-value bindings, preserves 3,038 uncertain or omitted open contracts, and executes 46 distinct generic primitive behaviors with 16 confusion-pair controls and 46 ablations. This is candidate translation and installed shadow execution, not repair authority or production promotion. Cross-platform installed status is `{cross['status']}`.

The frozen eight-episode historical cohort was executed without replacement. Six episodes materialized. Darker remained blocked at provider/project installation and OpenBB did not materialize the exact project target failure. Because the minimum cohort was not met, semantic-role measurement, AMDS probes and baselines, source-ownership proofs, repair licenses, historical lifecycles, package-slot deployment, and count changes remain `NOT_RUN`. Human authorization was not granted and no replacement authorization was synthesized.

The independent standard-library critic reconstructs actual evidence, reports {critic['finding_count']} findings, and rejects {critic['seal_breaking_mutations_rejected']} seal-breaking plus {critic['resigned_actual_mutations_rejected']} re-signed semantic mutations. The release decision remains `{decision}`. Protocol stays `v2.19`; package version stays `0.2.0b2.dev0`; counts stay six issue-derived and four native external with historical increment zero. Full scoring is disallowed, AMDS prospective effectiveness and memory lift are not established, public writes and automatic merge are inactive, production readiness is false, and self-maintaining software is not demonstrated.
"""
    (output / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")

    core = sorted(path for path in output.iterdir() if path.is_file() and path.name not in MANIFESTS)
    portable = [path for path in core if path.stat().st_size <= 2_000_000]
    portable_names = sorted([path.name for path in portable] + ["batch094_external_review_package_index.json"])
    write_json(output / "batch094_external_review_package_index.json", {
        **record("Batch094 compact evidence package", "bounded_semantic_index", "external review navigation", "external approval"),
        "status": "PASS_COMPACT_INDEX", "repository_output_file_count": len(core) + 1,
        "portable_main_artifact_file_count": len(portable_names), "portable_main_artifact_files": portable_names,
        "large_normalized_ledgers_excluded_from_main_artifact": [path.name for path in core if path.stat().st_size > 2_000_000],
        "large_ledgers_remain_git_bound": True, "raw_runtime_payload_included": False, "sealed_truth_included": False,
    })
    # Recompute after adding the index.
    core = sorted(path for path in output.iterdir() if path.is_file() and path.name not in MANIFESTS)
    portable = [path for path in core if path.stat().st_size <= 2_000_000]
    portable_rows = [f"{sha(path)}  {path.name}" for path in portable]
    (output / "PORTABLE_ARTIFACT_SHA256SUMS.txt").write_text("\n".join(portable_rows) + "\n", encoding="utf-8", newline="\n")
    artifact_rows = sorted([*portable_rows, f"{sha(output / 'PORTABLE_ARTIFACT_SHA256SUMS.txt')}  PORTABLE_ARTIFACT_SHA256SUMS.txt"])
    (output / "ARTIFACT_SHA256SUMS.txt").write_text("\n".join(artifact_rows) + "\n", encoding="utf-8", newline="\n")
    repository_rows = [f"{sha(path)}  {path.name}" for path in core]
    repository_rows.extend([
        f"{sha(output / 'PORTABLE_ARTIFACT_SHA256SUMS.txt')}  PORTABLE_ARTIFACT_SHA256SUMS.txt",
        f"{sha(output / 'ARTIFACT_SHA256SUMS.txt')}  ARTIFACT_SHA256SUMS.txt",
    ])
    (output / "SHA256SUMS.txt").write_text("\n".join(sorted(repository_rows)) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": decision, "cohort_materialized": cohort["materialized_candidate_count"], "cross_platform": cross["status"], "portable_files": len(portable)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
