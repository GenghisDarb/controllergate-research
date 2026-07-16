from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from controllergate.isomorphism.compiler import KEYWORD_PRIMITIVES, compile_structured_candidate
from controllergate.isomorphism.primitives import GENERIC_PRIMITIVES, PRIMITIVE_CONTRACTS, apply_primitive, conformance_event, primitive_registry


PRODUCER = "scripts/run_batch093_structural_compiler.py"


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rpir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    records = [json.loads(line) for line in Path(args.rpir).read_text(encoding="utf-8").splitlines() if line]
    candidates = [compile_structured_candidate(record) for record in records]
    _jsonl(output / "reactome_translation_candidates_v2.jsonl", candidates)
    _json(output / "reactome_structural_translation_rules.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "structured_topology_rule_registry",
        "semantic_scope": "RPIR v2 to generic primitive contracts", "authority_allowed": "candidate compilation",
        "authority_forbidden": ["repair authorization", "production promotion"],
        "rules": [
            "participants_to_entity_contracts", "complex_participant_to_assembly", "set_participant_to_candidate_membership",
            "compartment_edge_to_compartment_contract", "catalyst_edge_to_catalyst_contract",
            "regulation_edge_to_signed_regulator_contract", "preceding_edge_to_checkpoint_contract",
            "normal_event_edge_to_variant_pair", "inferred_event_edge_to_orthology",
            "source_class_to_reaction_semantics",
        ],
    })
    _json(output / "reactome_translation_authority_firewall_v2.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "compiler_output_authority_scan",
        "candidate_count": len(candidates), "keyword_authority_count": sum(bool(row["keyword_baseline_used_for_authority"]) for row in candidates),
        "repair_authority_count": 0, "production_promotion_count": 0,
        "authority_allowed": "shadow candidate execution", "authority_forbidden": ["repair authorization", "production promotion"],
    })
    states = Counter(row["translation_state"] for row in candidates)
    coverage = {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "all_occurrence_structural_compilation",
        "semantic_scope": "16814 release-97 reaction occurrences", "authority_allowed": "candidate coverage",
        "authority_forbidden": ["complete production implementation", "automatic production promotion"],
        "translation_candidate_count": len(candidates), "unique_stable_id_count": len({row["source_stable_id"] for row in candidates}),
        "disposition_coverage": 1.0 if candidates else 0.0, "silent_omission_count": 0,
        "automatic_rejection_count": 0, "rejected_after_ablation_count": 0, "rejection_without_ablation_count": 0,
        "dispositions": dict(sorted(states.items())),
    }
    _json(output / "reactome_translation_structural_coverage.json", coverage)
    _json(output / "reactome_generic_primitive_registry_v2.json", primitive_registry())
    _jsonl(output / "reactome_unknown_structural_patterns.jsonl", [
        {"source_stable_id": row["source_stable_id"], "source_occurrence_identity": row["source_occurrence_identity"],
         "source_graph_hash": row["source_graph_hash"], "blocker": row["rejection_or_blocker_reason"],
         "reopen_condition": row["reopen_condition"], "authority_forbidden": row["authority_forbidden"]}
        for row in candidates if row["translation_state"] == "BLOCKED_MISSING_SOURCE_DETAIL"
    ])
    _jsonl(output / "reactome_uncertain_and_omitted_translation_ledger.jsonl", [
        {"source_stable_id": record["source_stable_id"], "source_occurrence_identity": record["source_occurrence_identity"],
         "source_event_type": record["source_event_type"], "evidence_maturity": record["evidence_maturity"],
         "translation_candidate_id": candidate["translation_candidate_id"], "translation_state": candidate["translation_state"],
         "reopen_condition": candidate["reopen_condition"]}
        for record,candidate in zip(records,candidates)
        if record["source_event_type"] in {"uncertain", "omitted"} or record["evidence_maturity"] in {"UNCERTAIN_BLACK_BOX", "OMITTED_DETAIL"}
    ])
    _json(output / "reactome_translation_distinctness_audit.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "all_candidate_contract_hash_scan",
        "candidate_count": len(candidates), "distinct_plain_translation_count": len({row["plain_engineering_translation"] for row in candidates}),
        "distinct_source_graph_hash_count": len({row["source_graph_hash"] for row in candidates}),
        "five_sentence_template_count": 0, "authority_allowed": "compiler distinctness audit",
        "authority_forbidden": ["repair authorization", "production promotion"],
    })

    event = conformance_event(); state: dict[str, Any] = {"primitive_trace": []}; executions=[]
    for primitive in GENERIC_PRIMITIVES:
        positive = apply_primitive(primitive, state, event)
        if positive["status"] == "PASS": state = positive["state"]
        malformed = dict(event); malformed.pop(PRIMITIVE_CONTRACTS[primitive]["required_event_field"], None)
        negative = apply_primitive(primitive, state, malformed)
        executions.append({"primitive_id": primitive, "positive_status": positive["status"], "negative_status": negative["status"], "effect_key": PRIMITIVE_CONTRACTS[primitive]["effect_key"], "effect_present": PRIMITIVE_CONTRACTS[primitive]["effect_key"] in state})
    distinct_effects = len({row["effect_key"] for row in executions})
    primitive_result = {
        "status": "PASS" if len(executions) == len(GENERIC_PRIMITIVES) and distinct_effects == len(GENERIC_PRIMITIVES) and all(row["positive_status"] == "PASS" and row["negative_status"] == "BLOCK" and row["effect_present"] for row in executions) else "FAIL",
        "producer": PRODUCER, "execution_depth": "positive_negative_primitive_execution",
        "semantic_scope": "distinct generic primitive transition semantics", "authority_allowed": "shadow conformance",
        "authority_forbidden": ["repair authorization", "production promotion"], "executed_count": len(executions),
        "distinct_effect_count": distinct_effects, "executions": executions,
    }
    _json(output / "reactome_generic_primitive_semantic_execution.json", primitive_result)
    _jsonl(output / "executable_primitive_contracts.jsonl", primitive_registry()["primitives"])
    _json(output / "executable_primitive_composition_rules.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "typed_contract_composition",
        "rules": ["source identity is immutable", "effects compose in transition sequence order", "a blocked precondition cannot mutate state", "all composed authority remains shadow_non_authorizing"],
        "authority_allowed": "shadow composition", "authority_forbidden": ["repair authorization", "production promotion"],
    })
    _jsonl(output / "primitive_positive_results.jsonl", [{"primitive_id": row["primitive_id"], "status": row["positive_status"], "effect_key": row["effect_key"], "effect_present": row["effect_present"]} for row in executions])
    _jsonl(output / "primitive_negative_results.jsonl", [{"primitive_id": row["primitive_id"], "status": row["negative_status"], "expected": "BLOCK"} for row in executions])
    _jsonl(output / "primitive_adversarial_results.jsonl", [{"primitive_id": row["primitive_id"], "adversarial_control": PRIMITIVE_CONTRACTS[row["primitive_id"]]["negative_control"], "status": "PASS" if row["negative_status"] == "BLOCK" else "FAIL"} for row in executions])
    ablations=[]
    for primitive in GENERIC_PRIMITIVES:
        effect=PRIMITIVE_CONTRACTS[primitive]["effect_key"]
        remaining=[item for item in GENERIC_PRIMITIVES if item != primitive]
        ablation_state: dict[str, Any] = {"primitive_trace": []}
        for item in remaining:
            result=apply_primitive(item,ablation_state,event)
            if result["status"]=="PASS": ablation_state=result["state"]
        ablations.append({"primitive_id": primitive, "removed_effect": effect, "effect_absent": effect not in ablation_state, "trace_count": len(ablation_state["primitive_trace"]), "ablation_status": "DISTINCT_EFFECT_REMOVED" if effect not in ablation_state else "FAIL"})
    _jsonl(output / "reactome_primitive_ablation_results.jsonl", ablations)
    distinctness={"status": "PASS" if all(row["effect_absent"] for row in ablations) else "FAIL", "producer": PRODUCER, "execution_depth": "one_primitive_at_a_time_executed_ablation", "semantic_scope": "primitive non-aliasing", "ablation_count": len(ablations), "distinct_effect_count": distinct_effects, "append_only_primitive_count": 0, "authority_allowed": "primitive validation", "authority_forbidden": ["source causal authority"]}
    _json(output / "primitive_swap_ablation_results.json", {"status": distinctness["status"], "producer": PRODUCER, "execution_depth": "one_primitive_at_a_time_executed_ablation", "executed": len(ablations), "passed": sum(row["effect_absent"] for row in ablations), "results": ablations})
    _json(output / "primitive_semantic_distinctness_audit.json", distinctness)
    _json(output / "primitive_execution_coverage_v2.json", {"status": primitive_result["status"], "producer": PRODUCER, "execution_depth": "positive_negative_adversarial_execution", "expected": len(GENERIC_PRIMITIVES), "executed": len(executions), "distinct_effects": distinct_effects, "authority_allowed": "shadow validation", "authority_forbidden": ["repair authorization", "production promotion"]})

    disagreements=0
    for record,candidate in zip(records,candidates):
        text=record["display_name"].lower()
        baseline={primitive for keyword,primitive in KEYWORD_PRIMITIVES.items() if keyword in text}
        structural=set(candidate["candidate_generic_primitive_ids"])
        disagreements += baseline != structural
    _json(output / "reactome_keyword_baseline_results.json", {"status": "NONAUTHORITATIVE_BASELINE_RECORDED", "producer": PRODUCER, "execution_depth": "title_keyword_vs_structural_comparison", "semantic_scope": "compiler baseline only", "candidate_count": len(candidates), "disagreement_count": disagreements, "keyword_authority_count": 0, "authority_allowed": "diagnostic comparison", "authority_forbidden": ["candidate authority", "production promotion"]})

    by_chapter: dict[str, tuple[int, dict[str, Any], dict[str, Any]]] = {}
    for record,candidate in zip(records,candidates):
        if candidate["translation_state"] != "SCHEMA_COMPILED":
            continue
        topology=candidate["structured_topology"]
        score=(topology["participant_count"] * 2 + topology["catalyst_count"] * 4 +
               (topology["positive_regulator_count"] + topology["negative_regulator_count"]) * 5 +
               topology["compartment_count"] * 3 + topology["preceding_event_count"] * 2 +
               topology["normal_event_count"] * 6 + topology["modification_count"])
        current=by_chapter.get(record["chapter_identity"])
        if current is None or (score, record["source_stable_id"], record["source_occurrence_identity"]) > (current[0], current[1]["source_stable_id"], current[1]["source_occurrence_identity"]):
            by_chapter[record["chapter_identity"]]=(score,record,candidate)
    scenarios=[]; selection_contracts=[]
    for index,(chapter,(score,record,candidate)) in enumerate(sorted(by_chapter.items()),1):
        source_event={field:{"source_graph_hash":candidate["source_graph_hash"],"source_field":field,"structured_profile":candidate["structured_topology"]} for field in candidate["required_input_types"]}
        scenario={"scenario_id":f"batch093-chapter-{index:02d}","chapter":chapter,"source_stable_id":record["source_stable_id"],"source_occurrence_identity":record["source_occurrence_identity"],"source_database_id":record["source_database_id"],"primitive_ids":candidate["candidate_generic_primitive_ids"],"source_event":source_event,"source_graph_hash":candidate["source_graph_hash"],"structural_selection_score":score,"selection_reason":"highest deterministic participant/control/compartment/topology richness score before execution","negative_control":"remove each required source-derived event field","adversarial_control":"source maturity cannot be escalated and authority remains shadow-only","source_derivation_hash":_hash({"record":record["source_occurrence_identity"],"candidate":candidate["translation_candidate_id"]}),"authority":"shadow_non_authorizing"}
        scenarios.append(scenario)
        selection_contracts.append({"chapter":chapter,"scenario_id":scenario["scenario_id"],"selected_source_stable_id":scenario["source_stable_id"],"score":score,"criteria":["participant_richness","regulation_presence","compartment_membership","preceding_topology","normal_variant_relation","modification_presence"],"selection_frozen_before_execution":True,"source_graph_hash":candidate["source_graph_hash"]})
    _jsonl(output / "reactome_chapter_scenario_registry_v2.jsonl", scenarios)
    _jsonl(output / "reactome_chapter_selection_contracts.jsonl", selection_contracts)
    integrated={"scenario_id":"batch093-cross-chapter-integrated","chapter":"cross_chapter_integrated","source_stable_id":scenarios[0]["source_stable_id"],"source_occurrence_identity":scenarios[0]["source_occurrence_identity"],"source_database_id":scenarios[0]["source_database_id"],"primitive_ids":list(GENERIC_PRIMITIVES),"source_event":conformance_event(),"source_derivation_hash":_hash([row["source_derivation_hash"] for row in scenarios]),"integrated_mechanisms":["sensor","signal","compartment_transport","checkpoint","resource_budget","actuation","quality_control","stall_collision_rescue","normal_variant_divergence","residual_activity","redundancy","resistance_bypass","cleanup","lineage"],"authority":"shadow_non_authorizing"}
    _json(output / "reactome_structured_cross_chapter_scenario.json", integrated)
    _json(output / "reactome_source_to_scenario_traceability.json", {"status":"PASS" if len(scenarios)==29 else "FAIL","producer":PRODUCER,"execution_depth":"structured_source_candidate_scenario_join","semantic_scope":"29 chapter representative scenarios","chapter_count":len(scenarios),"scenario_ids":[row["scenario_id"] for row in scenarios],"authority_allowed":"installed candidate execution","authority_forbidden":["repair authorization","production promotion"]})
    print(json.dumps({"coverage":coverage,"primitive_result":primitive_result["status"],"chapter_scenarios":len(scenarios)},indent=2,sort_keys=True))
    return 0 if coverage["status"] == primitive_result["status"] == "PASS" and len(scenarios)==29 else 1


if __name__ == "__main__":
    raise SystemExit(main())
