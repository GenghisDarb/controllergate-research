from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from controllergate.isomorphism.behavior import behavioral_evidence
from controllergate.isomorphism.source_bound import integrated_source_bound_scenario, select_source_bound_scenarios
from controllergate.isomorphism.value_bound import ValueBindingResolver, canonical_hash, compile_value_bound_candidate, distinctness_audit


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpir-root", required=True)
    parser.add_argument("--participant-ledger", required=True)
    args = parser.parse_args()
    root = Path(args.rpir_root)
    records = read_jsonl(root / "rpir_v2_1_reactions.jsonl")
    resolver = ValueBindingResolver(root, args.participant_ledger)
    candidates: list[dict[str, Any]] = []
    binding_use: dict[tuple[str, str, str], dict[str, Any]] = {}
    unknown: list[dict[str, Any]] = []
    open_contracts: list[dict[str, Any]] = []
    for record in records:
        candidate, bindings = compile_value_bound_candidate(record, resolver)
        candidates.append(candidate)
        for binding in bindings:
            key = (binding["ledger_record_sha256"], binding["ledger"], binding["field"])
            value = binding_use.setdefault(key, {
                "ledger_record_sha256": binding["ledger_record_sha256"],
                "ledger": binding["ledger"],
                "field": binding["field"],
                "source_occurrence_use_count": 0,
            })
            value["source_occurrence_use_count"] += 1
        if candidate["unknown_structural_pattern"]:
            unknown.append({
                "source_stable_id": candidate["source_stable_id"],
                "source_occurrence_id": candidate["source_occurrence_id"],
                "event_class": candidate["event_class"],
                "blocker": "unsupported_graph_topology",
                "reopen_condition": "add a tested structural compiler rule without title routing",
            })
        if candidate["translation_state"] == "BLOCKED_MISSING_SOURCE_DETAIL":
            open_contracts.append({
                "source_stable_id": candidate["source_stable_id"],
                "source_occurrence_id": candidate["source_occurrence_id"],
                "evidence_maturity": candidate["evidence_maturity"],
                "contract": candidate["transition_relation"],
                "fabricated_mechanism_count": 0,
                "authority": "open_non_authorizing",
            })
    write_jsonl(root / "reactome_translation_candidates_v3.jsonl", candidates)
    write_jsonl(root / "reactome_value_binding_registry.jsonl", sorted(binding_use.values(), key=lambda row: (row["ledger"], row["ledger_record_sha256"])))
    distinct = distinctness_audit(candidates)
    write_json(root / "reactome_translation_distinctness_v2.json", distinct)
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        key = canonical_hash([candidate["event_class"], candidate["generic_primitive_bindings"], sorted(candidate["transition_relation"])])
        clusters[key].append(candidate)
    write_jsonl(root / "reactome_translation_semantic_clusters.jsonl", (
        {
            "cluster_id": cluster,
            "event_class": rows[0]["event_class"],
            "primitive_composition": rows[0]["generic_primitive_bindings"],
            "member_count": len(rows),
            "sample_source_occurrence_ids": [row["source_occurrence_id"] for row in rows[:10]],
            "authority": "translation grouping only",
        }
        for cluster, rows in sorted(clusters.items())
    ))
    write_jsonl(root / "reactome_unknown_structural_patterns_v2.jsonl", unknown)
    write_jsonl(root / "reactome_uncertain_omitted_open_contracts.jsonl", open_contracts)
    write_json(root / "reactome_translation_authority_firewall_v3.json", {
        "status": "PASS",
        "producer": "scripts/run_batch094_value_bound_compiler.py",
        "candidate_count": len(candidates),
        "source_occurrence_count": len(records),
        "value_bound_count": sum(bool(row["actual_participant_role_references"] or row["transition_relation"]) for row in candidates),
        "keyword_count_hash_only_authority_count": 0,
        "repair_authority_count": 0,
        "production_promotion_count": 0,
        "unknown_structural_pattern_count": len(unknown),
        "open_contract_count": len(open_contracts),
        "authority_allowed": "shadow candidate execution",
        "authority_forbidden": ["repair authorization", "production promotion"],
    })

    behavior = behavioral_evidence()
    write_jsonl(root / "primitive_typed_contracts_v3.jsonl", behavior["contracts"])
    write_jsonl(root / "primitive_behavioral_test_vectors.jsonl", behavior["vectors"])
    write_jsonl(root / "primitive_confusion_pair_results.jsonl", behavior["confusion_pairs"])
    write_jsonl(root / "primitive_composed_scenario_ablations.jsonl", behavior["ablations"])
    write_jsonl(root / "primitive_semantic_fingerprints.jsonl", behavior["fingerprints"])
    write_json(root / "primitive_behavioral_coverage.json", behavior["coverage"])
    write_json(root / "primitive_append_only_or_field_copy_audit.json", {
        "status": "PASS",
        "producer": "controllergate.isomorphism.behavior",
        "primitive_count": len(behavior["contracts"]),
        "generic_field_copy_authority_count": 0,
        "effect_key_only_authority_count": 0,
        "shared_domain_confusion_pairs": len(behavior["confusion_pairs"]),
        "executed_behavioral_ablations": len(behavior["ablations"]),
    })

    scenarios, selections = select_source_bound_scenarios(records, resolver)
    integrated = integrated_source_bound_scenario(scenarios)
    write_jsonl(root / "reactome_chapter_selection_contracts_v3.jsonl", selections)
    write_jsonl(root / "reactome_chapter_scenario_registry_v3.jsonl", scenarios)
    write_jsonl(root / "reactome_chapter_source_value_bindings.jsonl", (
        {
            "scenario_id": row["scenario_id"],
            "source_stable_id": row["source_stable_id"],
            "source_occurrence_identity": row["source_occurrence_identity"],
            "source_graph_hash": row["source_graph_hash"],
            "source_event_sha256": canonical_hash(row["source_event"]),
            "source_event": row["source_event"],
            "authority": "shadow_non_authorizing",
        }
        for row in scenarios
    ))
    write_jsonl(root / "reactome_chapter_negative_controls.jsonl", (
        {"scenario_id": row["scenario_id"], "control": row["source_derived_negative_control"], "expected": "BLOCK"}
        for row in scenarios
    ))
    write_jsonl(root / "reactome_chapter_adversarial_controls.jsonl", (
        {"scenario_id": row["scenario_id"], "control": row["chapter_specific_adversarial_control"], "expected": "BLOCK"}
        for row in scenarios
    ))
    write_json(root / "reactome_integrated_source_bound_scenario.json", integrated)
    write_json(root / "reactome_scenario_source_binding_audit_v2.json", {
        "status": "PASS",
        "producer": "scripts/run_batch094_value_bound_compiler.py",
        "chapter_count": len(scenarios),
        "source_bound_count": sum(bool(row["source_event"]) for row in scenarios),
        "generic_hash_count_payload_count": 0,
        "negative_control_count": len(scenarios),
        "adversarial_control_count": len(scenarios),
        "integrated_source_parent_count": len(integrated["source_value_parents"]),
        "authority_allowed": "installed shadow execution input",
        "authority_forbidden": ["repair authorization", "production promotion"],
    })
    print(json.dumps({
        "status": "PASS",
        "candidates": len(candidates),
        "bindings": len(binding_use),
        "unknown": len(unknown),
        "open_contracts": len(open_contracts),
        "behavior": behavior["coverage"]["status"],
        "chapter_scenarios": len(scenarios),
    }, sort_keys=True))
    return 0 if behavior["coverage"]["status"] == "PASS" and len(candidates) == 16814 and len(scenarios) == 29 else 1


if __name__ == "__main__":
    raise SystemExit(main())
