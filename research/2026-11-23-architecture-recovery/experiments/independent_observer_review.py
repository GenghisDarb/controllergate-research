"""Independent review of the frozen observer extension.

Parses the raw JSON contract anew. Does not call the experiment's source oracle,
graph traversal, rank calculation, observation audit or local-case generator.
The role-shell implementation is imported only as the object under test.
"""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations, product
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import sys
import sympy as sp

HERE=Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    payload=json.loads((HERE/'model/token_contract.json').read_text())
    spec=json.loads((HERE/'experiment_spec.json').read_text())
    saved=json.loads((HERE/'results.json').read_text())
    frozen=json.loads((HERE/'FROZEN_EXTENSION.json').read_text())
    hashes={name:sha(HERE/name)==value for name,value in frozen['files'].items()}
    assert all(hashes.values())
    resources=payload['resources']; keys=[row['key'] for row in resources]
    pos={key:i for i,key in enumerate(keys)}
    chemicals={row['key']:row['chemical'] for row in resources}
    met=[i for i,row in enumerate(resources) if row['role']=='metabolite_count']
    cat=[i for i,row in enumerate(resources) if row['role']=='asserted_active_catalytic_role']
    events={r['id']:r for r in payload['reactions']}

    # Independent raw-contract parser produces dense coefficients and read arcs.
    parsed={}
    for event,raw in events.items():
        take=[raw['inputs'].get(key,0) for key in keys]
        give=[raw['outputs'].get(key,0) for key in keys]
        read=[int(key in raw['active_catalysts']) for key in keys]
        assert all(take[i]==give[i]==0 for i in cat)
        parsed[event]=(tuple(take),tuple(give),tuple(read))

    def reference(event,x):
        take,give,read=parsed[event]
        enabled=all(a>=need and a>=role for a,need,role in zip(x,take,read))
        return ('PASS',tuple(a-need+out for a,need,out in zip(x,take,give))) if enabled else ('BLOCK',x)

    def enabled_pattern(x):
        return tuple(reference(event,x)[0] for event in events)

    def traversal(initial):
        found={initial};frontier={initial};edges=set()
        while frontier:
            following=set()
            for x in frontier:
                for event in events:
                    status,y=reference(event,x)
                    if status=='PASS':
                        edges.add((x,event,y))
                        if y not in found: following.add(y)
            found|=following;frontier=following
            assert len(found)<=10000
        return found,edges

    matrix=sp.Matrix([[give[i]-take[i] for take,give,_ in parsed.values()] for i in met])
    forward=['R-HSA-70449','R-HSA-71849','R-HSA-373875']
    selected=[list(events).index(event) for event in forward]
    basis=matrix[:,selected]
    obskeys=[key for row in spec['observers'].values() for key in row]
    metkeys=[keys[i] for i in met]
    CB=basis[[metkeys.index(key) for key in obskeys],:]
    rank=int(matrix.rank());nullity=len(matrix.T.nullspace())
    assert rank==saved['linear_structure']['exact_rank']==3
    assert nullity==saved['linear_structure']['linear_conservation_dimension']==7
    assert CB==sp.diag(-1,-1,1)
    assert matrix.tolist()==saved['linear_structure']['stoichiometric_matrix']
    sufficient_triples=[tuple(metkeys[i] for i in rows) for rows in combinations(range(len(met)),3) if basis[list(rows),:].det()!=0]

    implementation_spec=importlib.util.spec_from_file_location('reviewed_observer_extension',HERE/'observer_interlock.py')
    impl=importlib.util.module_from_spec(implementation_spec)
    sys.modules[implementation_spec.name]=impl
    implementation_spec.loader.exec_module(impl)
    shell=impl.RoleShell(payload)

    grid_cases=grid_enabled=grid_mismatch=0
    for event,raw in events.items():
        support=set(raw['inputs'])|set(raw['outputs'])|set(raw['active_catalysts'])
        support=sorted(support)
        active_chem={chemicals[k] for k in support}
        remote=[k for k in keys if k not in support and chemicals[k] in active_chem]
        for outside in ((0,2) if remote else (0,)):
            for row in product((0,1,2),repeat=len(support)):
                x=[0]*len(keys)
                for key,value in zip(support,row):x[pos[key]]=value
                for key in remote:x[pos[key]]=outside
                x=tuple(x);truth=reference(event,x);actual=shell.step(event,x)
                grid_cases+=1;grid_enabled+=truth[0]=='PASS'
                grid_mismatch+=(actual.status,actual.inventory)!=truth
    assert (grid_cases,grid_enabled,grid_mismatch)==(12150,2592,0)

    graphs={}
    for seed in spec['seeds']:
        initial=tuple(seed['overrides'].get(key,seed['metabolite_default'] if i in met else seed['catalyst_default']) for i,key in enumerate(keys))
        nodes,edges=traversal(initial)
        old=saved['graphs'][seed['id']]
        old_edges={(tuple(e['before']),e['event'],tuple(e['after'])) for e in old['edges']}
        assert nodes=={tuple(x) for x in old['states']}
        assert edges==old_edges
        assert len(nodes)==old['state_count'] and len(edges)==old['directed_edges']
        reverses=all((y,events[event]['reverse_event'],x) in edges for x,event,y in edges)
        assert reverses
        obs_stats={}
        names=list(spec['observers'])
        for count in range(1,len(names)+1):
            for subset in combinations(names,count):
                name='+'.join(subset)
                columns=[key for n in subset for key in spec['observers'][n]]
                bucket=defaultdict(list)
                for x in nodes:bucket[tuple(x[pos[key]] for key in columns)].append(x)
                collisions=sum(len(group)*(len(group)-1) for group in bucket.values())
                patterns=[Counter(enabled_pattern(x) for x in group) for group in bucket.values()]
                ambiguity=sum(len(c)>1 for c in patterns)
                minimum_errors=sum(sum(c.values())-max(c.values()) for c in patterns)
                stats={'observation_fibers':len(bucket),'false_full_return_ordered_distinct_pairs':collisions,'ambiguous_enabledness_fibers':ambiguity,'minimum_enabledness_pattern_errors_uniform_states':minimum_errors}
                assert all(old['observations'][name][key]==value for key,value in stats.items())
                obs_stats[name]=stats
        before=tuple(old['catalyst_off_intervention']['before'])
        after=tuple(old['catalyst_off_intervention']['after'])
        assert before in nodes
        assert before!=after and all(before[i]==after[i] for i in met)
        assert all(after[i]==0 for i in cat)
        assert sum(status=='PASS' for status in enabled_pattern(before))>0
        assert all(status=='BLOCK' for status in enabled_pattern(after))
        assert after not in nodes  # external context change, not one of six reactions
        graphs[seed['id']]={'states':len(nodes),'edges':len(edges),'all_nodes_and_edges_match':True,'every_edge_has_curated_reverse':reverses,'all_observation_statistics_match':True,'observations':obs_stats,'off_intervention_changes_full_context_without_metabolite_change':True,'off_intervention_not_reachable_under_six_reactions':True}

    # Recompute certification controls against independently constructed truth.
    event='R-HSA-71849';raw=events[event]
    x=[0]*len(keys)
    for key,n in raw['inputs'].items():x[pos[key]]=n
    for key in raw['active_catalysts']:x[pos[key]]=1
    x=tuple(x);status,y=reference(event,x)
    assert status=='PASS'
    pr=shell.propose(event,x)
    good=impl.Result('PASS',y,'independent reference')
    bad_y=list(y);bad_y[pos['PYR_c']]+=1
    bad_cat=list(y);bad_cat[pos[raw['active_catalysts'][0]]]=0
    cases={
        'valid':(pr,good,True),
        'stale_snapshot':(impl.Proposal(event,'wrong',shell.contract),good,False),
        'wrong_model_hash':(impl.Proposal(event,pr.snapshot,'wrong'),good,False),
        'unknown_event':(impl.Proposal('unknown',pr.snapshot,shell.contract),good,False),
        'wrong_metabolite_successor':(pr,impl.Result('PASS',tuple(bad_y),'mutant'),False),
        'catalyst_consumption':(pr,impl.Result('PASS',tuple(bad_cat),'mutant'),False),
        'wrong_block_status':(pr,impl.Result('BLOCK',x,'mutant'),False),
    }
    controls={name:shell.certify(proposal,x,candidate)==expected for name,(proposal,candidate,expected) in cases.items()}
    assert all(controls.values())
    receipt={
        'schema':'independent_observer_review.v1',
        'executed_utc':datetime.now(timezone.utc).isoformat(),
        'result':'PASS_WITH_STATED_SCOPE',
        'method':'Independent raw-JSON dense stoichiometry/read-arc parser, set-frontier reachability, SymPy exact algebra and observation fibers. Implementation imported only as system under test; no implementation oracle/graph/rank/case generator reused.',
        'source_hashes':{p:sha(HERE/p) for p in ['observer_interlock.py','experiment_spec.json','FROZEN_EXTENSION.json','model/token_contract.json','results.json','independent_observer_review.py']},
        'frozen_files_match':hashes,
        'local_grid':{'cases':grid_cases,'source_enabled':grid_enabled,'shell_disagreements':grid_mismatch},
        'linear_algebra':{'rank':rank,'left_nullity':nullity,'observer_basis_matrix':CB.tolist(),'observer_basis_determinant':int(CB.det()),'all_three_readout_subsets_tested':120,'other_sufficient_readout_triples_count':len(sufficient_triples)-1,'all_sufficient_triples':sufficient_triples},
        'graphs':graphs,'certification_controls':controls,
        'scope_notes':[
            'Joint observability is conditional on fixed stoichiometric class and known catalytic context. It is not global injectivity over arbitrary inventories.',
            'Three readouts are one sufficient choice; alternative independent triples exist. No unique biological triad is selected.',
            'Ordered collision-pair counts are ambiguity witnesses over finite reachable states, not empirical false-positive rates.',
            'Uniform-state minimum pattern errors are a finite combinatorial lower bound under that specified weighting, not kinetic prediction accuracy.',
            'Pure functional commit supplies no cross-process transaction isolation, authenticated provenance or physical causal closure.',
            'Agreement on the 12150 fixed known-state cases and two finite reachability classes does not extend to all unknown/large-integer states; the archived float guard retains its stated exact-integer range restriction.',
            'The frozen source oracle can require PASS beyond the archived backend exact range and reject a backend UNRESOLVED there; this wrapper is validated here only in the small-count domain.',
            'No14-selection, physical dimension, reaction-rate, thermodynamic or quantum-observer conclusion follows.',
            'Local recorded hash freeze is not an external preregistration authority.'
        ]
    }
    (HERE/'INDEPENDENT_OBSERVER_REVIEW.json').write_text(json.dumps(receipt,indent=2,default=lambda v:int(v))+"\n")
    print(json.dumps({'result':receipt['result'],'grid':receipt['local_grid'],'graphs':{k:(v['states'],v['edges']) for k,v in graphs.items()},'exact_rank':rank,'alternative_sufficient_triples':len(sufficient_triples)-1,'receipt':str(HERE/'INDEPENDENT_OBSERVER_REVIEW.json')}))

if __name__=='__main__':main()
