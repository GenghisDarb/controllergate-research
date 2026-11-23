"""Review the completed benchmark against its original Reactome source contract.

The reference below does not call source_step, sequential_batch, or the compiled
contract's coefficients. It reads the separately retained source transcription.
It does execute the submitted backends to compare their actual behavior.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MECH = ROOT / 'mechanisms'
sys.path.insert(0, str(MECH))
from token_translation import FaithfulTranslation, GenericIncidence, ablated_step, load_model


def h(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_path = ROOT / 'research/reactome_event_contract.json'
    source = json.loads(source_path.read_text())
    original_events = {e['id']: e for e in source['events']}
    model = load_model(json.loads((MECH / 'token_contract.json').read_text()))
    idx = {p: i for i, p in enumerate(model.places)}
    compiled_events = {e.identifier: e for e in model.reactions}
    assert set(compiled_events) == set(original_events)
    assert set(model.places) == set(source['participants']) | {'active_' + c for c in source['catalysts']}
    result = json.loads((MECH / 'results.json').read_text())

    def expected(event_id, inventory):
        e = original_events[event_id]
        # Use a strict source-contract enablement inequality independently of
        # the translated contract. All inspected grid states have exact counts.
        demands = dict(e['inputs'])
        demands['active_' + e['catalyst']] = 1
        if min(inventory[idx[p]] - n for p, n in demands.items()) < 0:
            return 'BLOCK', tuple(inventory)
        delta = Counter(e['outputs'])
        delta.subtract(e['inputs'])
        return 'PASS', tuple(n + delta[p] for p, n in zip(model.places, inventory))

    faithful, generic = FaithfulTranslation(model), GenericIncidence(model)
    backends = {'faithful_atomic': faithful.step, 'generic_incidence': generic.step}
    for mode in ('edge_only', 'consume_catalyst', 'pool_compartments'):
        backends[mode] = lambda e, x, mode=mode: ablated_step(model, e, x, mode)
    counters = {name: Counter() for name in backends}
    seen, enabled, table_errors = set(), 0, 0
    rows = csv.DictReader((MECH / 'source_oracle_truth_table.csv').open())
    for ordinal, row in enumerate(rows, 1):
        assert int(row['case_id']) == ordinal
        event = row['event']
        inventory = tuple(json.loads(row['inventory_by_frozen_place_order']))
        assert len(inventory) == len(idx)
        assert all(type(v) is int and v in (0, 1, 2) for v in inventory)
        key = (event, inventory)
        assert key not in seen
        seen.add(key)
        truth_status, truth_next = expected(event, inventory)
        enabled += truth_status == 'PASS'
        table_errors += (truth_status != row['oracle_status'] or
                         truth_next != tuple(json.loads(row['oracle_successor'])))
        for name, backend in backends.items():
            actual = backend(compiled_events[event], inventory)
            c = counters[name]
            c['cases'] += 1
            c['oracle_enabled'] += truth_status == 'PASS'
            c['false_enable'] += truth_status != 'PASS' and actual.status == 'PASS'
            c['wrong_successor'] += (truth_status == actual.status == 'PASS' and
                                     truth_next != actual.inventory)
            c['exact_model_disagreement'] += (truth_status, truth_next) != (actual.status, actual.inventory)
            c['negative_count'] += any(v < 0 for v in actual.inventory)
    assert table_errors == 0
    assert len(seen) == result['one_step_cases_per_arm']
    for name, c in counters.items():
        for metric, value in c.items():
            assert value == result['one_step_totals'][name][metric], (name, metric)

    batch_errors, batch_checks = 0, 0
    for row in result['batch_rows']:
        current = tuple(row['initial'])
        statuses = []
        for event in row['events']:
            status, following = expected(event, current)
            statuses.append(status)
            if status == 'PASS':
                current = following
        reference = [statuses, list(current)]
        assert row['oracle'] == reference
        for name in ('faithful_atomic', 'generic_incidence'):
            state, executed_statuses = tuple(row['initial']), []
            for event in row['events']:
                out = backends[name](compiled_events[event], state)
                executed_statuses.append(out.status)
                if out.status == 'PASS':
                    state = out.inventory
            batch_checks += 1
            batch_errors += [executed_statuses, list(state)] != reference
    assert batch_errors == 0
    receipt = {
        'schema': 'RootIndependentTransitionReviewV1',
        'reviewed_utc': datetime.now(timezone.utc).isoformat(), 'status': 'PASS',
        'source_transcription_sha256': h(source_path),
        'benchmark_result_sha256': h(MECH / 'results.json'),
        'source_truth_table_sha256': h(MECH / 'source_oracle_truth_table.csv'),
        'review_code_sha256': h(Path(__file__)),
        'unique_event_local_cases': len(seen), 'source_enabled_cases': enabled,
        'independent_source_table_disagreements': table_errors,
        'recomputed_arm_metrics': {n: dict(c) for n, c in counters.items()},
        'ordered_batches': len(result['batch_rows']),
        'reexecuted_competent_backend_batch_checks': batch_checks,
        'batch_disagreements': batch_errors,
        'independence': 'Reference reads original source-transcription coefficients, not benchmark source_step or compiled coefficients. Submitted backends are executed; Reactome transcription remains a shared source assumption.',
        'scope': 'All predeclared event-local cases and ordered batches, not all global network states or empirical kinetics.',
    }
    out = ROOT / 'formal/independent_transition_review.json'
    out.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'unique_event_local_cases', 'source_enabled_cases',
                                            'independent_source_table_disagreements', 'ordered_batches',
                                            'reexecuted_competent_backend_batch_checks', 'batch_disagreements')}, indent=2))


if __name__ == '__main__':
    main()
