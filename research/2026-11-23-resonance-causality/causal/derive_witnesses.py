"""Post-result explanatory witnesses; original frozen experiment remains unchanged."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import json,hashlib

ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'model/token_contract.json').read_text())
results=json.loads((ROOT/'results.json').read_text())
keys=[r['key'] for r in raw['resources']];events={r['id']:r for r in raw['reactions']}

def step(x,event):
    v=dict(zip(keys,x));r=events[event]
    if any(v[k]<n for k,n in r['inputs'].items()) or any(v[k]<1 for k in r['active_catalysts']):return 'BLOCK',tuple(x)
    return 'PASS',tuple(v[k]-r['inputs'].get(k,0)+r['outputs'].get(k,0) for k in keys)

states=[tuple(x) for x in results['graphs']['recycling_seed']['states']];ids={x:i for i,x in enumerate(states)}
col=keys.index('LACT_e')
initial=tuple(i for i,x in enumerate(states) if x[col]==0)
trap=(0,1,4,5)
certificate=[]
for belief in [initial,trap]:
    actions=[]
    for event in events:
        groups=defaultdict(list)
        for i in belief:
            status,y=step(states[i],event);groups[y[col]].append({'before_id':i,'after_id':ids[y],'status':status})
        outcomes=[];merges=False
        for output,rows in sorted(groups.items()):
            following=tuple(sorted({r['after_id'] for r in rows}));injective=len(rows)==len(following)
            merges |= not injective
            outcomes.append({'external_lactate':output,'following':following,'injective':injective,'transitions':rows})
        if merges:kind='merges initial hypotheses under an identical observation'
        else:
            assert any(tuple(o['following']) in (initial,trap) for o in outcomes)
            kind='has a response branch staying in the certified nonidentifying set'
        actions.append({'event':event,'reason_no_guaranteed_initial_identification':kind,'outcomes':outcomes})
    certificate.append({'belief':belief,'actions':actions})

extensions=[]
for name,g in results['graphs'].items():
    w=g['context_extension']['mask_hidden|readout_and_status']['first_future_equivalent_witness']
    x,y=tuple(w['first_state']),tuple(w['second_state'])
    vx,vy=dict(zip(keys,x)),dict(zip(keys,y))
    event=next(e for e,r in events.items() if any(vx[k]!=vy[k] for k in r['active_catalysts']))
    supplied={k:max(0,n-vx[k]) for k,n in events[event]['inputs'].items() if vx[k]<n}
    # The same supplied material is added to both otherwise identical metabolite states.
    xx=tuple(vx[k]+supplied.get(k,0) for k in keys);yy=tuple(vy[k]+supplied.get(k,0) for k in keys)
    before=[step(x,event)[0],step(y,event)[0]];after=[step(xx,event),step(yy,event)]
    assert before[0]==before[1] and after[0][0]!=after[1][0]
    extensions.append({'graph':name,'original_equivalent_pair':w,'external_supply':supplied,'tested_command':event,'statuses_before_supply':before,'after_supply':[{'status':s,'state':v} for s,v in after],'scope':'New external material supply changes the allowed dynamics and conservation class. It exposes a previously silent catalyst difference; it is not a counterexample within the original closed six-command model.'})

out={'schema':'causal_scope_followup_results.v1','executed_utc':datetime.now(timezone.utc).isoformat(),'followup':'post-result explanatory diagnostics, not original frozen primary outcomes','initial_identification_impossibility':{'observer':'LACT_e only; PASS/BLOCK not observed','initial_belief':initial,'trap_belief':trap,'certificate':certificate,'proof':'Every possible first command either irreversibly merges at least two initial hypotheses within one output branch, or admits a branch that stays inside these nonsingleton beliefs. Hence no finite adaptive strategy identifies the initial state for every possible outcome.'},'extended_intervention_witnesses':extensions,'input_hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['FOLLOWUP_SPEC.json','results.json','model/token_contract.json','derive_witnesses.py']}}
(ROOT/'FOLLOWUP_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'impossibility_certificate':'PASS','external_supply_witnesses':len(extensions),'supplies':[r['external_supply'] for r in extensions]},indent=2))
