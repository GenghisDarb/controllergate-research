"""Finite, model-relative observation acquisition; no external operations.

This adds a conditional-policy interface, not a biological dynamics simulator.
The generic solver is intentionally shared by the reaction-schema adapter:
equal semantic information must not acquire extra power from biological names.
"""
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache


@dataclass(frozen=True)
class Model:
    resource_count: int
    requirements: tuple[tuple[int, ...], ...]

    def __post_init__(self):
        if type(self.resource_count) is not int or not 1 <= self.resource_count <= 4:
            raise ValueError('resource_count must be an integer in 1..4')
        if not 1 <= len(self.requirements) <= 4:
            raise ValueError('one to four routes required')
        for requirement in self.requirements:
            if len(set(requirement)) != len(requirement):
                raise ValueError('duplicate prerequisite')
            if any(type(r) is not int or not 0 <= r < self.resource_count for r in requirement):
                raise ValueError('invalid prerequisite reference')

    @property
    def vault_count(self):
        return 2*len(self.requirements)

    @property
    def worlds(self):
        return tuple(range(1 << self.resource_count))

    def available(self, world, route):
        return all(world & (1 << resource) for resource in self.requirements[route])

    def outcome(self, world, action):
        if action < self.vault_count:
            return int(self.available(world, action//2))
        return int(bool(world & (1 << (action-self.vault_count))))

    def pair_acquired(self, acquired):
        return any(acquired & (3 << (2*r)) == (3 << (2*r))
                   for r in range(len(self.requirements)))

    def any_route_available(self, world):
        return any(self.available(world,r) for r in range(len(self.requirements)))


def compile_reaction_rows(rows, resources):
    """Compile declared AND dependencies only; display names have no semantics.

    Ordinals are stable contract identities, not name-sorted priorities.
    Both biologically named and neutral resource/row strings compile identically.
    """
    if not isinstance(resources, list) or not resources or len(set(resources)) != len(resources):
        raise ValueError('distinct declared resources required')
    if any(not isinstance(r,str) or not r for r in resources):
        raise ValueError('resource identifiers must be nonempty strings')
    mapping = {name:i for i,name in enumerate(resources)}
    if not isinstance(rows,list) or not rows:
        raise ValueError('reaction rows required')
    requirements = []
    for index,row in enumerate(rows):
        if row.get('ordinal') != index:
            raise ValueError('stable contiguous row ordinals required')
        if set(row) != {'ordinal','display_name','requires_all','roles'}:
            raise ValueError('explicit schema required; cannot infer from labels')
        if row['roles'] != ['incident','control'] or not isinstance(row['requires_all'],list):
            raise ValueError('two declared roles and an AND prerequisite list required')
        if any(r not in mapping for r in row['requires_all']):
            raise ValueError('undeclared prerequisite')
        requirements.append(tuple(mapping[r] for r in row['requires_all']))
    return Model(len(resources), tuple(requirements))


def public_state(model, history):
    """Reconstruct knowledge only from paid, recorded observations.

    Returns the posterior support, acquired vaults and attempted action mask.
    UNAVAILABLE is an observation about route execution; it does not name a
    specific absent input. No actual-world parameter is accepted here.
    """
    belief, acquired, attempted = model.worlds, 0, 0
    for action,outcome in history:
        if type(action) is not int or not 0 <= action < model.vault_count+model.resource_count:
            raise ValueError('unknown action')
        if type(outcome) is not int or outcome not in (0,1):
            raise ValueError('invalid observation')
        if attempted & (1 << action):
            raise ValueError('duplicate observation action')
        attempted |= 1 << action
        belief = tuple(w for w in belief if model.outcome(w,action) == outcome)
        if not belief:
            raise ValueError('observations incompatible with declared model')
        if action < model.vault_count and outcome:
            acquired |= 1 << action
    return belief,acquired,attempted


class ConditionalPolicy:
    """Exact finite-horizon contingent planning under the declared uniform prior.

    Maximizes acquisition probability; at equal probability minimizes expected
    actions. An all-unavailable proof is relative to this finite model.
    """
    def __init__(self, model, allow_probes=True):
        self.model = model
        self.action_count = model.vault_count+(model.resource_count if allow_probes else 0)

        @lru_cache(None)
        def solve(belief,acquired,attempted,budget):
            if model.pair_acquired(acquired):
                return Fraction(1),Fraction(0),None,'PAIR_ACQUIRED'
            if all(not model.any_route_available(w) for w in belief):
                return Fraction(0),Fraction(0),None,'UNREACHABLE_UNDER_DECLARED_MODEL'
            if budget == 0:
                return Fraction(0),Fraction(0),None,'BUDGET_EXHAUSTED'
            # Abstention is retained when no positive-probability success policy
            # fits the remaining horizon; it never licenses a causal conclusion.
            best = (Fraction(0),Fraction(0),None,'BUDGET_BOUND_NO_SUCCESS_POLICY')
            for action in range(self.action_count):
                if attempted & (1 << action):
                    continue
                partitions = [tuple(w for w in belief if model.outcome(w,action) == outcome)
                              for outcome in (0,1)]
                # A known unavailable vault or already-known probe has no effect.
                if action < model.vault_count and not partitions[1]:
                    continue
                if action >= model.vault_count and (not partitions[0] or not partitions[1]):
                    continue
                probability,cost = Fraction(0),Fraction(1)
                for outcome,following in enumerate(partitions):
                    if not following:
                        continue
                    weight = Fraction(len(following),len(belief))
                    next_acquired = acquired | (1 << action) if action < model.vault_count and outcome else acquired
                    p,c,_,_ = solve(following,next_acquired,attempted | (1 << action),budget-1)
                    probability += weight*p
                    cost += weight*c
                if probability > best[0] or (probability == best[0] and cost < best[1]):
                    best = probability,cost,action,'COSTED_OBSERVATION_SELECTED'
            return best
        self.solve = solve

    def decide(self, history, remaining_budget):
        if type(remaining_budget) is not int or remaining_budget < 0:
            raise ValueError('invalid remaining budget')
        belief,acquired,attempted = public_state(self.model,history)
        p,c,action,reason = self.solve(belief,acquired,attempted,remaining_budget)
        return {'action':action,'reason':reason,'expected_pair_probability':str(p),
                'expected_remaining_actions':str(c),'belief_world_count':len(belief),
                'authority':'OBSERVATION_ACQUISITION_ONLY'}


def best_frozen_order(model):
    """Exact best permutation of vault reads with success-only early stop.

    At a prefix mask, the probability of still running is determined by which
    route pairs are complete. Sum those probabilities over action positions.
    This subset dynamic program evaluates every permutation implicitly.
    """
    all_vaults = (1 << model.vault_count)-1

    @lru_cache(None)
    def solve(mask):
        if mask == all_vaults:
            return Fraction(0),()
        survivors = sum(not any((mask & (3 << (2*r))) == (3 << (2*r)) and model.available(w,r)
                               for r in range(len(model.requirements))) for w in model.worlds)
        chance = Fraction(survivors,len(model.worlds))
        candidates = []
        for action in range(model.vault_count):
            if not mask & (1 << action):
                later,sequence = solve(mask | (1 << action))
                candidates.append((chance+later,(action,)+sequence))
        return min(candidates)
    return solve(0)


def run_episode(model, world, arm, budget, policy=None, order=None):
    """The environment owns world; policy receives only public model/history.

    This is an interface separation, not a security sandbox for hostile code.
    Every observation below is charged before being passed to the policy.
    """
    if world not in model.worlds:
        raise ValueError('invalid environment state')
    history,trace = [],[]
    terminal = None
    while len(history) <= budget:
        belief,acquired,_ = public_state(model,history)
        if model.pair_acquired(acquired):
            terminal = 'PAIR_ACQUIRED'; break
        if len(history) == budget:
            terminal = 'BUDGET_EXHAUSTED'; break
        if arm == 'UNKNOWN_AS_UNAVAILABLE_NEGATIVE_CONTROL':
            terminal = 'UNKNOWN_COLLAPSED_TO_UNAVAILABLE'; break
        if arm == 'BEST_FROZEN_ORDER':
            action = order[len(history)]
            decision = {'action':action,'reason':'NEXT_FROZEN_ORDER_POSITION'}
        else:
            decision = policy.decide(tuple(history),budget-len(history))
            action = decision['action']
            if action is None:
                terminal = decision['reason']; break
        before = tuple(history)
        outcome = model.outcome(world,action)
        history.append((action,outcome))
        trace.append({'step':len(history),'selection':decision,
                      'history_length_at_selection':len(before),'charged_cost':1,
                      'observation_after_charge':outcome,
                      'observation_kind':'vault' if action < model.vault_count else 'prerequisite'})
    _,acquired,_ = public_state(model,history)
    if terminal == 'UNREACHABLE_UNDER_DECLARED_MODEL':
        assert all(not model.any_route_available(w) for w in belief)
    return {'arm':arm,'actual_world_for_scoring_only':world,'actions':len(history),
            'failed_vault_accesses':sum(a < model.vault_count and not value for a,value in history),
            'prerequisite_probes':sum(a >= model.vault_count for a,_ in history),
            'pair_acquired':model.pair_acquired(acquired),'terminal':terminal,'trace':trace,
            'physical_validation':False,'causal_ownership':False,'patch_authority':False}
