"""Sealed exploratory stopping ablation. Never writes to original bridge/.

This analysis was motivated by original outcomes. Its local pre-execution seal
does not make it prospective with respect to those original outcomes.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from functools import lru_cache
import hashlib
from itertools import permutations
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
BRIDGE = ROOT.parent / 'bridge'
sys.path.insert(0, str(BRIDGE))
from conditional_acquisition import Model, public_state

SEALED = ['experiment_spec.json', 'run_stopping_ablation.py']
ORIGINAL = ['conditional_acquisition.py', 'experiment_spec.json', 'results.json', 'FROZEN_DESIGN.json']
NEW_ARMS = ['ORIGINAL_FIXED_ORDER_WITH_SOUND_STOP', 'BEST_FIXED_ORDER_WITH_SOUND_STOP']
OLD_ARMS = ['BEST_FROZEN_ORDER', 'GENERIC_ADAPTIVE_VAULT_ONLY', 'GENERIC_ADAPTIVE_WITH_PROBES']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def freeze():
    if (ROOT / 'FROZEN_DESIGN.json').exists() or (ROOT / 'results.json').exists():
        raise RuntimeError('Refusing to replace an existing design seal or result')
    original_seal = json.loads((BRIDGE / 'FROZEN_DESIGN.json').read_text())
    for name, digest in original_seal['source_hashes'].items():
        if sha(BRIDGE / name) != digest:
            raise RuntimeError('Original frozen source changed: ' + name)
    seal = {'schema': 'ExploratoryLocalSealV1', 'created_utc': datetime.now(timezone.utc).isoformat(),
            'source_hashes': {name: sha(ROOT / name) for name in SEALED},
            'original_input_hashes': {name: sha(BRIDGE / name) for name in ORIGINAL},
            'followup_evaluation_has_not_run': True,
            'scope': 'Locally frozen follow-up design after seeing original outcomes; not external preregistration or independent validation.'}
    save('FROZEN_DESIGN.json', seal)
    print(json.dumps({'frozen_design_sha256': sha(ROOT / 'FROZEN_DESIGN.json'), 'evaluated': False}))


def verify_seal():
    seal = json.loads((ROOT / 'FROZEN_DESIGN.json').read_text())
    for name, digest in seal['source_hashes'].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError('Follow-up source changed after freezing: ' + name)
    for name, digest in seal['original_input_hashes'].items():
        if sha(BRIDGE / name) != digest:
            raise RuntimeError('Original input changed: ' + name)
    return seal


def fixed_decision(model, history, order, budget):
    """No actual-world argument: only paid observations and the public model."""
    belief, acquired, _ = public_state(model, history)
    if model.pair_acquired(acquired):
        return None, 'PAIR_ACQUIRED', belief
    if all(not model.any_route_available(world) for world in belief):
        return None, 'UNREACHABLE_UNDER_DECLARED_MODEL', belief
    if len(history) >= budget:
        return None, 'BUDGET_EXHAUSTED', belief
    # Deliberately do not skip a known-unavailable vault: this is a fixed order.
    return order[len(history)], 'NEXT_FROZEN_ORDER_POSITION', belief


def run_fixed(model, world, order, budget, arm, graph_id):
    if sorted(order) != list(range(model.vault_count)):
        raise ValueError('Order must be a complete vault-only permutation')
    history, trace = [], []
    while True:
        action, reason, belief = fixed_decision(model, tuple(history), order, budget)
        if action is None:
            terminal = reason
            break
        assert action == order[len(history)]
        # Only the environment consults the actual world; the read is charged.
        outcome = model.outcome(world, action)
        trace.append({'step': len(history) + 1, 'action': action, 'charged_cost': 1,
                      'history_length_at_selection': len(history), 'belief_before': list(belief),
                      'observation_after_charge': outcome})
        history.append((action, outcome))
    _, acquired, _ = public_state(model, tuple(history))
    attainable = model.any_route_available(world)
    assert model.pair_acquired(acquired) == attainable
    assert len(history) <= budget
    if terminal == 'UNREACHABLE_UNDER_DECLARED_MODEL':
        assert not attainable and all(not model.any_route_available(w) for w in belief)
    return {'graph_id': graph_id, 'arm': arm, 'actual_world_for_scoring_only': world,
            'actions': len(history), 'failed_vault_accesses': sum(not value for _, value in history),
            'prerequisite_probes': 0, 'pair_acquired': model.pair_acquired(acquired),
            'pair_physically_available_in_synthetic_world': attainable, 'terminal': terminal,
            'history': history, 'trace': trace}


def optimize_order(model):
    """Return exact optimum plus survival flags for independent checking."""
    n, worlds = model.vault_count, model.worlds
    positive_masks = {w: sum(1 << a for a in range(n) if model.outcome(w, a)) for w in worlds}

    @lru_cache(None)
    def flags(mask):
        answers = []
        for w in worlds:
            observed_positive = mask & positive_masks[w]
            support = [v for v in worlds if mask & positive_masks[v] == observed_positive]
            acquired_pair = model.pair_acquired(observed_positive)
            possible_route = any(model.any_route_available(v) for v in support)
            answers.append(not acquired_pair and possible_route)
        return tuple(answers)

    @lru_cache(None)
    def solve(mask):
        if mask == (1 << n) - 1:
            assert not any(flags(mask))
            return Fraction(0), ()
        chance = Fraction(sum(flags(mask)), len(worlds))
        candidates = []
        for action in range(n):
            if not mask & (1 << action):
                later, suffix = solve(mask | (1 << action))
                candidates.append((chance + later, (action,) + suffix))
        return min(candidates)

    optimum, order = solve(0)
    table = {mask: flags(mask) for mask in range(1 << n)}
    return optimum, order, table


def verify_optimum(model, optimum, order, flag_table):
    """Independent public-history enumeration, then all complete permutations."""
    n, worlds = model.vault_count, model.worlds
    counts = []
    for mask in range(1 << n):
        observed_flags = []
        for world in worlds:
            history = tuple((a, model.outcome(world, a)) for a in range(n) if mask & (1 << a))
            belief, acquired, _ = public_state(model, history)
            alive = not model.pair_acquired(acquired) and any(model.any_route_available(v) for v in belief)
            observed_flags.append(alive)
        assert tuple(observed_flags) == flag_table[mask]
        counts.append(sum(observed_flags))
        for action in range(n):
            if not mask & (1 << action):
                following = flag_table[mask | (1 << action)]
                assert all(not nxt or prev for prev, nxt in zip(observed_flags, following))
    brute_best, number = None, 0
    for candidate in permutations(range(n)):
        total, mask = 0, 0
        for action in candidate:
            total += counts[mask]
            mask |= 1 << action
        option = (total, candidate)
        if brute_best is None or option < brute_best:
            brute_best = option
        number += 1
    assert Fraction(brute_best[0], len(worlds)) == optimum
    assert brute_best[1] == order
    return {'permutations_checked': number, 'minimum_total_actions_over_worlds': brute_best[0],
            'dp_brute_force_exact_match': True, 'public_history_survival_match': True,
            'survival_monotonicity': True}


def development_checks():
    single = Model(1, ((0,),))
    absent = run_fixed(single, 0, (0, 1), 2, 'fixture', 'single')
    present = run_fixed(single, 1, (0, 1), 2, 'fixture', 'single')
    assert absent['actions'] == 1 and absent['terminal'] == 'UNREACHABLE_UNDER_DECLARED_MODEL'
    assert present['actions'] == 2 and present['pair_acquired']
    assert fixed_decision(single, (), (0, 1), 2)[0] == 0
    separate = Model(2, ((0,), (1,)))
    # Failure of the first route does not prove failure of the other route.
    # A fixed permutation must not silently skip its next known-bad vault.
    assert fixed_decision(separate, ((0, 0),), (0, 1, 2, 3), 4)[0] == 1
    universal = Model(1, ((),))
    assert all(run_fixed(universal, w, (0, 1), 2, 'fixture', 'universal')['actions'] == 2 for w in universal.worlds)
    return {'status': 'PASS', 'checks': ['negative first observation soundly stops only with sufficient model support',
            'positive case still acquires both role receipts', 'empty unknown state does not imply failure',
            'failure of one route does not invalidate another route', 'no conditional skipping',
            'unconditional route succeeds in both worlds']}


def summarize(rows):
    attainable = [r for r in rows if r['pair_physically_available_in_synthetic_world']]
    unattainable = [r for r in rows if not r['pair_physically_available_in_synthetic_world']]
    return {'scenarios': len(rows), 'attainable_scenarios': len(attainable), 'unattainable_scenarios': len(unattainable),
            'pair_acquisitions': sum(r['pair_acquired'] for r in rows),
            'total_actions': sum(r['actions'] for r in rows),
            'actions_attainable': sum(r['actions'] for r in attainable),
            'actions_unattainable': sum(r['actions'] for r in unattainable),
            'failed_vault_accesses': sum(r['failed_vault_accesses'] for r in rows),
            'prerequisite_probes': sum(r.get('prerequisite_probes', 0) for r in rows),
            'terminals': dict(Counter(r['terminal'] for r in rows))}


def execute():
    seal = verify_seal()
    if (ROOT / 'results.json').exists():
        raise RuntimeError('Refusing to overwrite follow-up evaluation results')
    checks = development_checks()
    spec = json.loads((BRIDGE / 'experiment_spec.json').read_text())
    original = json.loads((BRIDGE / 'results.json').read_text())
    assert spec['budget'] == 8 and spec['resource_count'] == 3
    assert len(spec['frozen_evaluation_graphs']) == 4
    original_models = {m['graph_id']: m for m in original['models']}
    episodes, models = [], []
    for graph in spec['frozen_evaluation_graphs']:
        model = Model(spec['resource_count'], tuple(tuple(x) for x in graph['requires_all']))
        cost, order, flags = optimize_order(model)
        verification = verify_optimum(model, cost, order, flags)
        original_order = tuple(original_models[graph['id']]['fixed_order'])
        for arm, current_order in [(NEW_ARMS[0], original_order), (NEW_ARMS[1], order)]:
            for world in model.worlds:
                episodes.append(run_fixed(model, world, current_order, spec['budget'], arm, graph['id']))
        optimal_rows = [r for r in episodes if r['graph_id'] == graph['id'] and r['arm'] == NEW_ARMS[1]]
        assert Fraction(sum(r['actions'] for r in optimal_rows), len(model.worlds)) == cost
        models.append({'graph_id': graph['id'], 'original_fixed_order': original_order,
                       'best_fixed_order_with_sound_stop': order, 'minimum_expected_actions': str(cost),
                       'verification': verification})
    comparison = [r for r in original['episodes'] if r['arm'] in OLD_ARMS] + episodes
    arms = OLD_ARMS[:1] + NEW_ARMS + OLD_ARMS[1:]
    summaries = {arm: summarize([r for r in comparison if r['arm'] == arm]) for arm in arms}
    for arm in OLD_ARMS:
        for key in ['total_actions', 'pair_acquisitions', 'failed_vault_accesses', 'prerequisite_probes']:
            assert summaries[arm][key] == original['summaries'][arm][key]
    assert all(summaries[arm]['pair_acquisitions'] == 18 for arm in arms)
    stratified = [{'graph_id': graph['id'], 'arm': arm, **summarize([r for r in comparison if r['arm'] == arm and r['graph_id'] == graph['id']])}
                  for graph in spec['frozen_evaluation_graphs'] for arm in arms]
    costs = {arm: summaries[arm]['total_actions'] for arm in arms}
    decomposition = {
        'original_fixed_to_same_order_sound_stopping': costs[OLD_ARMS[0]] - costs[NEW_ARMS[0]],
        'same_order_sound_stopping_to_optimized_fixed_sound_stopping': costs[NEW_ARMS[0]] - costs[NEW_ARMS[1]],
        'optimized_fixed_sound_stopping_to_adaptive_vault_selection': costs[NEW_ARMS[1]] - costs[OLD_ARMS[1]],
        'adaptive_vault_selection_to_adaptive_with_probes': costs[OLD_ARMS[1]] - costs[OLD_ARMS[2]],
        'scope': 'Sequential descriptive contrasts on the same finite scenarios, not an independent population effect or unique causal decomposition.'}
    verify_seal()
    receipt = {'schema': 'FixedOrderSoundStoppingExploratoryResultsV1', 'status': 'PASS',
               'completed_utc': datetime.now(timezone.utc).isoformat(),
               'scope': json.loads((ROOT / 'experiment_spec.json').read_text())['scope'],
               'frozen_design_sha256': sha(ROOT / 'FROZEN_DESIGN.json'), 'frozen_inputs': seal,
               'original_files_unchanged': True, 'new_episode_count': len(episodes),
               'development_checks': checks, 'summaries': summaries, 'models': models,
               'stratified_results': stratified, 'descriptive_cost_contrasts': decomposition, 'episodes': episodes,
               'limitations': ['Same outcomes motivated this follow-up; no independent validation.',
                               'Uniform prior, exact AND dependencies and deterministic noiseless observations are assumed.',
                               'Sound stopping is a model-relative inference, not proof of real provider unavailability.',
                               'Residual adaptive gains include avoiding known-bad vault reads, not solely rearranging a complete permutation.',
                               'No new biological experiment, real provider execution, physical mechanism or fourteen-layer inference.']}
    save('results.json', receipt)
    print(json.dumps({'status': 'PASS', 'summaries': summaries, 'descriptive_cost_contrasts': decomposition,
                      'new_episode_count': len(episodes), 'models': models}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze', action='store_true')
    mode.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    freeze() if args.freeze else execute()
