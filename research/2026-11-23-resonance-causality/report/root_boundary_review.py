"""Post-result root review of the two consequential boundary witnesses.

This is not part of the frozen discovery suites. It independently reconstructs
the matrix and raw reaction semantics, importing neither experiment module.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
n, a = 14, 0.5
identity = np.eye(n)
laplacian = 2 * identity - np.roll(identity, 1, axis=1) - np.roll(identity, -1, axis=1)
Q = a * identity + (1-a) * laplacian / 4
A = identity - 0.42 * Q
p = identity[0]
raw = p + A @ (-p)
assert np.allclose(raw[[0, 1, -1]], [0.315, -0.0525, -0.0525], atol=1e-15)
projected = np.maximum(raw, 0)
assert projected.min() == 0 and np.count_nonzero(projected) == 1
assert np.allclose(np.maximum(p + A @ (p-p), 0), p)

# Two different strictly feasible inputs collapse to exactly the same projected
# branch. No assertion of a physical arrow of time is attached to this witness.
x = np.full(n, 0.01)
delta = 0.001 * np.linalg.solve(A, identity[1])
y = x + delta
fx = np.maximum(p + A @ (x-p), 0)
fy = np.maximum(p + A @ (y-p), 0)
assert np.min(y) > 0 and np.linalg.norm(delta) > 0
assert np.max(np.abs(fx-fy)) < 1e-15

model_path = ROOT/'causal/model/token_contract.json'
model = json.loads(model_path.read_text())
keys = [r['key'] for r in model['resources']]
position = {k:i for i,k in enumerate(keys)}
event = next(e for e in model['reactions'] if e['id']=='R-HSA-70449')
def step(state):
    values = dict(zip(keys, state))
    blocked = (any(values[k] < amount for k, amount in event['inputs'].items())
               or any(values[k] < 1 for k in event['active_catalysts']))
    if blocked:
        return 'BLOCK', tuple(state)
    for k, amount in event['inputs'].items(): values[k] -= amount
    for k, amount in event['outputs'].items(): values[k] += amount
    return 'PASS', tuple(values[k] for k in keys)

saved = json.loads((ROOT/'causal/FOLLOWUP_RESULTS.json').read_text())
replayed = []
for witness in saved['extended_intervention_witnesses']:
    pair = witness['original_equivalent_pair']
    states = [pair['first_state'], pair['second_state']]
    before = [step(v)[0] for v in states]
    augmented = []
    for state in states:
        updated = list(state)
        for key, amount in witness['external_supply'].items():
            updated[position[key]] += amount
        augmented.append(step(updated))
    assert before == ['BLOCK', 'BLOCK']
    assert [s for s,v in augmented] == ['BLOCK', 'PASS']
    assert [list(v) for s,v in augmented] == [v['state'] for v in witness['after_supply']]
    replayed.append({'graph':witness['graph'], 'before':before,
                    'after':[s for s,v in augmented],
                    'supply':witness['external_supply']})

receipt = {'schema':'root_boundary_review.v1',
    'executed_utc':datetime.now(timezone.utc).isoformat(), 'status':'PASS',
    'method':'Independent matrix construction and raw-dictionary reaction interpreter; no experiment imports',
    'admissibility':{'raw_nonzero':raw[np.abs(raw)>1e-15].tolist(),
                    'distinct_input_distance':float(np.linalg.norm(delta)),
                    'minimum_second_input':float(y.min()),
                    'projected_output_max_difference':float(np.max(np.abs(fx-fy)))},
    'environment_witnesses':replayed,
    'scope':'Post-result witness checks, not an independent biological validation or new frozen experiment',
    'input_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),
    'reviewer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
target = HERE/'ROOT_BOUNDARY_REVIEW.json'
if target.exists(): raise RuntimeError('Preserve the original review receipt; replay in a copied package')
target.write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(receipt, indent=2))
