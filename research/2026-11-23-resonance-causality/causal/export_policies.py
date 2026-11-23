"""Export concrete adaptive policies from the already-tested finite game.

This is a derived explanation artifact, not a new primary hypothesis test.
Reuses the frozen experiment's policy implementation and replays each initial
state to expose the actual action/response traces underlying its guarantees.
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import hashlib,json
from causal_history import parse,refine,belief_machine,winning_strategy

ROOT=Path(__file__).resolve().parent
payload=json.loads((ROOT/'model/token_contract.json').read_text())
saved=json.loads((ROOT/'results.json').read_text())
keys,pos,actions,step=parse(payload)
export=[]
for graph,column in [('all_metabolites_one','GA3P_c'),('recycling_seed','LACT_e')]:
    states=[tuple(x) for x in saved['graphs'][graph]['states']];ids={x:i for i,x in enumerate(states)}
    observations=[(x[pos[column]],) for x in states];nexts=[];responses=[]
    for x in states:
        nr=[];rr=[]
        for a in range(len(actions)):
            status,y=step(x,a);j=ids[y];nr.append(j);rr.append((status,observations[j]))
        nexts.append(nr);responses.append(rr)
    machine=belief_machine(observations,nexts,responses,50000)
    ranks,policy=winning_strategy(machine,lambda b:len(b)==1,forbid_merging=True)
    assert all(b in ranks for b in machine['roots'])
    traces=[]
    for initial in range(len(states)):
        belief=next(b for b in machine['roots'] if initial in b);lineage={i:i for i in belief};current=initial;history=[]
        while len(belief)>1:
            a=policy[belief];output=responses[current][a]
            nxt=next(n for o,n,_ in machine['transition'][belief][a] if o==output)
            assert ranks[nxt]<ranks[belief]
            lineage={i:nexts[j][a] for i,j in lineage.items() if responses[j][a]==output}
            current=nexts[current][a]
            history.append({'action':actions[a][0],'response':output,'belief_before':belief,'belief_after':nxt})
            belief=nxt
        assert list(lineage)==[initial] and set(lineage.values())=={current}
        traces.append({'initial_state_id':initial,'final_state_id':current,'initial_state_identified':True,'commands':len(history),'history':history})
    expected=saved['graphs'][graph]['fixed_context'][column+'|readout_and_status']['history']['initial_state']['max_guaranteed_root_steps']
    assert max(t['commands'] for t in traces)==expected
    export.append({'graph':graph,'observation':column,'status_observed':True,'guarantee':'Identify initial and current state for every allowed initial hypothesis; no state-merging within an identical response','worst_case_commands':expected,'all_initial_state_replays':traces})
out={'schema':'derived_adaptive_policy_examples.v1','executed_utc':datetime.now(timezone.utc).isoformat(),'status':'All original initial states replayed successfully under exported adaptive policies','source':'Derived from the frozen primary deterministic game; not independent verification','policies':export,'hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['causal_history.py','results.json','export_policies.py']}}
(ROOT/'POLICY_EXAMPLES.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'policies':len(export),'initial_states_replayed':sum(len(x['all_initial_state_replays']) for x in export),'worst_case_commands':[x['worst_case_commands'] for x in export]},indent=2))
