from __future__ import annotations
import csv
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path

from token_translation import (FaithfulTranslation, GenericIncidence, ablated_step,
                              independent_snapshot_batch, load_model, sequential_batch,
                              source_step, state_from)

ROOT = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def verify_freeze():
    path = ROOT / "FROZEN_DESIGN.json"
    freeze = json.loads(path.read_text())
    failures = [name for name, sha in freeze["files"].items()
                if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha]
    if failures:
        raise RuntimeError("frozen input drift: " + ", ".join(failures))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one_step_cases(model, levels):
    for reaction in model.reactions:
        support = sorted({p for p, _ in reaction.inputs + reaction.outputs} | set(reaction.catalysts))
        chemicals = {model.chemical[p] for p in support}
        remote = sorted(p for p in model.places if p not in support and model.chemical[p] in chemicals)
        for remote_count in ([0, 2] if remote else [0]):
            for assignment in itertools.product(levels, repeat=len(support)):
                supplied = dict(zip(support, assignment))
                supplied.update({p: remote_count for p in remote})
                yield reaction, state_from(model, supplied), remote_count


def semantic(result):
    return result.status, result.inventory


def trace_run(model, steps, spec):
    state = state_from(model, spec["initial"])
    by_id = {r.identifier: r for r in model.reactions}
    result = {"initial": list(state), "steps": []}
    for identifier in spec["events"]:
        if any(x is not None and x < 0 for x in state):
            row = {"status": "INVALID_STATE", "inventory": state, "reason": "prior ablation produced negative inventory"}
        else:
            row = asdict(steps(by_id[identifier], state))
            if row["status"] == "PASS":
                state = tuple(row["inventory"])
        result["steps"].append({"event": identifier, **row})
    result["final"] = list(state)
    return result


