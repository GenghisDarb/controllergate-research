"""Independent review: imports no functions from run_operator_audit.py.

Only the pinned source functions are executed as the system under test. Reference
calculations use direct neighbor weights, an edge-list energy/gradient, scalar
modal recurrences and the saved, frozen specification. This is computational
review of a specified synthetic model, not independent physical replication.
"""
from pathlib import Path
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
import statistics

import numpy as np

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / 'independent_operator_review_receipt.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source_only():
    source = (HERE/'source_snapshot/kernels.py').read_bytes()
    tree = ast.parse(source.decode())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in ('cyclic_coherence', '_clamp')]
    ladder = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                  and n.name == 'LadderKernel')
    update = next(n for n in ladder.body if isinstance(n, ast.FunctionDef)
                  and n.name == '_relax')
    update.decorator_list = []
    nodes.append(update)
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    namespace = {'statistics': statistics}
    exec(compile(module, 'independent_pinned_source_only', 'exec'), namespace)
    return namespace['_relax'], namespace['cyclic_coherence'], source


def direct_step(x, p, a):
    """Coefficient expansion; does not call the root reference matrix helper."""
    off = 0.105*(1-a)
    diag = 0.79 - 0.21*a
    return diag*x + off*(np.roll(x, 1)+np.roll(x, -1)) + 0.42*a*p


def edge_energy_gradient(x, p, a, residual_edges=False):
    e = x-p
    q = e if residual_edges else x
    energy = a*float(e@e)/2
    gradient = a*e.copy()
    for i in range(len(x)):
        j = (i+1) % len(x)
        difference = q[i]-q[j]
        energy += (1-a)*difference*difference/8
        increment = (1-a)*difference/4
        gradient[i] += increment
        gradient[j] -= increment
    return energy, gradient


def direct_matrix(n, a, cut_edges=()):
    edges = [(i, (i+1) % n) for i in range(n)]
    blocked = {frozenset(edge) for edge in cut_edges}
    laplacian = np.zeros((n, n))
    for i, j in edges:
        if frozenset((i,j)) in blocked:
            continue
        laplacian[i,i] += 1
        laplacian[j,j] += 1
        laplacian[i,j] -= 1
        laplacian[j,i] -= 1
    return np.eye(n)*(1-.42*a) - .105*(1-a)*laplacian


