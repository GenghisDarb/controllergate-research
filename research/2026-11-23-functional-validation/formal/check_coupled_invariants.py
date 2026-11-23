"""Independent exact arithmetic for the retrieved Reactome inventory contract.

This script does not import the new translation engine. It derives invariant
checks directly from signed integer stoichiometric columns and audits finite
representation fibers. The finite table has a uniform artificial weighting;
its error lower bounds are not measurements of biological prevalence.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'research/reactome_event_contract.json'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fiber_audit(rows: list[tuple[tuple[int, ...], int]], representation) -> dict:
    groups: dict[tuple, Counter] = defaultdict(Counter)
    examples: dict[tuple, dict[int, tuple]] = defaultdict(dict)
    for state, target in rows:
        key = representation(state)
        groups[key][target] += 1
        examples[key].setdefault(target, state)
    errors = sum(sum(c.values()) - max(c.values()) for c in groups.values())
    ambiguous = [k for k, c in groups.items() if len(c) > 1]
    return {
        'states': len(rows), 'fibers': len(groups),
        'ambiguous_fibers': len(ambiguous),
        'minimum_errors_under_uniform_table_weight': errors,
        'examples': [{'representation': k, 'different_targets': examples[k]}
                     for k in ambiguous[:3]],
    }


def main() -> None:
    source = json.loads(SOURCE.read_text())
    events = {event['id']: event for event in source['events']}
    selected = ['R-HSA-70449', 'R-HSA-71849']
    entities = ['GA3P_c', 'Pi_c', 'NAD_c', 'BPG13_c',
                'NADH_c', 'H_c', 'PYR_c', 'LACT_c']
    columns = {}
    for event_id in selected:
        event = events[event_id]
        for side in ('inputs', 'outputs'):
            if not set(event[side]).issubset(entities):
                raise ValueError('unreviewed participant in selected event')
            if any(type(n) is not int or n <= 0 for n in event[side].values()):
                raise ValueError('positive integer coefficients required')
        columns[event_id] = [event['outputs'].get(k, 0) - event['inputs'].get(k, 0)
                             for k in entities]

    invariants = {
        'NAD_plus_NADH': ['NAD_c', 'NADH_c'],
        'GA3P_plus_BPG13': ['GA3P_c', 'BPG13_c'],
        'PYR_plus_LACT': ['PYR_c', 'LACT_c'],
    }
    invariant_checks = []
    for name, group in invariants.items():
        products = {event: sum(column[entities.index(k)] for k in group)
                    for event, column in columns.items()}
        invariant_checks.append({'name': name, 'entities': group,
                                 'dot_products': products,
                                 'preserved_per_event': all(v == 0 for v in products.values())})

    paired_delta = [sum(columns[event][i] for event in selected)
                    for i in range(len(entities))]
    restored = ['NAD_c', 'NADH_c', 'H_c']
    projected_return = all(paired_delta[entities.index(k)] == 0 for k in restored)
    full_return = all(v == 0 for v in paired_delta)
    assert all(c['preserved_per_event'] for c in invariant_checks)
    assert projected_return and not full_return

    # Event-local inventory domain: three required GAPDH inputs, 0/1/2 each.
    # Catalyst activity and cytosolic identity are held available and fixed.
    rows = [(counts, int(all(n >= 1 for n in counts)))
            for counts in itertools.product(range(3), repeat=3)]
    representations = {
        'reaction_metadata_only': lambda x: ('same_reaction',),
        'sum_of_available_required_tokens_only': lambda x: (sum(x),),
        'per_input_presence_for_single_step': lambda x: tuple(int(v > 0) for v in x),
        'full_input_inventory': lambda x: x,
    }
    fiber_results = {name: fiber_audit(rows, fn) for name, fn in representations.items()}
    # The same presence projection ceases to suffice when the target is
    # maximum consecutive firings without replenishment: min(counts).
    repeated_rows = [(counts, min(counts))
                     for counts in itertools.product(range(3), repeat=3)]
    repeated_presence = fiber_audit(repeated_rows,
                                   lambda x: tuple(int(v > 0) for v in x))
    result = {
        'schema': 'IndependentStoichiometricAndFiberAuditV1',
        'executed_utc': datetime.now(timezone.utc).isoformat(),
        'script_sha256': sha(Path(__file__)), 'source_sha256': sha(SOURCE),
        'source_kind': 'manually transcribed official Reactome event contract, not SBML export',
        'entity_order': entities, 'stoichiometric_columns': columns,
        'invariant_checks': invariant_checks,
        'one_GAPDH_then_one_LDH_delta': dict(zip(entities, paired_delta)),
        'declared_projection': restored,
        'projected_return': projected_return, 'full_state_return': full_return,
        'single_step_representation_audits': fiber_results,
        'repeated_firing_presence_audit': repeated_presence,
        'assumptions': ['unit source coefficients', 'inventory model',
                        'active catalyst available', 'annotated cytosolic event',
                        'no boundary replenishment during a trace',
                        'no reaction rates inferred'],
        'limits': ['not an empirical frequency distribution',
                   'not a TLD RMS-closure experiment',
                   'not a new conservation law',
                   'not a claim that all cell dynamics are captured'],
    }
    (ROOT / 'independent_invariants.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'projected_return': projected_return, 'full_state_return': full_return,
                      'minimum_single_step_errors': {
                          k: v['minimum_errors_under_uniform_table_weight']
                          for k, v in fiber_results.items()},
                      'repeated_firing_presence_errors':
                          repeated_presence['minimum_errors_under_uniform_table_weight']}, indent=2))


if __name__ == '__main__':
    main()
