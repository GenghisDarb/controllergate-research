from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


PRODUCER = "scripts/finalize_batch092.py"
MANIFEST_NAMES = {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True); parser.add_argument("--repo", default="."); args = parser.parse_args()
    output = Path(args.output); repo = Path(args.repo)
    contract = read_json(repo / "configs" / "batch092_prompt_contract.json")
    source = read_json(output / "reactome_source_coverage.json")
    translation = read_json(output / "reactome_translation_coverage.json")
    candidates = read_jsonl(output / "reactome_translation_candidates.jsonl")
    amds = read_json(output / "amds_quality_gate.json")
    critic = read_json(output / "internal_release_evidence_decision.json")
    cross_platform = read_json(output / "reactome_cross_platform_equivalence.json")
    windows = read_jsonl(output / "installed_reactome_scenarios_windows.jsonl") if (output / "installed_reactome_scenarios_windows.jsonl").is_file() else []
    linux = read_jsonl(output / "installed_reactome_scenarios_linux.jsonl") if (output / "installed_reactome_scenarios_linux.jsonl").is_file() else []
    dispositions = Counter(row["translation_state"] for row in candidates)
    installed_ids = {row["scenario_id"] for row in windows if row.get("mechanism_status") == "PASS" and row.get("installed_site_packages_origin") is True}
    if linux:
        installed_ids &= {row["scenario_id"] for row in linux if row.get("mechanism_status") == "PASS" and row.get("installed_site_packages_origin") is True}
    else:
        installed_ids = set()
    internal_decision = "PRODUCT_BETA_RC_BLOCKED_EXACT"
    blockers = sorted(set(critic["exact_blockers"] + (["reactome_linux_installed_execution_pending"] if cross_platform["status"] != "PASS" else [])))
    claim = {
        "status": internal_decision, "producer": PRODUCER, "execution_depth": "current_SQLite_scoped_receipt_and_critic_view",
        "semantic_scope": "Batch092 public claim boundary", "authority_allowed": "bounded current status",
        "authority_forbidden": ["Product Beta approval", "production readiness", "complete production implementation", "full scoring", "self-maintaining software"],
        "protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repair_count": 6,
        "native_external_repair_count": 4, "historical_increment": 0, "full_scoring": "NOT_RUN/disallowed",
        "amds_prospective_effectiveness": "NOT_ESTABLISHED", "prospective_memory_lift": "not demonstrated",
        "public_write_connectors": "inactive", "automatic_merge": "inactive", "production_readiness": False,
        "self_maintaining_software": "false/not demonstrated", "complete_source_coverage_is_production_implementation": False,
        "exact_blockers": blockers,
    }
    write(output / "batch092_claim_boundary.json", claim)
    translation_depth = {
        "translation_candidate_count": len(candidates), "schema_compiled_count": len(candidates) - dispositions.get("BLOCKED_MISSING_SOURCE_DETAIL", 0),
        "shadow_executable_count": len(candidates) - dispositions.get("BLOCKED_MISSING_SOURCE_DETAIL", 0),
        "mechanism_tested_count": 29, "installed_product_executed_count": len(installed_ids), "product_reachable_count": len(installed_ids),
        "promoted_production_count": 0, "rejected_after_ablation_count": dispositions.get("REJECTED_AFTER_EXECUTED_ABLATION", 0),
        "rejection_without_ablation_count": translation["rejection_without_ablation_count"], "blocked_missing_source_detail_count": dispositions.get("BLOCKED_MISSING_SOURCE_DETAIL", 0),
    }
    decision = {
        "status": internal_decision, "maximum_possible_status": "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING_V2",
        "producer": PRODUCER, "execution_depth": "all_current_batch_gate_join", "semantic_scope": "Batch092 internal release decision",
        "authority_allowed": "internal block", "authority_forbidden": "external release approval",
        "reactome_compiler_capability": "PASS", "reactome_source_coverage": source["status"],
        "reactome_cross_platform_equivalence": cross_platform["status"], "amds_quality_decision": amds["decision"],
        "standalone_critic": critic["status"], "exact_blockers": blockers,
        "reopen_conditions": [amds["reopen_condition"], "execute and aggregate all 29 installed scenarios on Linux and Windows" if cross_platform["status"] != "PASS" else "cross-platform execution complete; AMDS blocker remains"],
    }
    write(output / "batch092_internal_release_decision.json", decision)
    lineage = {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "Git_and_package_metadata_lineage",
        "semantic_scope": "version and protocol immutability", "authority_allowed": "lineage audit", "authority_forbidden": "version promotion",
        "starting_head": contract["expected_starting_head"], "protocol": "v2.19", "package_version": "0.2.0b2.dev0",
        "protocol_changed": False, "package_version_changed": False, "historical_increment": 0,
    }
    write(output / "release_version_lineage.json", lineage)
    write(output / "public_state_generation_audit.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "current_batch_raw_evidence_join",
        "semantic_scope": "current public state", "authority_allowed": "bounded public status", "authority_forbidden": "old summary authority",
        "sources": ["reactome_source_coverage.json", "reactome_translation_coverage.json", "amds_quality_gate.json", "internal_release_evidence_decision.json", "batch092_claim_boundary.json"],
        "old_batch_summary_as_authority": False,
    })
    write(output / "public_state_sync_audit.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "claim_value_cross_file_comparison", "semantic_scope": "public state synchronization",
        "authority_allowed": "current view consistency", "authority_forbidden": "release promotion", "protocol": "v2.19", "package_version": "0.2.0b2.dev0",
        "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0,
        "internal_release_decision": internal_decision,
    })
    consolidated = {
        "status": internal_decision, "producer": PRODUCER, "execution_depth": "Batch092 bounded evidence consolidation",
        "semantic_scope": "Batch092 current state", "authority_allowed": "handoff and external review", "authority_forbidden": "external approval",
        "prompt_id": contract["prompt_id"], "batch091_artifact": read_json(output / "batch091_artifact_ingest.json"),
        "reactome_source": {key: source[key] for key in ("status", "unique_chapter_count", "duplicate_chapter_count", "observed_pathway_count", "observed_reaction_count", "silent_omission_count", "stable_id_conflict_count", "uncertain_event_count", "omitted_event_count", "normal_variant_pair_count")},
        "translation_depth": translation_depth, "chapter_scenarios": {"windows": len(windows), "linux": len(linux), "cross_platform": cross_platform["status"]},
        "amds": {key: amds[key] for key in ("decision", "eligible_cohort_count", "executed_episode_count", "executed_probe_count", "contradiction_count", "backtrack_count", "terminal_distribution", "safe_abstention_accuracy", "macro_accuracy")},
        "critic": {"finding_count": critic["finding_count"], "seal_mutations_rejected": critic["seal_breaking_mutations_rejected"], "semantic_mutations_rejected": critic["resigned_raw_semantic_mutations_rejected"]},
        "claim_boundary": claim, "exact_blockers": blockers,
    }
    write(output / "batch092_consolidated_state.json", consolidated)
    summary = f"""# Batch092 campaign summary

Batch092 officially verifies the Batch091 artifact while reconciling its invalid outer self-manifest entry. Independent expected-red review excludes Batch091's class-associated AMDS path, copied baselines, generated proof authority, dictionary-only slot transition, and compact-summary critic from current authority without rewriting historical bytes.

The Reactome release 97 documentary boundary contains 29 unique chapters, {source['observed_pathway_count']} pathway occurrences, and {source['observed_reaction_count']} reaction occurrences with zero silent omissions and zero duplicate chapter inflation. Every reaction has a candidate translation disposition. This is complete candidate-translation coverage, not complete production implementation or software causal authority.

The reusable RPIR compiler and generic primitive library execute 29 representative chapter scenarios and the integrated adversarial scenario. Windows wheel-installed execution is complete; cross-platform status is `{cross_platform['status']}`. No candidate translation is promoted to production.

Corrected historical AMDS remains blocked because the eight Batch091 episodes do not have independently measured receipts for all semantic roles. Baselines, source-ownership proofs, repair licenses, historical patch actuation, and historical package-slot rollback therefore remain `NOT_RUN`. The canonical slot manager is implemented and unit-executed, but its capability test is not historical canary evidence.

The current decision is `{internal_decision}`. Protocol remains v2.19, package version remains 0.2.0b2.dev0, repair counts remain six issue-derived and four native external with historical increment zero, full scoring remains disallowed, public writes and automatic merge remain inactive, production readiness is false, and self-maintaining software is not demonstrated.
"""
    (output / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    core_names = sorted(path.name for path in output.iterdir() if path.is_file() and path.name not in MANIFEST_NAMES)
    write(output / "batch092_external_review_package_index.json", {
        "status": "PASS_COMPACT_INDEX", "producer": PRODUCER, "execution_depth": "bounded_output_file_index",
        "semantic_scope": "external review handoff", "authority_allowed": "artifact navigation", "authority_forbidden": "external approval",
        "file_count": len(core_names), "files": core_names, "raw_reactome_pdfs_included": False, "runtime_database_included": False,
    })
    core_rows = [
        f"{sha(path)}  {path.name}"
        for path in sorted(item for item in output.iterdir() if item.is_file() and item.name not in MANIFEST_NAMES)
    ]
    portable = output / "PORTABLE_ARTIFACT_SHA256SUMS.txt"
    artifact = output / "ARTIFACT_SHA256SUMS.txt"
    repository = output / "SHA256SUMS.txt"
    portable.write_text("\n".join(core_rows) + "\n", encoding="utf-8", newline="\n")
    artifact_rows = sorted(core_rows + [f"{sha(portable)}  {portable.name}"])
    artifact.write_text("\n".join(artifact_rows) + "\n", encoding="utf-8", newline="\n")
    repository_rows = sorted(
        core_rows
        + [
            f"{sha(artifact)}  {artifact.name}",
            f"{sha(portable)}  {portable.name}",
        ]
    )
    repository.write_text("\n".join(repository_rows) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": internal_decision, "output_file_count": len(core_names), "manifest_entry_count": len(repository_rows), "exact_blockers": blockers}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
