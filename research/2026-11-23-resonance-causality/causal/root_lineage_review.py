"""Third implementation: retain original-state labels through every observation.

This checks the surprising six-state identification result without importing
the experiment or its independent reviewer, and without a no-merging rule.
All hypotheses retain their original identities explicitly.
"""
from pathlib import Path
from collections import deque,defaultdict
import hashlib,json
from datetime import datetime,timezone

P=Path(__file__).resolve().parent
model=json.loads((P/'model/token_contract.json').read_text())
prior=json.loads((P/'model/prior_seed_spec.json').read_text())
keys=[r['key'] for r in model['resources']];pos={k:i for i,k in enumerate(keys)}
seed=next(r for r in prior['seeds'] if r['id']=='recycling_seed')
start=tuple(seed['overrides'].get(r['key'],seed['metabolite_default'] if r['role']=='metabolite_count' else seed['catalyst_default']) for r in model['resources'])
def execute(x,event):
    v=dict(zip(keys,x))
    if any(v[k]<n for k,n in event['inputs'].items()) or any(v[k]<1 for k in event['active_catalysts']):return 'BLOCK',x
    for k,n in event['inputs'].items():v[k]-=n
    for k,n in event['outputs'].items():v[k]+=n
    return 'PASS',tuple(v[k] for k in keys)
states={start};todo=[start]
while todo:
    x=todo.pop()
    for event in model['reactions']:
        _,y=execute(x,event)
        if y not in states:states.add(y);todo.append(y)
states=sorted(states);index={x:i for i,x in enumerate(states)}
saved=json.loads((P/'results.json').read_text())
assert states==[tuple(x) for x in saved['graphs']['recycling_seed']['states']]

out={}
for status_seen in [False,True]:
    channels={}
    for y in sorted({x[pos['LACT_e']] for x in states}):
        root=tuple(i if x[pos['LACT_e']]==y else -1 for i,x in enumerate(states))
        found={root};q=deque([root]);trans={}
        while q:
            hypothesis=q.popleft();action_rows=[]
            for event in model['reactions']:
                by_output={}
                for origin,current in enumerate(hypothesis):
                    if current<0:continue
                    status,xn=execute(states[current],event)
                    obs=(xn[pos['LACT_e']],status) if status_seen else (xn[pos['LACT_e']],)
                    by_output.setdefault(obs,[-1]*len(states))[origin]=index[xn]
                successors=[tuple(v) for v in by_output.values()]
                action_rows.append(successors)
                for nxt in successors:
                    if nxt not in found:found.add(nxt);q.append(nxt)
            trans[hypothesis]=action_rows
            assert len(found)<200000
        checks={}
        for label,goal in [('initial_identity',lambda h:sum(v>=0 for v in h)==1),('current_state',lambda h:len({v for v in h if v>=0})==1)]:
            won={h:0 for h in found if goal(h)}
            while True:
                more={}
                for h in found-won.keys():
                    costs=[1+max(won[n] for n in row) for row in trans[h] if all(n in won for n in row)]
                    if costs:more[h]=min(costs)
                if not more:break
                won.update(more)
            checks[label]={'guaranteed':root in won,'worst_case_commands':won.get(root)}
        channels[str(y)]={'lineage_states':len(found),'checks':checks}
    out['with_status' if status_seen else 'readout_only']=channels
assert out['readout_only']['0']['checks']['initial_identity']['guaranteed'] is False
assert out['readout_only']['0']['checks']['current_state']['worst_case_commands']==3
assert out['with_status']['0']['checks']['initial_identity']['worst_case_commands']==3
receipt={'schema':'root_origin_label_review.v1','executed_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS',
 'method':'Fresh raw-dictionary event parser, reachable graph, explicit (original identity -> current state) hypothesis machine and finite reachability game; no experiment/reviewer code imports and no inferred nonmerging shortcut.',
 'scope':'Six-state external-lactate observer; critical all-pairs-versus-guaranteed-identification distinction',
 'states':len(states),'results':out,'source_sha256':hashlib.sha256((P/'model/token_contract.json').read_bytes()).hexdigest(),
 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(P/'ROOT_LINEAGE_REVIEW.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
