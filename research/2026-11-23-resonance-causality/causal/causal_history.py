"""Exact action-conditioned behavior and observer-history audit.

Independent raw JSON parser; no previous experiment implementation imported.
All action counts are command counts, never units of physical time.
"""
from collections import defaultdict,deque,Counter
from datetime import datetime,timezone
from pathlib import Path
from itertools import combinations,product
import hashlib,json

HERE=Path(__file__).resolve().parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def parse(payload):
    keys=[r['key'] for r in payload['resources']];pos={k:i for i,k in enumerate(keys)}
    actions=[]
    for r in payload['reactions']:
        take=tuple(r['inputs'].get(k,0) for k in keys)
        give=tuple(r['outputs'].get(k,0) for k in keys)
        read=tuple(int(k in r['active_catalysts']) for k in keys)
        actions.append((r['id'],take,give,read))
    def step(x,a):
        _,take,give,read=actions[a]
        enabled=all(v>=n and v>=c for v,n,c in zip(x,take,read))
        if not enabled:return 'BLOCK',x
        return 'PASS',tuple(v-n+m for v,n,m in zip(x,take,give))
    return keys,pos,actions,step

def reachable(step,initial,action_count,cap):
    found={initial};queue=deque([initial]);edges=set()
    while queue:
        x=queue.popleft()
        for a in range(action_count):
            status,y=step(x,a)
            if status=='PASS':
                edges.add((x,a,y))
                if y not in found:
                    found.add(y);queue.append(y)
                    if len(found)>cap:raise RuntimeError('state cap exceeded')
    return sorted(found),edges

def labels_from_signatures(signatures):
    seen={};out=[]
    for s in signatures:
        if s not in seen:seen[s]=len(seen)
        out.append(seen[s])
    return tuple(out)

def refine(observations,nexts,responses):
    labels=labels_from_signatures(observations);counts=[len(set(labels))]
    while True:
        sig=[(observations[i],tuple((responses[i][a],labels[nxt]) for a,nxt in enumerate(nexts[i]))) for i in range(len(nexts))]
        new=labels_from_signatures(sig)
        if new==labels:break
        assert len(set(new))>len(set(labels))
        labels=new;counts.append(len(set(labels)))
    # The stable relation is a congruence of every command/response transition.
    for i in range(len(labels)):
        for j in range(i):
            if labels[i]==labels[j]:
                assert observations[i]==observations[j]
                for a in range(len(nexts[i])):
                    assert responses[i][a]==responses[j][a]
                    assert labels[nexts[i][a]]==labels[nexts[j][a]]
    return labels,counts

def distinguishing_word(i,j,nexts,responses):
    # Called only when initial observations coincide. No initial-output shortcut.
    queue=deque([(i,j,())]);seen={(min(i,j),max(i,j))}
    while queue:
        x,y,word=queue.popleft()
        for a in range(len(nexts[x])):
            if responses[x][a]!=responses[y][a]:return word+(a,)
            xx,yy=nexts[x][a],nexts[y][a]
            pair=(min(xx,yy),max(xx,yy))
            if xx!=yy and pair not in seen:
                seen.add(pair);queue.append((xx,yy,word+(a,)))
    return None

def belief_machine(observations,nexts,responses,cap):
    fibers=defaultdict(list)
    for i,o in enumerate(observations):fibers[o].append(i)
    roots=[tuple(v) for _,v in sorted(fibers.items())]
    known=set(roots);queue=deque(roots);transition={}
    while queue:
        belief=queue.popleft();rows=[]
        for a in range(len(nexts[0])):
            groups=defaultdict(list)
            for i in belief:groups[responses[i][a]].append((i,nexts[i][a]))
            outcomes=[]
            for output,pairs in sorted(groups.items()):
                following=tuple(sorted({n for _,n in pairs}))
                outcomes.append((output,following,len(pairs)==len(following)))
                if following not in known:
                    known.add(following);queue.append(following)
                    if len(known)>cap:return {'complete':False,'cap':cap,'beliefs_seen':len(known)}
            rows.append(outcomes)
        transition[belief]=rows
    return {'complete':True,'roots':roots,'nodes':sorted(known),'transition':transition}

