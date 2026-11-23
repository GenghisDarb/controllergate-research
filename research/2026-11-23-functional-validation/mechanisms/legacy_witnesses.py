"""Execute exact selected archived functions on documented source-shaped fixtures.

Function bodies are parsed from pinned source snapshots, not rewritten. The
resolver is an in-memory fixture, not a claim of replaying the 56 MB RPIR ledger.
The full installed CLI/SQLite/provider path is not invoked here.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from run_benchmark import verify_freeze
from token_translation import load_archived_primitive, load_model, source_step, state_from

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "source_snapshot/controllergate/isomorphism"


def load_functions(filename, names, namespace):
    tree = ast.parse((SNAPSHOT / filename).read_text())
    nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets):
            nodes.append(node)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), filename, "exec"), namespace)


def main():
    freeze_sha = verify_freeze()
    source = json.loads((ROOT / "reactome_event_contract.source.json").read_text())
    model = load_model(json.loads((ROOT / "token_contract.json").read_text()))
    apply = load_archived_primitive()
    env = {"Any": Any, "hashlib": hashlib, "json": json,
           "PRIMITIVE_CONTRACTS": apply.__globals__["PRIMITIVE_CONTRACTS"],
           "GENERIC_PRIMITIVES": apply.__globals__["GENERIC_PRIMITIVES"]}
    load_functions("value_bound.py", {"LEDGER_FILES", "canonical_hash", "record_hash", "_primitives", "_role_refs", "compile_value_bound_candidate"}, env)
    load_functions("source_bound.py", {"_actual_event", "integrated_source_bound_scenario"}, env)
    event_source = next(row for row in source["events"] if row["id"] == "R-HSA-71849")
    values = {field: [] for field in env["LEDGER_FILES"]}
    for role, key in (("input", "inputs"), ("output", "outputs")):
        for participant, count in event_source[key].items():
            entity = source["participants"][participant]
            values["source_value_binding"].append({"stable_id": entity["id"], "class": "SimpleEntity", "role": role,
                                                   "stoichiometry": count, "compartment": entity["compartment"]})
    values["catalyst_details"] = [{"catalyst": source["catalysts"]["LDH"]["id"], "activity": source["catalysts"]["LDH"]["activity"]}]
    values["entity_compartments"] = [{"compartment": "GO:0005829", "name": "cytosol"}]
    record = {"source_occurrence_identity": "manual-source-fixture:R-HSA-71849", "source_stable_id": "R-HSA-71849",
              "source_database_id": 71849, "source_class": "Reaction", "evidence_maturity": "DIRECT_CURATED",
              "chapter_identity": "local_fixture_only", "source_graph_hash": env["canonical_hash"](values)}
    for field, rows in values.items():
        record[field] = {"state": "SOURCE_VALUE" if rows else "SOURCE_EXPLICITLY_EMPTY",
                         "value": [env["record_hash"](row) for row in rows]}

    class Resolver:
        def __init__(self):
            self.fields_requested = []
        def resolve(self, _record, field):
            self.fields_requested.append(field)
            return values.get(field, [])

    resolver = Resolver()
    candidate, bindings = env["compile_value_bound_candidate"](record, resolver)
    event = env["_actual_event"](record, candidate, resolver)
    state, transitions = {"primitive_trace": []}, []
    for primitive in candidate["generic_primitive_bindings"]:
        result = apply(primitive, state, event)
        transitions.append({"primitive": primitive, "status": result["status"]})
        if result["status"] == "PASS":
            state = result["state"]
    scenario = {"source_event": event, "source_stable_id": record["source_stable_id"], "scenario_id": "manual-source-fixture"}
    integrated = env["integrated_source_bound_scenario"]([scenario])
    integrated_result = apply("RESOURCE_FLUX", {"primitive_trace": []}, integrated["source_event"])
    direct_negative = apply("RESOURCE_FLUX", {"primitive_trace": [], "resource_balance": {"balance": 0}},
                            {"source_occurrence_identity": "negative-control", "resource_delta": -1})
    catalyst_empty = apply("CATALYST", {"primitive_trace": []},
                           {"source_occurrence_identity": "presence-control", "catalyst": {"state": "explicit_empty"}})
    reaction = next(r for r in model.reactions if r.identifier == "R-HSA-71849")
    ready = state_from(model, {"PYR_c": 1, "NADH_c": 1, "H_c": 1, "active_LDH": 1})
    absent = state_from(model, {"PYR_c": 1, "NADH_c": 1, "H_e": 1, "active_LDH": 1})
    paired = [{"id": label, "inventory": dict(zip(model.places, inventory)),
               "source_oracle_status": source_step(model, reaction, inventory).status,
               "legacy_source_event_sha256": env["canonical_hash"](event)}
              for label, inventory in (("local_proton_present", ready), ("same_total_proton_remote", absent))]
    result = {
        "schema": "archived_translation_semantics_witness.v1", "frozen_design_sha256": freeze_sha,
        "repository_commit": "38897b79588f3ff4b1b9002eedc299a9bcf05140",
        "source_fixture_scope": "Manually source-grounded RPIR-shaped fixture with an in-memory resolver; not a replay of original full release-97 registry or installed runtime.",
        "candidate": candidate, "source_event": event, "positive_primitive_results": transitions,
        "resource_flux_selected": "RESOURCE_FLUX" in candidate["generic_primitive_bindings"],
        "source_adapter_fields_requested": sorted(set(resolver.fields_requested)),
        "integrated_resource_origin": next(row for row in integrated["source_value_parents"] if row["primitive"] == "RESOURCE_FLUX"),
        "integrated_resource_delta_type": type(integrated["source_event"]["resource_delta"]).__name__,
        "integrated_resource_result": integrated_result,
        "archived_numeric_underflow_negative_control": direct_negative,
        "generic_catalyst_presence_control": catalyst_empty,
        "paired_worlds": paired,
        "interpretation": "The archived PASS means source-bound primitive conformance. It is not relabeled as a physical enabledness claim. The source-event projection supplied to this path contains no changing world inventory and therefore cannot distinguish the paired states; the local typed repair adds that missing contract.",
        "downstream_scope": "canonical_maintenance verifies stage, source-event/result hashes and authority; inspected code does not reconstruct resource balances from molecular participants.",
    }
    (ROOT / "legacy_witnesses.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"resource_flux_selected": result["resource_flux_selected"],
                      "integrated_resource_delta_type": result["integrated_resource_delta_type"],
                      "integrated_resource_status": integrated_result["status"],
                      "numeric_underflow_status": direct_negative["status"], "paired_statuses": [r["source_oracle_status"] for r in paired]}, indent=2))


if __name__ == "__main__":
    main()
