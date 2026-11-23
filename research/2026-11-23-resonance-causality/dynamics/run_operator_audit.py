"""Pinned-source energy, propagation and recovery experiment.

The parent pattern, iteration clock and probes are supplied model choices.
Original source remains unchanged; the new candidate acts on its residuals.
"""
from pathlib import Path
import ast,hashlib,json,math,statistics
from datetime import datetime,timezone
import numpy as np

HERE=Path(__file__).resolve().parent

def source_functions():
    tree=ast.parse((HERE/'source_snapshot/kernels.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LadderKernel')
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_relax')
    fn.decorator_list=[]
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_clamp','cyclic_coherence'}]
    module=ast.Module(body=selected+[fn],type_ignores=[]);ast.fix_missing_locations(module)
    scope={'statistics':statistics};exec(compile(module,'pinned_source_extract','exec'),scope)
    return scope['_relax'],scope['cyclic_coherence']

def energy(x,p,a,residual_coupling=False):
    e=x-p;q=e if residual_coupling else x
    return float(a*np.dot(e,e)/2+(1-a)*np.sum((q-np.roll(q,-1))**2)/8)

def operators(n,a):
    L=2*np.eye(n)-np.roll(np.eye(n),1,axis=1)-np.roll(np.eye(n),-1,axis=1)
    Q=a*np.eye(n)+(1-a)*L/4
    return L,Q,np.eye(n)-0.42*Q

def main():
    target=HERE/'results.json'
    if target.exists():raise RuntimeError('Preserve results; replay in a fresh copied directory')
    freeze=json.loads((HERE/'FROZEN_DESIGN.json').read_text())
    for path,expected in freeze['files'].items():
        assert hashlib.sha256((HERE/path).read_bytes()).hexdigest()==expected,path
    spec=json.loads((HERE/'experiment_spec.json').read_text())
    relax,coherence=source_functions();rng=np.random.default_rng(spec['seed'])
    records=[]
    for n in spec['sizes']:
        parent=np.sin(2*np.pi*np.arange(n)/n)+0.3*np.cos(6*np.pi*np.arange(n)/n)
        for a in spec['anchorings']:
            L,Q,A=operators(n,a);zeros=np.zeros(n)
            source_matrix=np.column_stack([relax(np.eye(n)[i].tolist(),zeros.tolist(),a) for i in range(n)])
            max_source_error=float(np.max(np.abs(source_matrix-A)))
            max_gradient_error=0.;max_bound_excess=-float('inf');max_candidate_gradient_error=0.
            for _ in range(spec['random_states_per_case']):
                x=rng.normal(size=n);g=Q@x-a*parent
                y=np.asarray(relax(x.tolist(),parent.tolist(),a))
                max_gradient_error=max(max_gradient_error,float(np.max(np.abs(y-(x-.42*g)))))
                change=energy(y,parent,a)-energy(x,parent,a)
                max_bound_excess=max(max_bound_excess,change+.3318*float(g@g))
                z=parent+np.asarray(relax((x-parent).tolist(),zeros.tolist(),a))
                max_candidate_gradient_error=max(max_candidate_gradient_error,float(np.max(np.abs(z-(x-.42*(Q@(x-parent)))))))
            initial=parent+.4*rng.normal(size=n)
            original=initial.copy();candidate=initial.copy();original_E=[];candidate_E=[]
            for t in range(spec['trajectory_steps']+1):
                original_E.append(energy(original,parent,a))
                candidate_E.append(energy(candidate,parent,a,True))
                if t<spec['trajectory_steps']:
                    original=np.asarray(relax(original.tolist(),parent.tolist(),a))
                    candidate=parent+np.asarray(relax((candidate-parent).tolist(),zeros.tolist(),a))
            eig=np.linalg.eigvalsh(A)
            station=None
            if a>0:
                star=np.linalg.solve(Q,a*parent)
                station={'original_fixedpoint_parent_rms':float(np.sqrt(np.mean((star-parent)**2))),
                         'original_equilibrium_energy':energy(star,parent,a),
                         'original_stationarity_error':float(np.max(np.abs(Q@star-a*parent))),
                         'candidate_parent_one_step_error':float(np.max(np.abs(parent+np.asarray(relax(zeros.tolist(),zeros.tolist(),a))-parent))),
                         'original_parent_one_step_error':float(np.max(np.abs(np.asarray(relax(parent.tolist(),parent.tolist(),a))-parent)))}
            impulse=np.zeros(n);impulse[0]=1;history=[impulse.copy()]
            for _ in range(spec['impulse_steps']):
                impulse=np.asarray(relax(impulse.tolist(),zeros.tolist(),a));history.append(impulse.copy())
            impulse_arr=np.asarray(history);outside=0.;first=[]
            for j in range(n):
                distance=min(j,n-j)
                ids=np.flatnonzero(impulse_arr[:,j]>0)
                onset=int(ids[0]) if len(ids) else None
                expected=distance if a<1 or j==0 else None
                assert onset==expected,(n,a,j,onset,expected)
                first.append(onset)
                if distance>0:outside=max(outside,float(np.max(np.abs(impulse_arr[:distance,j]))))
            visibility=[{'floor':floor,'detected_nodes':int(np.any(impulse_arr>=floor,axis=0).sum()),
                         'first_detected_step':[int(v[0]) if len(v:=np.flatnonzero(impulse_arr[:,j]>=floor)) else None for j in range(n)]}
                        for floor in spec['absolute_visibility_floors']]
            forced=[]
            if a>0:
                mode=np.cos(2*np.pi*np.arange(n)*spec['force_mode']/n);mode/=np.linalg.norm(mode)
                lam=1-.42*(a+(1-a)*np.sin(np.pi*spec['force_mode']/n)**2)
                for w in spec['forcing_frequencies']:
                    x=zeros.copy();ys=[]
                    for t in range(spec['forced_iteration_steps']):
                        ys.append(float(x@mode))
                        p=mode*np.cos(w*t)
                        x=np.asarray(relax(x.tolist(),p.tolist(),a))
                    ids=np.arange(spec['forced_iteration_steps']-spec['forced_fit_tail'],spec['forced_iteration_steps'])
                    tail=np.asarray(ys[-spec['forced_fit_tail']:])
                    if w==0:measured=abs(float(tail.mean()))
                    elif abs(w-np.pi)<1e-12:measured=abs(float(tail@np.cos(w*ids)/(np.cos(w*ids)@np.cos(w*ids))))
                    else:
                        design=np.column_stack([np.cos(w*ids),np.sin(w*ids)])
                        measured=float(np.linalg.norm(np.linalg.lstsq(design,tail,rcond=None)[0]))
                    expected=.42*a/abs(np.exp(1j*w)-lam)
                    forced.append({'omega_radians_per_iteration':w,'measured_gain':measured,'analytic_gain':float(expected),'absolute_error':abs(measured-expected)})
            cut=None
            if n==14 and a==.5:
                # Remove edges0-1 and13-0, updating BOTH diagonals as well.
                Lcut=L.copy()
                for u,v in [(0,1),(0,n-1)]:
                    Lcut[u,u]-=1;Lcut[v,v]-=1;Lcut[u,v]+=1;Lcut[v,u]+=1
                Acut=np.eye(n)-.42*(a*np.eye(n)+(1-a)*Lcut/4)
                state=np.eye(n)[0];max_remote=0.
                for t in range(spec['impulse_steps']):
                    state=Acut@state;max_remote=max(max_remote,float(np.max(np.abs(state[1:]))))
                cut={'edges_removed':[[0,1],[0,n-1]],'diagonal_corrected':True,'max_remote_impulse_after_isolating_source':max_remote}
            records.append({'N':n,'a':a,'source_matrix_error':max_source_error,'gradient_identity_error':max_gradient_error,
              'energy_descent_bound_max_excess':max_bound_excess,'candidate_gradient_identity_error':max_candidate_gradient_error,
              'eigenvalues':eig.tolist(),'original_energy':original_E,'candidate_energy':candidate_E,
              'original_max_energy_increase':float(np.max(np.diff(original_E))),
              'candidate_max_energy_increase':float(np.max(np.diff(candidate_E))),
              'original_final_parent_rms':float(np.sqrt(np.mean((original-parent)**2))),
              'candidate_final_parent_rms':float(np.sqrt(np.mean((candidate-parent)**2))),
              'stationary':station,'impulse_history':impulse_arr.tolist(),'first_nonzero_impulse':first,
              'max_influence_before_graph_distance':outside,'visibility':visibility,'forced_response':forced,'cut_control':cut})
    ordering=[];splay=[]
    for n in spec['sizes']:
        score=coherence(list(map(float,range(n))))
        ordering.append({'N':n,'monotone_score':score,'analytic_score':1-1.6/n,'legacy_closed_threshold_met':score>=.7,
                         'meaning':'Scalar cyclic ordering diagnostic; no trajectory is supplied'})
        times=np.arange(32)*.1;phases=.7*times[:,None]+2*np.pi*np.arange(n)[None,:]/n
        units=np.exp(1j*phases);rel=units/units[:,[0]]
        splay.append({'N':n,'max_first_harmonic_order':float(np.max(np.abs(units.mean(axis=1)))),
                      'max_relative_phase_change':float(np.max(np.abs(rel-rel[[0],:]))),
                      'min_Nth_harmonic_order':float(np.min(np.abs(np.exp(1j*n*phases).mean(axis=1)))),
                      'scope':'Constructed phase-locked pattern; no spontaneous emergence, historical bug or favored count claim'})
    maxerr=max(r['gradient_identity_error'] for r in records)
    assert maxerr<1e-12 and max(r['candidate_gradient_identity_error'] for r in records)<1e-12
    assert all(r['original_max_energy_increase']<1e-11 and r['candidate_max_energy_increase']<1e-11 for r in records)
    assert max(r['energy_descent_bound_max_excess'] for r in records)<1e-11
    assert all(r['max_influence_before_graph_distance']==0 for r in records)
    assert max(v['absolute_error'] for r in records for v in r['forced_response'])<1e-10
    result={'schema':'source_operator_resonance_results.v1','executed_utc':datetime.now(timezone.utc).isoformat(),
            'frozen_design_sha256':hashlib.sha256((HERE/'FROZEN_DESIGN.json').read_bytes()).hexdigest(),
            'cases':records,'ordering':ordering,'splay_control':splay,'limits':spec['limits']}
    target.write_text(json.dumps(result,indent=2)+'\n')
    brief={'cases':len(records),'random_source_gradient_checks':len(records)*spec['random_states_per_case'],
           'max_source_matrix_error':max(r['source_matrix_error'] for r in records),
           'max_gradient_error':maxerr,'max_candidate_gradient_error':max(r['candidate_gradient_identity_error'] for r in records),
           'max_energy_bound_excess':max(r['energy_descent_bound_max_excess'] for r in records),
           'max_forced_gain_error':max(v['absolute_error'] for r in records for v in r['forced_response']),
           'all_causal_cones_match':all(r['max_influence_before_graph_distance']==0 for r in records),
           'N14_a05':{k:v for k,v in next(r for r in records if r['N']==14 and r['a']==.5).items() if k not in {'original_energy','candidate_energy','impulse_history','eigenvalues'}},
           'ordering':ordering,'splay_control':splay}
    (HERE/'summary.json').write_text(json.dumps(brief,indent=2)+'\n');print(json.dumps(brief,indent=2))

if __name__=='__main__':main()