def winning_strategy(machine,target,forbid_merging=False):
    wins={b:0 for b in machine['nodes'] if target(b)};strategy={}
    while True:
        candidates={}
        for b in machine['nodes']:
            if b in wins:continue
            options=[]
            for a,rows in enumerate(machine['transition'][b]):
                if forbid_merging and not all(injective for _,_,injective in rows):continue
                if all(nxt in wins for _,nxt,_ in rows):options.append((1+max(wins[nxt] for _,nxt,_ in rows),a))
            if options:candidates[b]=min(options)
        if not candidates:break
        for b,(depth,a) in candidates.items():wins[b]=depth;strategy[b]=a
    return wins,strategy

def shortest_homing_witness(root,machine,nexts,responses,actions):
    queue=deque([(root,())]);seen={root}
    while queue:
        b,path=queue.popleft()
        if len(b)==1 and path:
            lineage={i:i for i in root};trace=[]
            for a,out in path:
                lineage={origin:nexts[current][a] for origin,current in lineage.items() if responses[current][a]==out}
                trace.append({'action':actions[a][0],'response':out,'remaining_initial_hypotheses':len(lineage),'possible_current_state_ids':sorted(set(lineage.values()))})
            return {'initial_belief':root,'steps':trace,'remaining_initial_state_ids':sorted(lineage),'current_state_ids':sorted(set(lineage.values())),'initial_state_identified':len(lineage)==1,'homing_includes_state_merging':len(lineage)>1}
        for a,rows in enumerate(machine['transition'][b]):
            for output,nxt,_ in rows:
                if nxt not in seen:seen.add(nxt);queue.append((nxt,path+((a,output),)))
    return None

def analyze(states,step,actions,indices,with_status,cap):
    sid={x:i for i,x in enumerate(states)}
    observations=[tuple(x[i] for i in indices) for x in states]
    nexts=[];responses=[]
    for x in states:
        nrow=[];orow=[]
        for a in range(len(actions)):
            status,y=step(x,a);nrow.append(sid[y]);obs=tuple(y[i] for i in indices)
            orow.append((status,obs) if with_status else (obs,))
        nexts.append(nrow);responses.append(orow)
    labels,counts=refine(observations,nexts,responses)
    histogram=Counter();equivalent=0;first_word=None;first_equiv=None;initial_pairs=0
    for i,j in combinations(range(len(states)),2):
        if observations[i]!=observations[j]:continue
        initial_pairs+=1;word=distinguishing_word(i,j,nexts,responses)
        assert (word is None)==(labels[i]==labels[j])
        if word is None:
            equivalent+=1
            if first_equiv is None:first_equiv={'first_id':i,'second_id':j,'observation':observations[i],'first_state':states[i],'second_state':states[j]}
        else:
            histogram[len(word)]+=1
            if first_word is None:
                xx,yy=i,j;tr=[]
                for a in word:
                    tr.append({'action':actions[a][0],'first_response':responses[xx][a],'second_response':responses[yy][a]});xx,yy=nexts[xx][a],nexts[yy][a]
                first_word={'first_id':i,'second_id':j,'first_state':states[i],'second_state':states[j],'initial_observation':observations[i],'action_word':[actions[a][0] for a in word],'response_trace':tr}
    machine=belief_machine(observations,nexts,responses,cap)
    memory={'complete':machine['complete']}
    if machine['complete']:
        for name,target,no_merge in [('current_state',lambda b:len(b)==1,False),('predictive_class',lambda b:len({labels[i] for i in b})==1,False),('initial_state',lambda b:len(b)==1,True)]:
            wins,strategy=winning_strategy(machine,target,no_merge)
            memory[name]={'winning_beliefs':len(wins),'roots_guaranteed':sum(b in wins for b in machine['roots']),'root_depths':[wins.get(b) for b in machine['roots']],'max_guaranteed_root_steps':max((wins[b] for b in machine['roots'] if b in wins),default=None)}
        memory['belief_nodes']=len(machine['nodes']);memory['initial_fibers']=len(machine['roots'])
        memory['ambiguous_roots']=sum(len(b)>1 for b in machine['roots'])
        memory['first_homing_witness']=next((w for b in machine['roots'] if len(b)>1 for w in [shortest_homing_witness(b,machine,nexts,responses,actions)] if w is not None),None)
        memory['minimum_possible_homing_by_root']=[0 if len(b)==1 else (len(w['steps']) if (w:=shortest_homing_witness(b,machine,nexts,responses,actions)) else None) for b in machine['roots']]
    else:memory.update({k:v for k,v in machine.items() if k!='complete'})
    return {'states':len(states),'current_observation_classes':counts[0],'future_behavior_classes':counts[-1],'refinement_class_counts':counts,'initial_ambiguous_unordered_pairs':initial_pairs,'future_equivalent_unordered_pairs':equivalent,'shortest_distinguishing_word_histogram':dict(sorted(histogram.items())),'first_distinguishing_witness':first_word,'first_future_equivalent_witness':first_equiv,'history':memory}

