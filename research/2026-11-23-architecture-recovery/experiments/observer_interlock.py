"""Exact finite model extension: observation, functional roles and composition.

No empirical rates, measured biology, or universal layer-count claim is supplied.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'model'))
from token_translation import FaithfulTranslation, GenericIncidence, Result, load_model, state_from

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def exact_rank(matrix):
    a=[[Fraction(v) for v in row] for row in matrix]
    if not a:return 0
    row=0
    for col in range(len(a[0])):
        pivot=next((i for i in range(row,len(a)) if a[i][col]),None)
        if pivot is None:continue
        a[row],a[pivot]=a[pivot],a[row]
        v=a[row][col];a[row]=[x/v for x in a[row]]
        for i in range(len(a)):
            if i!=row:
                v=a[i][col];a[i]=[x-v*y for x,y in zip(a[i],a[row])]
        row+=1
        if row==len(a):break
    return row

@dataclass(frozen=True)
class Proposal:
    event: str
    snapshot: str
    contract: str

class RoleShell:
    """Three functional services around an atomic commit, not three catalysts."""
    def __init__(self,payload):
        self.payload=payload;self.model=load_model(payload)
        self.contract=digest(payload)
        self.raw={r['id']:r for r in payload['reactions']}
        self.events={r.identifier:r for r in self.model.reactions}
        self.backend=FaithfulTranslation(self.model)

    def propose(self,event,state):
        if event not in self.events:raise ValueError('undeclared event')
        return Proposal(event,digest(state),self.contract)

    def reconcile(self,proposal,state):
        if proposal.contract!=self.contract or proposal.snapshot!=digest(state):
            raise ValueError('proposal does not bind the current state/model')
        return self.backend.step(self.events[proposal.event],state)

    def certify(self,proposal,before,candidate):
        if (proposal.event not in self.raw or proposal.snapshot!=digest(before)
                or proposal.contract!=self.contract):return False
        expected=source_reference(self.payload,proposal.event,before)
        return candidate.status==expected.status and candidate.inventory==expected.inventory

    def commit(self,proposal,before,candidate):
        if not self.certify(proposal,before,candidate):
            return Result('REJECT',before,'source-transition certificate rejected')
        return candidate

    def step(self,event,state):
        proposal=self.propose(event,state)
        return self.commit(proposal,state,self.reconcile(proposal,state))

def source_reference(payload,event,state):
    """Independent direct raw-JSON interpretation; no imported source oracle."""
    keys=[r['key'] for r in payload['resources']]
    vals=dict(zip(keys,state));r=next(x for x in payload['reactions'] if x['id']==event)
    requirements=list(r['inputs'].items())+[(c,1) for c in r['active_catalysts']]
    if any(vals[k] is not None and vals[k]<n for k,n in requirements):
        return Result('BLOCK',state,'known prerequisite absent')
    touched=set(r['inputs'])|set(r['outputs'])|set(r['active_catalysts'])
    if any(vals[k] is None for k in touched):return Result('UNRESOLVED',state,'unknown')
    for k,n in r['inputs'].items():vals[k]-=n
    for k,n in r['outputs'].items():vals[k]+=n
    return Result('PASS',tuple(vals[k] for k in keys),'source raw coefficients')

def local_cases(model):
    for r in model.reactions:
        support=sorted({p for p,_ in r.inputs+r.outputs}|set(r.catalysts))
        chemicals={model.chemical[p] for p in support}
        remote=sorted(p for p in model.places if p not in support and model.chemical[p] in chemicals)
        for amount in ([0,2] if remote else [0]):
            for counts in itertools.product((0,1,2),repeat=len(support)):
                supplied=dict(zip(support,counts));supplied.update({p:amount for p in remote})
                yield r,state_from(model,supplied)

def enumerate_graph(payload,model,initial):
    seen={initial};q=deque([initial]);edges=[]
    while q:
        x=q.popleft()
        for r in model.reactions:
            y=source_reference(payload,r.identifier,x)
            if y.status=='PASS':
                edges.append((x,r.identifier,y.inventory))
                if y.inventory not in seen:
                    seen.add(y.inventory);q.append(y.inventory)
                    if len(seen)>10000:raise RuntimeError('predeclared state cap exceeded')
    return sorted(seen),edges

def audit_observation(payload,model,states,columns):
    indices=[model.places.index(k) for k in columns];fibers=defaultdict(list)
    for x in states:fibers[tuple(x[i] for i in indices)].append(x)
    ambiguous=0;errors=0;witness=None
    false_pairs=0
    for obs,group in sorted(fibers.items()):
        false_pairs+=len(group)*(len(group)-1)
        targets=Counter(tuple(source_reference(payload,r.identifier,x).status for r in model.reactions) for x in group)
        ambiguous+=len(targets)>1;errors+=len(group)-max(targets.values())
        if len(group)>1 and witness is None:
            witness={'observation':obs,'first':group[0],'second':group[1]}
    return {'columns':columns,'states':len(states),'observation_fibers':len(fibers),
            'false_full_return_ordered_distinct_pairs':false_pairs,
            'ambiguous_enabledness_fibers':ambiguous,'minimum_enabledness_pattern_errors_uniform_states':errors,
            'example_same_observation_different_full_state':witness}

def verify_freeze():
    f=json.loads((ROOT/'FROZEN_EXTENSION.json').read_text())
    for name,sha in f['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:
            raise RuntimeError('frozen source changed: '+name)
    return hashlib.sha256((ROOT/'FROZEN_EXTENSION.json').read_bytes()).hexdigest()

def main():
    target=ROOT/'results.json'
    if target.exists():raise RuntimeError('preserve original output; use a fresh copied directory')
    frozen=verify_freeze();spec=json.loads((ROOT/'experiment_spec.json').read_text())
    payload=json.loads((ROOT/'model/token_contract.json').read_text());model=load_model(payload)
    shell=RoleShell(payload);generic=GenericIncidence(model)
    metabolites=[r['key'] for r in payload['resources'] if r['role']=='metabolite_count']
    catalysts=[r['key'] for r in payload['resources'] if r['role']=='asserted_active_catalytic_role']
    columns=[]
    for r in payload['reactions']:
        columns.append([r['outputs'].get(k,0)-r['inputs'].get(k,0) for k in metabolites])
    matrix=[list(row) for row in zip(*columns)]
    basis_ids=['R-HSA-70449','R-HSA-71849','R-HSA-373875']
    basis=[[matrix[i][[r.identifier for r in model.reactions].index(k)] for k in basis_ids] for i in range(len(metabolites))]
    observer_keys=[k for group in spec['observers'].values() for k in group]
    restricted=[basis[metabolites.index(k)] for k in observer_keys]
    result={'schema':'architecture_observation_results.v1','freeze_sha256':frozen,
            'architecture':{'metabolite_coordinates':len(metabolites),'catalyst_context_assertions':len(catalysts),
                            'coupling_commit_boundaries':1,'role_inspired_shell_services':['propose','reconcile','certify'],
                            'role_warning':'services are not catalyst places; this is a new role-inspired factorization, not a recovered fourteen-stage derivation'},
            'linear_structure':{'metabolite_order':metabolites,'event_order':[r.identifier for r in model.reactions],
                                'stoichiometric_matrix':matrix,'exact_rank':exact_rank(matrix),
                                'linear_conservation_dimension':len(metabolites)-exact_rank(matrix),
                                'basis_events':basis_ids,'observer_order':observer_keys,
                                'observer_on_basis_matrix':restricted,'observer_rank':exact_rank(restricted)},
            'local_cases':{'cases':0,'source_enabled':0,'role_shell_disagreements':0,'generic_disagreements':0},'graphs':{}}
    for r,x in local_cases(model):
        truth=source_reference(payload,r.identifier,x);out=shell.step(r.identifier,x);g=generic.step(r,x)
        row=result['local_cases'];row['cases']+=1;row['source_enabled']+=truth.status=='PASS'
        row['role_shell_disagreements']+=(out.status,out.inventory)!=(truth.status,truth.inventory)
        row['generic_disagreements']+=(g.status,g.inventory)!=(truth.status,truth.inventory)
    for seed in spec['seeds']:
        supplied={k:seed['metabolite_default'] for k in metabolites}
        supplied.update({k:seed['catalyst_default'] for k in catalysts});supplied.update(seed['overrides'])
        initial=state_from(model,supplied);states,edges=enumerate_graph(payload,model,initial)
        obs={};names=list(spec['observers']);observation_mutations=0
        for count in range(1,len(names)+1):
            for subset in itertools.combinations(names,count):
                keys=[k for n in subset for k in spec['observers'][n]]
                before=digest(states);obs['+'.join(subset)]=audit_observation(payload,model,states,keys)
                observation_mutations+=before!=digest(states)
        disagreements=0
        for a,event,b in edges:
            r=shell.step(event,a);g=generic.step(shell.events[event],a)
            disagreements+=r.status!='PASS' or r.inventory!=b or g.status!='PASS' or g.inventory!=b
        enabled=next(x for x in states if any(source_reference(payload,r.identifier,x).status=='PASS' for r in model.reactions))
        off=list(enabled)
        for k in catalysts:off[model.places.index(k)]=0
        off=tuple(off)
        intervention={'before':enabled,'after':off,'metabolite_readouts_unchanged':all(enabled[model.places.index(k)]==off[model.places.index(k)] for k in metabolites),
                      'full_state_unchanged':enabled==off,'enabled_actions_before':sum(source_reference(payload,r.identifier,enabled).status=='PASS' for r in model.reactions),
                      'enabled_actions_after':sum(source_reference(payload,r.identifier,off).status=='PASS' for r in model.reactions),
                      'interpretation':'Explicit external catalyst-context intervention, not passive observation or cyclic return.'}
        result['graphs'][seed['id']]={'initial':initial,'state_count':len(states),'directed_edges':len(edges),
                                     'states':states,'edges':[{'before':a,'event':e,'after':b} for a,e,b in edges],
                                     'observations':obs,'passive_observation_state_mutations':observation_mutations,
                                     'backend_edge_disagreements':disagreements,'catalyst_off_intervention':intervention}
    r=model.reactions[0];x=state_from(model,{**dict(r.inputs),**{k:1 for k in r.catalysts}})
    proposal=shell.propose(r.identifier,x);good=shell.reconcile(proposal,x)
    changed=list(good.inventory);changed[model.places.index('PYR_c')]+=1
    spent=list(good.inventory);spent[model.places.index(r.catalysts[0])]=0
    tests=[('valid',proposal,good,True),('stale_snapshot',Proposal(r.identifier,'wrong',shell.contract),good,False),
           ('wrong_model_hash',Proposal(r.identifier,proposal.snapshot,'wrong'),good,False),
           ('unknown_event',Proposal('unknown',proposal.snapshot,shell.contract),good,False),
           ('wrong_metabolite_successor',proposal,Result('PASS',tuple(changed),'mutant'),False),
           ('catalyst_consumption',proposal,Result('PASS',tuple(spent),'mutant'),False),
           ('wrong_block_status',proposal,Result('BLOCK',x,'mutant'),False)]
    result['certification_controls']=[{'id':name,'expected_accept':expected,'actual_accept':shell.certify(pr,x,out),
                                       'pass':shell.certify(pr,x,out)==expected} for name,pr,out,expected in tests]
    result['executed_utc']=datetime.now(timezone.utc).isoformat()
    result['scope']=spec['limits']
    target.write_text(json.dumps(result,indent=2)+'\n')
    brief={'linear_structure':result['linear_structure'],'local_cases':result['local_cases'],
           'graphs':{k:{'states':v['state_count'],'edges':v['directed_edges'],'backend_disagreements':v['backend_edge_disagreements'],
                        'observations':{n:{a:b for a,b in o.items() if a!='example_same_observation_different_full_state'} for n,o in v['observations'].items()},
                        'intervention':v['catalyst_off_intervention']} for k,v in result['graphs'].items()},
           'certification_controls':result['certification_controls']}
    (ROOT/'summary.json').write_text(json.dumps(brief,indent=2)+'\n')
    print(json.dumps(brief,indent=2))

if __name__=='__main__':main()
