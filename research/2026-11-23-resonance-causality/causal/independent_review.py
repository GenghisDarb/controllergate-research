"""Independent finite-machine review using dictionaries and backward pair marking.

Does not import causal_history.py. Rebuilds all transitions and reachable sets;
uses pair-table fixed points rather than the original pair BFS/refinement.
"""
from pathlib import Path
from itertools import combinations,product
from collections import defaultdict,Counter
from datetime import datetime,timezone
import hashlib,json

ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

payload=json.loads((ROOT/'model/token_contract.json').read_text())
prior=json.loads((ROOT/'model/prior_seed_spec.json').read_text())
results=json.loads((ROOT/'results.json').read_text())
frozen=json.loads((ROOT/'FROZEN_DESIGN.json').read_text())
assert all(sha(ROOT/k)==v for k,v in frozen['files'].items())
keys=tuple(x['key'] for x in payload['resources'])
met=tuple(x['key'] for x in payload['resources'] if x['role']=='metabolite_count')
cat=tuple(x['key'] for x in payload['resources'] if x['role']=='asserted_active_catalytic_role')
events={x['id']:x for x in payload['reactions']}

def transition(x,event):
    inventory=dict(zip(keys,x));raw=events[event]
    missing=[k for k,n in raw['inputs'].items() if inventory[k]<n]
    missing += [k for k in raw['active_catalysts'] if inventory[k]<1]
    if missing:return 'BLOCK',x
    nxt={k:inventory[k]+raw['outputs'].get(k,0)-raw['inputs'].get(k,0) for k in keys}
    return 'PASS',tuple(nxt[k] for k in keys)

def independent_graph(seed):
    initial=tuple(seed['overrides'].get(k,seed['metabolite_default'] if k in met else seed['catalyst_default']) for k in keys)
    seen={initial};frontier=[initial];edges=set()
    while frontier:
        x=frontier.pop()
        for e in events:
            status,y=transition(x,e)
            if status=='PASS':
                edges.add((x,e,y))
                if y not in seen:seen.add(y);frontier.append(y)
    return sorted(seen),edges

def review_case(states,columns,status_visible,saved):
    lookup={x:i for i,x in enumerate(states)}
    observations=[tuple(dict(zip(keys,x))[k] for k in columns) for x in states]
    transitions={}
    for i,x in enumerate(states):
        for e in events:
            status,y=transition(x,e);j=lookup[y]
            response=(status,observations[j]) if status_visible else observations[j]
            transitions[i,e]=(response,j)
    # Backward marking obtains shortest discriminating word lengths, using
    # equality of current observations as length-zero behavior.
    pairs=list(combinations(range(len(states)),2));dist={p:0 for p in pairs if observations[p[0]]!=observations[p[1]]}
    while True:
        additions={}
        for i,j in pairs:
            if (i,j) in dist:continue
            opts=[]
            for e in events:
                a,ii=transitions[i,e];b,jj=transitions[j,e]
                if a!=b:opts.append(1)
                else:
                    nxt=(min(ii,jj),max(ii,jj))
                    if nxt in dist:opts.append(1+dist[nxt])
            if opts:additions[i,j]=min(opts)
        if not additions:break
        dist.update(additions)
    equiv=[p for p in pairs if p not in dist]
    # Exact class count via pair relation, without original partition algorithm.
    classes=[]
    for i in range(len(states)):
        for block in classes:
            pair=(min(i,block[0]),max(i,block[0]))
            if pair not in dist:block.append(i);break
        else:classes.append([i])
    assert len(classes)==saved['future_behavior_classes']
    assert len(equiv)==saved['future_equivalent_unordered_pairs']
    hist=Counter(d for p,d in dist.items() if observations[p[0]]==observations[p[1]])
    assert {str(k):v for k,v in sorted(hist.items())}==saved['shortest_distinguishing_word_histogram']
    levels=[]
    for depth in range(max(dist.values(),default=0)+1):
        blocks=[]
        for i in range(len(states)):
            for block in blocks:
                pair=(min(i,block[0]),max(i,block[0]))
                if pair not in dist or dist[pair]>depth:block.append(i);break
            else:blocks.append([i])
        levels.append(len(blocks))
    assert levels==saved['refinement_class_counts']
    # Independent reachable powerset graph for command/response histories.
    roots={frozenset(i for i,o in enumerate(observations) if o==v) for v in observations}
    discovered=set(roots);frontier=list(roots);table={}
    while frontier:
        b=frontier.pop()
        for e in events:
            outcomes=defaultdict(list)
            for i in b:
                response,j=transitions[i,e];outcomes[response].append(j)
            rows=[(frozenset(v),len(v)==len(set(v))) for v in outcomes.values()]
            table[b,e]=rows
            for nxt,_ in rows:
                if nxt not in discovered:discovered.add(nxt);frontier.append(nxt)
    assert len(discovered)==saved['history']['belief_nodes']
    assert len(roots)==saved['history']['initial_fibers']
    class_id={i:c for c,block in enumerate(classes) for i in block}
    for label,merge_allowed in [('current_state',True),('predictive_class',True),('initial_state',False)]:
        if label=='predictive_class':goal=lambda b:len({class_id[i] for i in b})==1
        else:goal=lambda b:len(b)==1
        values={b:0 for b in discovered if goal(b)}
        for depth in range(1,len(discovered)+1):
            frontier=[]
            for b in discovered-values.keys():
                options=[]
                for e in events:
                    rows=table[b,e]
                    if not merge_allowed and any(not inj for _,inj in rows):continue
                    if all(nxt in values for nxt,_ in rows):options.append(1+max(values[nxt] for nxt,_ in rows))
                if options:frontier.append((b,min(options)))
            if not frontier:break
            values.update(frontier)
        expected=saved['history'][label]
        assert len(values)==expected['winning_beliefs']
        assert sum(b in values for b in roots)==expected['roots_guaranteed']
        assert max((values[b] for b in roots if b in values),default=None)==expected['max_guaranteed_root_steps']
        ordered_roots=sorted(roots,key=lambda b:observations[min(b)])
        assert [values.get(b) for b in ordered_roots]==expected['root_depths']
    return {'states':len(states),'classes':len(classes),'beliefs':len(discovered),'pair_table_pairs':len(pairs),'status':'PASS'}