def main():
    if (HERE/'results.json').exists():raise RuntimeError('Preserve original outputs; run in a fresh copied directory')
    frozen=json.loads((HERE/'FROZEN_DESIGN.json').read_text())
    assert all(sha(HERE/p)==digest for p,digest in frozen['files'].items())
    spec=json.loads((HERE/'EXPERIMENT_SPEC.json').read_text())
    payload=json.loads((HERE/'model/token_contract.json').read_text())
    prior=json.loads((HERE/'model/prior_seed_spec.json').read_text())
    keys,pos,actions,step=parse(payload)
    met=[i for i,r in enumerate(payload['resources']) if r['role']=='metabolite_count']
    cat=[i for i,r in enumerate(payload['resources']) if r['role']=='asserted_active_catalytic_role']
    obs_keys=['GA3P_c','PYR_c','LACT_e']
    result={'schema':'action_history_closure_results.v1','frozen_design_sha256':sha(HERE/'FROZEN_DESIGN.json'),'resource_order':keys,'action_order':[a[0] for a in actions],'graphs':{},'scope':spec['limits']}
    for seed in prior['seeds']:
        x=tuple(seed['overrides'].get(k,seed['metabolite_default'] if i in met else seed['catalyst_default']) for i,k in enumerate(keys))
        states,edges=reachable(step,x,len(actions),spec['state_cap'])
        g={'states':states,'state_count':len(states),'enabled_edges':len(edges),'fixed_context':{},'context_extension':{}}
        for size in range(4):
            for subset in combinations(obs_keys,size):
                name='+'.join(subset) or 'empty'
                for status in (False,True):
                    ch='readout_and_status' if status else 'readout_only'
                    g['fixed_context'][name+'|'+ch]=analyze(states,step,actions,[pos[k] for k in subset],status,spec['belief_cap'])
        hidden=[]
        for x in states:
            for mask in product((0,1),repeat=len(cat)):
                y=list(x)
                for i,v in zip(cat,mask):y[i]=v
                hidden.append(tuple(y))
        hidden=sorted(set(hidden));g['context_extension']['state_count']=len(hidden)
        for mask_known in (False,True):
            inds=[pos[k] for k in obs_keys]+(cat if mask_known else [])
            for status in (False,True):
                name=('mask_known' if mask_known else 'mask_hidden')+'|'+('readout_and_status' if status else 'readout_only')
                g['context_extension'][name]=analyze(hidden,step,actions,inds,status,spec['belief_cap'])
        # Deterministic first enabled state/action for an unreported external change.
        before,a=next((s,a) for s in states for a in range(len(actions)) if step(s,a)[0]=='PASS')
        off=list(before)
        for i in cat:off[i]=0
        off=tuple(off);pred=step(before,a);actual=step(off,a)
        g['unreported_context_change']={'before':before,'after_external_change':off,'same_all_metabolite_readouts':all(before[i]==off[i] for i in met),'command':actions[a][0],'old_context_prediction':{'status':pred[0],'state':pred[1]},'actual_changed_context':{'status':actual[0],'state':actual[1]},'assumption_failure':'Catalyst masks changed outside the six-command transition law; a belief based on the old fixed context is no longer guaranteed.'}
        result['graphs'][seed['id']]=g
    result['executed_utc']=datetime.now(timezone.utc).isoformat()
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    summary={}
    for name,g in result['graphs'].items():
        summary[name]={'states':g['state_count'],'edges':g['enabled_edges'],'fixed_context':{},'context_extension':{}}
        for section in ['fixed_context','context_extension']:
            for label,r in g[section].items():
                if not isinstance(r,dict):continue
                summary[name][section][label]={'current_classes':r['current_observation_classes'],'future_classes':r['future_behavior_classes'],'refinement':r['refinement_class_counts'],'distinguishing_lengths':r['shortest_distinguishing_word_histogram'],'equivalent_pairs':r['future_equivalent_unordered_pairs'],'belief_nodes':r['history'].get('belief_nodes'),'roots':r['history'].get('initial_fibers'),'current_state_homing':r['history'].get('current_state'),'initial_state_identification':r['history'].get('initial_state'),'predictive_homing':r['history'].get('predictive_class')}
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