def main():
    if RECEIPT.exists():
        raise RuntimeError('Preserve review receipt; replay in a copied directory.')
    spec = json.loads((HERE/'experiment_spec.json').read_text())
    result = json.loads((HERE/'results.json').read_text())
    summary = json.loads((HERE/'summary.json').read_text())
    freeze = json.loads((HERE/'FROZEN_DESIGN.json').read_text())
    provenance = json.loads((HERE/'source_snapshot/SOURCE_PROVENANCE.json').read_text())
    for name, expected in freeze['files'].items():
        assert digest(HERE/name) == expected, name
    assert result['frozen_design_sha256'] == digest(HERE/'FROZEN_DESIGN.json')
    sut, coherence, source_bytes = load_source_only()
    assert hashlib.sha256(source_bytes).hexdigest() == provenance['sha256']
    blob_header = f'blob {len(source_bytes)}\0'.encode()
    assert hashlib.sha1(blob_header+source_bytes).hexdigest() == provenance['git_blob_sha']
    assert provenance['matched'] is True

    rng = np.random.default_rng(spec['seed'])
    maxima = dict(source_direct=0., matrix=0., gradient=0., candidate_gradient=0.,
                  energy_trajectory=0., final_rms=0., impulse_history=0.,
                  forced_analytic=0., finite_difference_gradient=0., stationary=0.)
    checked = 0
    forced_rows = 0
    for saved in result['cases']:
        n, a = saved['N'], saved['a']
        p = np.array([math.sin(2*math.pi*i/n)+.3*math.cos(6*math.pi*i/n)
                      for i in range(n)])
        # The supplied pattern is reconstructed from the frozen formula.
        A = direct_matrix(n,a)
        zero = np.zeros(n)
        source_A = np.column_stack([sut(np.eye(n)[i].tolist(), zero.tolist(), a)
                                    for i in range(n)])
        maxima['matrix'] = max(maxima['matrix'], float(np.max(abs(A-source_A))))
        eig = np.linalg.eigvalsh(A)
        assert np.allclose(eig,saved['eigenvalues'],atol=1e-14,rtol=0)
        assert eig.min() >= .58-1e-14 and eig.max() <= 1-0.42*a+1e-14
        for k in range(spec['random_states_per_case']):
            x = rng.normal(size=n)
            y = np.asarray(sut(x.tolist(),p.tolist(),a))
            E, gradient = edge_energy_gradient(x,p,a)
            maxima['source_direct'] = max(maxima['source_direct'],float(np.max(abs(y-direct_step(x,p,a)))))
            maxima['gradient'] = max(maxima['gradient'],float(np.max(abs(y-(x-.42*gradient)))))
            E_after,_ = edge_energy_gradient(y,p,a)
            assert E_after-E <= -.3318*float(gradient@gradient)+2e-13
            candidate = p+np.asarray(sut((x-p).tolist(),zero.tolist(),a))
            Ec,gc = edge_energy_gradient(x,p,a,True)
            maxima['candidate_gradient'] = max(maxima['candidate_gradient'],float(np.max(abs(candidate-(x-.42*gc)))))
            if k == 0:
                # Finite difference independently checks the edge-list derivative.
                h = 1e-5
                for j in [0,n//2,n-1]:
                    dx=np.zeros(n);dx[j]=h
                    plus=edge_energy_gradient(x+dx,p,a)[0]
                    minus=edge_energy_gradient(x-dx,p,a)[0]
                    maxima['finite_difference_gradient']=max(maxima['finite_difference_gradient'],abs((plus-minus)/(2*h)-gradient[j]))

        initial = p+.4*rng.normal(size=n)
        original = initial.copy()
        candidate = initial.copy()
        for t in range(spec['trajectory_steps']+1):
            E,_ = edge_energy_gradient(original,p,a)
            Ec,_ = edge_energy_gradient(candidate,p,a,True)
            maxima['energy_trajectory'] = max(maxima['energy_trajectory'],abs(E-saved['original_energy'][t]),abs(Ec-saved['candidate_energy'][t]))
            if t < spec['trajectory_steps']:
                original=direct_step(original,p,a)
                candidate=p+direct_step(candidate-p,zero,a)
        for observed,key in [(original,'original_final_parent_rms'),(candidate,'candidate_final_parent_rms')]:
            err=abs(float(np.linalg.norm(observed-p)/math.sqrt(n))-saved[key])
            maxima['final_rms']=max(maxima['final_rms'],err)
        assert np.allclose(p+direct_step(zero,zero,a),p,atol=1e-15,rtol=0)
        if a>0:
            star=np.linalg.solve(np.eye(n)-A,.42*a*p)
            stat=saved['stationary']
            maxima['stationary']=max(maxima['stationary'],abs(float(np.linalg.norm(star-p)/math.sqrt(n))-stat['original_fixedpoint_parent_rms']))
        else:
            # The candidate fixes a whole family p+c1, so unanchored parent
            # convergence is not claimed for an arbitrary initial residual.
            assert np.allclose(p+direct_step(np.ones(n),zero,a),p+1,atol=1e-15,rtol=0)
            assert saved['stationary'] is None

        state = np.eye(n)[0]
        history = [state.copy()]
        for _ in range(spec['impulse_steps']):
            state = direct_step(state,zero,a)
            history.append(state.copy())
        history=np.asarray(history)
        maxima['impulse_history']=max(maxima['impulse_history'],float(np.max(abs(history-np.asarray(saved['impulse_history'])))))
        for j in range(n):
            distance=min(j,n-j)
            nonzero=np.where(history[:,j]>0)[0]
            first=int(nonzero[0]) if nonzero.size else None
            assert first==saved['first_nonzero_impulse'][j]
            assert first==(distance if a<1 or j==0 else None)
            assert np.all(history[:distance,j]==0)
        for vis in saved['visibility']:
            mask=history>=vis['floor']
            assert int(mask.any(axis=0).sum())==vis['detected_nodes']
            actual=[int(ids[0]) if (ids:=np.flatnonzero(mask[:,j])).size else None for j in range(n)]
            assert actual==vis['first_detected_step']
        if saved['cut_control']:
            cut=direct_matrix(n,a,[(0,1),(n-1,0)])
            state=np.eye(n)[0]
            for _ in range(spec['impulse_steps']):
                state=cut@state
                assert np.all(state[1:]==0)

        lam=.58+.42*(1-a)*math.cos(math.pi*spec['force_mode']/n)**2
        old_gain=float('inf')
        for point in saved['forced_response']:
            w=point['omega_radians_per_iteration']
            # Independent real-valued magnitude formula.
            expected=.42*a/math.sqrt((1-lam)**2+2*lam*(1-math.cos(w)))
            err=max(abs(expected-point['analytic_gain']),abs(expected-point['measured_gain']))
            maxima['forced_analytic']=max(maxima['forced_analytic'],err)
            assert point['measured_gain'] <= old_gain+1e-13
            old_gain=point['measured_gain']
            forced_rows+=1
        checked+=1

    # Independently replay three representative forced runs, using a scalar
    # modal recurrence rather than the source vector or the root fit routine.
    representative=next(c for c in result['cases'] if c['N']==14 and c['a']==.5)
    n,a=14,.5
    lam=.58+.42*(1-a)*math.cos(math.pi/n)**2
    scalar_replays=[]
    for w in [0.,math.pi/4,math.pi]:
        samples=[];state=0.
        for t in range(spec['forced_iteration_steps']):
            samples.append(state)
            state=lam*state+.42*a*math.cos(w*t)
        tail=np.asarray(samples[-spec['forced_fit_tail']:])
        times=np.arange(len(samples)-len(tail),len(samples))
        if w==0:
            gain=abs(float(np.mean(tail)))
        elif w==math.pi:
            gain=abs(float(np.mean(tail*np.cos(w*times))))
        else:
            # Integral-period orthogonal demodulation.
            gain=2*abs(complex(np.mean(tail*np.exp(-1j*w*times))))
        saved=next(f for f in representative['forced_response'] if abs(f['omega_radians_per_iteration']-w)<1e-13)
        error=abs(gain-saved['measured_gain'])
        assert error<1e-12
        scalar_replays.append({'omega':w,'independent_scalar_gain':gain,'root_vector_gain':saved['measured_gain'],'absolute_difference':error})

    metric_errors=[]
    metric_rng=np.random.default_rng(981731)
    for row in result['ordering']:
        n=row['N']
        # Irregular monotone samples check more than the original linear ramp.
        values=np.cumsum(metric_rng.uniform(.02,3,size=n))+14.7
        exact=1-1.6/n
        error=abs(coherence(values.tolist())-exact)
        assert error<1e-14 and abs(row['monotone_score']-exact)<1e-14
        metric_errors.append(error)

    assert checked==20 and forced_rows==120 and summary['cases']==20
    assert maxima['finite_difference_gradient']<1e-8
    assert max(v for k,v in maxima.items() if k!='finite_difference_gradient')<1e-11
    focus=summary['N14_a05']
    assert focus['visibility']==representative['visibility']
    assert [v['detected_nodes'] for v in focus['visibility']]==[3,9,14]
    assert focus['visibility'][2]['first_detected_step'][7]==17
    assert abs(focus['original_final_parent_rms']-.06811019837998819)<1e-14
    assert focus['candidate_final_parent_rms']<1e-14

    receipt={
        'status':'PASS_WITH_DECLARED_SCOPE',
        'reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'reviewer':'independent resonance-history agent',
        'independence':'No root audit functions imported. Only pinned source SUT executed; references use edge-list gradients, coefficient-expanded updates, independent seeded trajectory reconstruction and scalar forcing.',
        'files':{name:digest(HERE/name) for name in ['experiment_spec.json','FROZEN_DESIGN.json','run_operator_audit.py','results.json','summary.json','source_snapshot/kernels.py','source_snapshot/SOURCE_PROVENANCE.json','independent_operator_review.py']},
        'source_provenance':{
            'sha256_matches':True,'git_blob_object_hash_matches':True,
            'commit':provenance['commit'],
            'fresh_remote_read':'Coordinating audit receipt checked; not independently repeated in this review.'},
        'checked_cases':checked,'gradient_states':checked*spec['random_states_per_case'],
        'full_energy_trajectories_reconstructed':checked*2,
        'impulse_trajectories_reconstructed':checked,
        'analytic_and_saved_measured_gain_rows_checked':forced_rows,
        'independent_scalar_forcing_replays':scalar_replays,
        'maximum_absolute_errors':maxima,
        'irregular_monotone_metric_max_error':max(metric_errors),
        'energy_descent_bound':'E(next)-E(now)<=-(.42-.42^2/2)||gradient||^2=-.3318||gradient||^2 because Hessian eigenvalues are in[0,1].',
        'candidate_goal':'Recover the supplied nonuniform parent while retaining the original perturbation Jacobian; candidate is p+A(x-p).',
        'candidate_caveat':'For a=0, constant residual is conserved and every p+c1 is fixed. Arbitrary parent recovery requires a>0; the parent is supplied, not predicted.',
        'a05_N14_visibility':{'nodes_above_declared_floors':[3,9,14],'floors':[.01,.0001,.000001],'opposite_node_first_nonzero_step':7,'opposite_node_first_above_1e_minus6_step':17},
        'interpretive_limits':['All20 cases are supplied synthetic models, not independent physical systems.','All120 saved forcing gains checked analytically; only three forced recurrences independently replayed.','The frequency response is low-pass in iteration units; no measured physical clock or nonzero-frequency resonance is established.','The causal cone is intervention sensitivity in this declared local model; no inference of real-world causal law.','No14-versus15 selection is supplied by these formulas.','The synchronization splay pattern is constructed; no spontaneous lock or historical global-resultant code bug is claimed.'],
    }
    RECEIPT.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'cases':checked,'forced_rows':forced_rows,'maxima':maxima,'receipt':RECEIPT.name},indent=2))


if __name__=='__main__':
    main()