def main():
    frozen_sha = verify_freeze()
    spec = json.loads((ROOT / "experiment_spec.json").read_text())
    model = load_model(json.loads((ROOT / "token_contract.json").read_text()))
    faithful, generic = FaithfulTranslation(model), GenericIncidence(model)
    arms = {"faithful_atomic": faithful.step, "generic_incidence": generic.step}
    for name in ("edge_only", "consume_catalyst", "pool_compartments"):
        arms[name] = lambda reaction, inventory, mode=name: ablated_step(model, reaction, inventory, mode)
    fields = ("cases", "oracle_enabled", "predicted_enabled", "status_disagreement", "false_enable", "false_block",
              "wrong_successor", "exact_model_disagreement", "negative_count", "catalyst_depletion")
    totals = {name: {key: 0 for key in fields} for name in arms}
    by_event = {r.identifier: {name: {key: 0 for key in fields} for name in arms} for r in model.reactions}
    examples, h = {}, hashlib.sha256()
    one_step_count, generic_faithful_disagreement = 0, 0
    with (ROOT / "source_oracle_truth_table.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "event", "remote_counterpart_count", "inventory_by_frozen_place_order", "oracle_status", "oracle_successor"])
        for case_id, (reaction, inventory, remote) in enumerate(one_step_cases(model, spec["initial_inventory_levels"]), 1):
            truth = source_step(model, reaction, inventory)
            writer.writerow([case_id, reaction.identifier, remote, json.dumps(inventory, separators=(",", ":")),
                             truth.status, json.dumps(truth.inventory, separators=(",", ":"))])
            outputs = {}
            for name, step in arms.items():
                result = step(reaction, inventory)
                outputs[name] = result
                catalyst_indices = [model.places.index(p) for p in reaction.catalysts]
                flags = {"cases": 1, "oracle_enabled": truth.status == "PASS", "predicted_enabled": result.status == "PASS",
                         "status_disagreement": truth.status != result.status,
                         "false_enable": truth.status != "PASS" and result.status == "PASS",
                         "false_block": truth.status == "PASS" and result.status != "PASS",
                         "wrong_successor": truth.status == result.status == "PASS" and truth.inventory != result.inventory,
                         "exact_model_disagreement": semantic(truth) != semantic(result),
                         "negative_count": any(v is not None and v < 0 for v in result.inventory),
                         "catalyst_depletion": any(result.inventory[i] < inventory[i] for i in catalyst_indices)}
                for key, value in flags.items():
                    totals[name][key] += int(value)
                    by_event[reaction.identifier][name][key] += int(value)
                if flags["exact_model_disagreement"]:
                    category = name + ":" + ("status" if flags["status_disagreement"] else "successor")
                    if len(examples.setdefault(category, [])) < 3:
                        examples[category].append({"case_id": case_id, "event": reaction.identifier,
                                                   "inventory": dict(zip(model.places, inventory)),
                                                   "oracle": asdict(truth), "candidate": asdict(result)})
            generic_faithful_disagreement += semantic(outputs["faithful_atomic"]) != semantic(outputs["generic_incidence"])
            h.update(canonical([case_id, reaction.identifier, inventory, semantic(truth),
                                {name: semantic(value) for name, value in outputs.items()}]) + b"\n")
            one_step_count += 1

    batch_rows = []
    for a, b in itertools.product(model.reactions, repeat=2):
        demands_a, demands_b = dict(a.inputs), dict(b.inputs)
        catalysts = set(a.catalysts) | set(b.catalysts)
        for kind in ("individual_maximum", "joint_sum", "zero_inputs"):
            quantities = {}
            for p in set(demands_a) | set(demands_b):
                x, y = demands_a.get(p, 0), demands_b.get(p, 0)
                quantities[p] = max(x, y) if kind == "individual_maximum" else x + y if kind == "joint_sum" else 0
            quantities.update({p: 1 for p in catalysts})
            initial = state_from(model, quantities)
            oracle = sequential_batch(lambda r, s: source_step(model, r, s), (a, b), initial)
            observed = {
                "faithful_atomic": sequential_batch(faithful.step, (a, b), initial),
                "generic_incidence": sequential_batch(generic.step, (a, b), initial),
                "independent_prerequisites": independent_snapshot_batch(model, (a, b), initial),
            }
            batch_rows.append({"events": [a.identifier, b.identifier], "inventory_kind": kind, "initial": initial,
                               "oracle": oracle, "arms": observed,
                               "disagreement": {name: value != oracle for name, value in observed.items()},
                               "negative_count": {name: any(x is not None and x < 0 for x in value[1]) for name, value in observed.items()}})
    batch_summary = {name: {"cases": len(batch_rows),
                            "disagreement": sum(row["disagreement"][name] for row in batch_rows),
                            "negative_count": sum(row["negative_count"][name] for row in batch_rows)}
                     for name in ("faithful_atomic", "generic_incidence", "independent_prerequisites")}
    traces = {}
    for trace in spec["coupled_traces"]:
        traces[trace["id"]] = {"source_oracle": trace_run(model, lambda r, s: source_step(model, r, s), trace)}
        for name, step in arms.items():
            traces[trace["id"]][name] = trace_run(model, step, trace)
    result = {
        "schema": "functional_translation_results.v1", "frozen_design_sha256": frozen_sha,
        "place_order": model.places, "source_event_count": len(model.reactions), "place_count": len(model.places),
        "one_step_cases_per_arm": one_step_count, "one_step_arm_count": len(arms),
        "one_step_outcome_stream_sha256": h.hexdigest(), "one_step_totals": totals,
        "by_event": by_event, "counterexamples": examples,
        "generic_faithful_semantic_disagreements": generic_faithful_disagreement,
        "batch_summary": batch_summary, "batch_rows": batch_rows, "coupled_traces": traces,
        "scope": "Exhaustive only over the predeclared event-local ternary state grids and fixed batches; not all whole-network states or biological outcomes.",
        "conclusion_boundary": "Compiler fidelity to an explicitly chosen untimed model; no empirical biological advantage or full cell isomorphism is established.",
    }
    (ROOT / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("one_step_cases_per_arm", "one_step_totals", "generic_faithful_semantic_disagreements", "batch_summary")}, indent=2))


if __name__ == "__main__":
    main()