checks={};state_total=0
for seed in prior['seeds']:
    states,edges=independent_graph(seed);saved_graph=results['graphs'][seed['id']]
    assert [list(s) for s in states]==saved_graph['states']
    assert len(edges)==saved_graph['enabled_edges']
    checks[seed['id']]={'source_states':len(states),'source_enabled_edges':len(edges),'cases':{}}
    for name,saved in saved_graph['fixed_context'].items():
        label,ch=name.split('|');cols=[] if label=='empty' else label.split('+')
        checks[seed['id']]['cases'][name]=review_case(states,cols,ch=='readout_and_status',saved)
    hidden=[]
    for x in states:
        for mask in product((0,1),repeat=3):
            row=dict(zip(keys,x));row.update(zip(cat,mask));hidden.append(tuple(row[k] for k in keys))
    hidden=sorted(set(hidden))
    for name,saved in saved_graph['context_extension'].items():
        if not isinstance(saved,dict):continue
        label,ch=name.split('|');cols=['GA3P_c','PYR_c','LACT_e']+(list(cat) if label=='mask_known' else [])
        checks[seed['id']]['cases'][name]=review_case(hidden,cols,ch=='readout_and_status',saved)

receipt={'schema':'independent_action_history_review.v1','result':'PASS','executed_utc':datetime.now(timezone.utc).isoformat(),'method':'Raw dictionary source semantics, separate graph traversal, backward state-pair distinguishing table, separate reachable belief graph and finite-horizon game iteration; no experiment code imported.','case_count':sum(len(g['cases']) for g in checks.values()),'checks':checks,'source_hashes':{p:sha(ROOT/p) for p in ['model/token_contract.json','EXPERIMENT_SPEC.json','FROZEN_DESIGN.json','causal_history.py','results.json','independent_review.py']},'limits':['Independent implementation checking within the same declared source model; not independent biological evidence.','Command counts are not physical time.','Initial-state identification is distinct from current-state convergence.']}
(ROOT/'INDEPENDENT_REVIEW.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'result':receipt['result'],'case_count':receipt['case_count'],'original_graphs':{k:(v['source_states'],v['source_enabled_edges']) for k,v in checks.items()}},indent=2))
