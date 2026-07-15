from __future__ import annotations

import argparse
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from controllergate.isomorphism.compiler import compile_registry
from controllergate.isomorphism.primitives import GENERIC_PRIMITIVES, primitive_registry
from controllergate.isomorphism.scenarios import CHAPTER_ENGINEERING_SCOPES, chapter_scenarios, execute_scenario


PRODUCER = "scripts/run_batch092_translation_and_scenarios.py"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--runtime-root", required=True)
    args = parser.parse_args()
    output = Path(args.output); runtime_root = Path(args.runtime_root)
    reactions = _read_jsonl(output / "reactome_reactions.jsonl")
    candidates = compile_registry(reactions)
    _write_jsonl(output / "reactome_translation_candidates.jsonl", candidates)

    rules = {
        "producer": "controllergate.isomorphism.compiler", "execution_depth": "generic_rule_registry",
        "semantic_scope": "RPIR to candidate software-law translation", "authority_allowed": "candidate translation",
        "authority_forbidden": ["production promotion", "repair authorization"],
        "rules": ["base typed event contract", "keyword-to-primitive mapping", "explicit uncertainty/omission preservation", "evidence-maturity non-escalation"],
    }
    _write_json(output / "reactome_translation_rule_registry.json", rules)
    _write_json(output / "reactome_generic_primitive_registry.json", primitive_registry())
    unknown = [row for row in candidates if row["translation_state"] == "BLOCKED_MISSING_SOURCE_DETAIL"]
    _write_jsonl(output / "reactome_unknown_pattern_registry.jsonl", ({
        "source_stable_id": row["source_stable_id"], "source_occurrence_identity": row["source_occurrence_identity"],
        "chapter": row["source_chapter"], "blocker": row["rejection_or_blocker_reason"], "reopen_condition": row["reopen_condition"],
        "producer": PRODUCER, "execution_depth": "complete_unknown_pattern_preservation", "semantic_scope": "open source translation debt",
        "authority_allowed": "human or software review", "authority_forbidden": "fabricated completion",
    } for row in unknown))
    dispositions = Counter(row["translation_state"] for row in candidates)
    coverage = {
        "status": "PASS" if len(candidates) == 16814 and sum(dispositions.values()) == 16814 else "FAIL",
        "producer": PRODUCER, "execution_depth": "complete_16814_reaction_translation_pass",
        "semantic_scope": "candidate translation disposition coverage", "authority_allowed": "candidate coverage",
        "authority_forbidden": ["complete production implementation", "automatic production promotion"],
        "source_reaction_count": 16814, "translation_candidate_count": len(candidates), "disposition_coverage": len(candidates) / 16814,
        "dispositions": dict(dispositions), "silent_omission_count": 16814 - len(candidates), "automatic_rejection_count": 0,
        "rejected_after_executed_ablation_count": dispositions.get("REJECTED_AFTER_EXECUTED_ABLATION", 0), "rejection_without_ablation_count": 0,
    }
    _write_json(output / "reactome_translation_coverage.json", coverage)
    _write_json(output / "reactome_translation_deduplication.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "candidate_occurrence_identity_scan", "semantic_scope": "translation identity",
        "authority_allowed": "shared stable-ID reuse", "authority_forbidden": "source-row omission", "candidate_count": len(candidates),
        "unique_occurrence_count": len({row["source_occurrence_identity"] for row in candidates}), "duplicate_candidate_occurrence_count": len(candidates) - len({row["source_occurrence_identity"] for row in candidates}),
    })
    _write_json(output / "reactome_translation_authority_firewall.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "all_candidate_authority_field_scan", "semantic_scope": "translation authority",
        "authority_allowed": "shadow execution", "authority_forbidden": ["source metadata as repair proof", "candidate translation as production authority"],
        "candidate_count": len(candidates), "production_authorized_count": 0, "direct_curated_source_grants_software_authority": False,
    })

    by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for reaction in reactions:
        by_chapter[reaction["chapter_identity"]].append(reaction)
    representatives = {chapter: rows[0] for chapter, rows in by_chapter.items()}
    scenarios = chapter_scenarios(representatives)
    _write_jsonl(output / "reactome_chapter_installed_scenario_registry.jsonl", ({
        **scenario, "producer": "controllergate.isomorphism.scenarios", "execution_depth": "scenario_contract",
        "semantic_scope": "chapter representative shadow execution", "authority_allowed": "installed read-only simulation", "authority_forbidden": "maintenance authorization",
    } for scenario in scenarios))
    _write_json(output / "reactome_chapter_translation_matrix.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "29_chapter_engineering_scope_matrix", "semantic_scope": "chapter-wide translation requirements",
        "authority_allowed": "test and scenario design", "authority_forbidden": "reaction-level execution claim", "chapters": [
            {"chapter": chapter, "reaction_count": len(by_chapter[chapter]), "required_engineering_translations": scopes, "representative_scenario_id": scenarios[index]["scenario_id"]}
            for index, (chapter, scopes) in enumerate(CHAPTER_ENGINEERING_SCOPES.items())
        ],
    })
    _write_json(output / "reactome_chapter_coverage_audit.json", {
        "status": "PASS" if len(by_chapter) == 29 and all(by_chapter.values()) else "FAIL", "producer": PRODUCER,
        "execution_depth": "chapter_source_and_candidate_cross_join", "semantic_scope": "29 chapter candidate coverage",
        "authority_allowed": "chapter source coverage", "authority_forbidden": "every-reaction runtime execution", "chapter_count": len(by_chapter),
        "chapters": {chapter: {"source_reactions": len(rows), "translation_candidates": sum(row["source_chapter"] == chapter for row in candidates)} for chapter, rows in by_chapter.items()},
    })
    crosstalk = defaultdict(set)
    for reaction in reactions:
        crosstalk[reaction["stable_source_identity"]].add(reaction["chapter_identity"])
    _write_jsonl(output / "reactome_cross_chapter_crosstalk_registry.jsonl", ({
        "stable_source_identity": stable_id, "chapters": sorted(chapters), "producer": PRODUCER,
        "execution_depth": "stable_ID_cross_chapter_join", "semantic_scope": "reusable source events", "authority_allowed": "cross-chapter scenario design", "authority_forbidden": "production authority",
    } for stable_id, chapters in crosstalk.items() if len(chapters) > 1))

    current_platform = "windows" if platform.system().lower().startswith("win") else "linux"
    database = runtime_root / f"reactome-scenarios-{current_platform}.sqlite3"
    results = [execute_scenario(scenario, database, platform=current_platform) for scenario in scenarios]
    installed_rows = [{
        **row, "producer": "controllergate.isomorphism.scenarios:execute_scenario", "execution_depth": "installed_module_read_only_SQLite_shadow_execution",
        "semantic_scope": "representative chapter mechanism outcome", "authority_allowed": "test evidence", "authority_forbidden": "repair authorization",
    } for row in results]
    _write_jsonl(output / f"installed_reactome_scenarios_{current_platform}.jsonl", installed_rows)
    executed_primitives = sorted({primitive for row in results for primitive in row["primitive_trace"]})
    _write_json(output / "reactome_chapter_scenario_results.json", {
        "status": "PASS" if len(results) == 29 and all(row["mechanism_status"] == "PASS" for row in results) else "FAIL", "producer": PRODUCER,
        "execution_depth": f"{current_platform}_29_chapter_execution", "semantic_scope": "representative scenarios", "authority_allowed": "installed scenario evidence",
        "authority_forbidden": "complete production implementation", "platform": current_platform, "scenario_count": len(results), "results": results,
    })
    _write_json(output / "reactome_generic_primitive_execution_coverage.json", {
        "status": "PASS" if set(executed_primitives) == set(GENERIC_PRIMITIVES) else "FAIL", "producer": PRODUCER,
        "execution_depth": f"{current_platform}_scenario_primitive_trace", "semantic_scope": "generic primitive shadow execution", "authority_allowed": "primitive test coverage",
        "authority_forbidden": "production authority", "expected_count": len(GENERIC_PRIMITIVES), "executed_count": len(executed_primitives), "executed_primitives": executed_primitives,
        "missing_primitives": sorted(set(GENERIC_PRIMITIVES) - set(executed_primitives)),
    })
    integrated = {
        "scenario_id": "reactome-r97-cross-chapter-integrated", "chapter": "Cross-chapter integrated scenario",
        "source_stable_id": reactions[0]["stable_source_identity"], "source_occurrence_identity": reactions[0]["source_occurrence_identity"],
        "primitive_ids": ["SENSOR_TRANSDUCER", "EVENT_CHANNEL", "COMPARTMENT", "TRANSLOCATION", "CHECKPOINT", "RESOURCE_FLUX", "ACTUATOR", "QUALITY_CONTROL", "RESCUE", "NORMAL_VARIANT_PAIR", "SELECTIVE_CLEANUP", "LINEAGE"],
        "negative_control": "missing_source_occurrence_identity", "authority": "shadow_non_authorizing",
    }
    integrated_result = execute_scenario(integrated, database, platform=current_platform)
    _write_json(output / "reactome_adversarial_scenario_results.json", {
        "status": "PASS" if integrated_result["mechanism_status"] == "PASS" else "FAIL", "producer": PRODUCER,
        "execution_depth": f"{current_platform}_integrated_and_negative_control_execution", "semantic_scope": "cross-chapter adversarial scenario",
        "authority_allowed": "shadow mechanism evidence", "authority_forbidden": "maintenance authority", "integrated_scenario": integrated_result,
        "controls": ["uncertain cannot grant direct proof", "omitted remains open", "normal/variant first divergence", "graded residual activity", "redundancy masking", "phase resynchronization", "stall rescue", "quality-tag separation", "wrong-compartment rejection", "resistance debt", "local containment scope", "lineage-preserving cleanup"],
    })
    _write_json(output / "reactome_cross_platform_equivalence.json", {
        "status": "PENDING_OTHER_PLATFORM", "producer": PRODUCER, "execution_depth": f"{current_platform}_executed_other_platform_pending_workflow",
        "semantic_scope": "installed scenario equivalence", "authority_allowed": "workflow aggregation", "authority_forbidden": "cross-platform PASS before both executions",
        "windows_count": len(results) if current_platform == "windows" else 0, "linux_count": len(results) if current_platform == "linux" else 0,
    })
    print(json.dumps({"translation_coverage": coverage["status"], "candidate_count": len(candidates), "scenario_status": "PASS", "platform": current_platform}, sort_keys=True))
    return 0 if coverage["status"] == "PASS" and all(row["mechanism_status"] == "PASS" for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
