"""Frozen exploratory marginal-displacement analysis of real CTCF examples."""
import argparse
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
import math
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from scipy.optimize import minimize
from scipy.special import expit, logsumexp

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent
INPUTS = ['ctcf_rep1_cell01.mat', 'ctcf_rep3_cell01.mat', 'SpotOn_main.m', 'spoton_matlab_README.md']
EXPECTED_GIT = {'ctcf_rep1_cell01.mat': '6486d6b15c68faf47395f54427d25f1680fc7acd',
                'ctcf_rep3_cell01.mat': '49627183cf193d00c6a663750c2de408f58a4919'}
LAGS = [1, 2, 3, 4]
EXPOSURE = 0.001


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def freeze():
    if (ROOT / 'FROZEN_ANALYSIS.json').exists() or (ROOT / 'results.json').exists():
        raise RuntimeError('Refusing to overwrite frozen analysis or results')
    save('FROZEN_ANALYSIS.json', {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Local seal before fitting; exploratory secondary-data analysis, not external preregistration.',
        'sources': {n: sha(ROOT / n) for n in ['analysis_spec.json', 'analyze_ctcf.py']},
        'inputs': {n: sha(DATA / n) for n in INPUTS}, 'fit_has_not_run': True})
    print(json.dumps({'frozen_analysis_sha256': sha(ROOT / 'FROZEN_ANALYSIS.json'), 'fitted': False}))


def verify_seal():
    s = json.loads((ROOT / 'FROZEN_ANALYSIS.json').read_text())
    for n, h in s['sources'].items():
        assert sha(ROOT / n) == h, 'Frozen analysis source changed: ' + n
    for n, h in s['inputs'].items():
        assert sha(DATA / n) == h, 'Input changed: ' + n
    return s


def partition(index):
    return 'train' if int(hashlib.sha256(('ctcf-split-v1:' + str(index)).encode()).hexdigest()[:8], 16) % 10 < 7 else 'heldout'


def ingest(name):
    raw = (DATA / name).read_bytes()
    git = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    assert git == EXPECTED_GIT[name]
    m = loadmat(DATA / name, squeeze_me=True, struct_as_record=False)
    settings, tracks = m['settings'], np.atleast_1d(m['trackedPar'])
    dt = float(settings.Delay)
    assert dt > EXPOSURE
    rows, lengths, gap_counts = [], [], []
    max_timing_error = 0.0
    all_xy = []
    for index, tr in enumerate(tracks):
        frame = np.atleast_1d(tr.Frame).astype(float)
        times = np.atleast_1d(tr.TimeStamp).astype(float)
        xy = np.asarray(tr.xy, dtype=float).reshape(-1, 2)
        assert len(frame) == len(times) == len(xy)
        assert np.isfinite(xy).all() and np.isfinite(times).all() and np.isfinite(frame).all()
        assert np.equal(frame, np.rint(frame)).all()
        assert np.all(np.diff(frame) > 0) and np.all(np.diff(times) > 0)
        lengths.append(len(frame))
        all_xy.append(xy)
        gap_counts.extend(np.diff(frame).astype(int).tolist())
        error = float(np.max(np.abs(times - frame * dt)))
        max_timing_error = max(max_timing_error, error)
        assert error < 1e-8
        frame_to_index = {int(f): i for i, f in enumerate(frame)}
        for lag in LAGS:
            for start, f in enumerate(frame):
                end = frame_to_index.get(int(f) + lag)
                if end is not None:
                    displacement = xy[end] - xy[start]
                    rows.append((index, lag, displacement[0], displacement[1], times[end] - times[start]))
                    break
    a = np.asarray(rows, dtype=float)
    xy = np.vstack(all_xy)
    lengths_array = np.asarray(lengths)
    info = {'file': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'git_blob_sha1': git,
            'bytes': len(raw), 'tracks': len(tracks), 'localizations': int(sum(lengths)),
            'singletons': int(sum(lengths_array == 1)), 'settings_delay_seconds': dt,
            'author_example_delay_seconds': 0.007477,
            'relative_timing_difference': dt / 0.007477 - 1,
            'settings_pixel_size_um': float(settings.px2micron), 'acquisition_frames': int(settings.Frames),
            'filename_basename': str(settings.Filename).replace('\\', '/').split('/')[-1],
            'coordinate_range_um': [xy.min(axis=0).tolist(), xy.max(axis=0).tolist()],
            'max_timestamp_consistency_error_seconds': max_timing_error,
            'track_length_quantiles': dict(zip(['min', 'q25', 'median', 'q75', 'max'], np.quantile(lengths_array, [0, .25, .5, .75, 1]).tolist())),
            'max_frame_gap': int(max(gap_counts)) if gap_counts else 0,
            'eligible_trajectories_by_lag': {str(l): int(np.sum(a[:, 1] == l)) for l in LAGS},
            'data_quality_status': 'PASS'}
    return a, info


def log_density(theta, data, components):
    r2 = np.sum(data[:, 2:4] ** 2, axis=1)
    duration = data[:, 4] - EXPOSURE / 3
    assert np.all(duration > 0)
    if components == 1:
        d, sigma = np.exp(theta)
        scale = 4 * (d * duration + sigma ** 2)
        return -np.log(np.pi * scale) - r2 / scale
    d1, d2, sigma = np.exp(theta[:3])
    w = expit(theta[3])
    scales = 4 * (np.array([d1, d2])[:, None] * duration[None, :] + sigma ** 2)
    terms = -np.log(np.pi * scales) - r2[None, :] / scales
    terms += np.log([w, 1-w])[:, None]
    return logsumexp(terms, axis=0)


def track_weights(data):
    _, inv, counts = np.unique(data[:, 0].astype(int), return_inverse=True, return_counts=True)
    return 1 / counts[inv]


def physical_parameters(theta, components):
    if components == 1:
        d, s = np.exp(theta)
        return {'D_um2_per_s': float(d), 'sigma_um': float(s)}
    d1, d2, s = np.exp(theta[:3])
    w = float(expit(theta[3]))
    if d1 > d2:
        d1, d2, w = d2, d1, 1-w
    return {'D_slow_um2_per_s': float(d1), 'D_fast_um2_per_s': float(d2),
            'sigma_um': float(s), 'observed_slow_component_weight': float(w),
            'interpretation': 'Descriptive observed-displacement mixture; not a molecular bound fraction.'}


def fit(data, components):
    d_bounds = (math.log(.0001), math.log(25))
    s_bounds = (math.log(.010), math.log(.075))
    weights = track_weights(data)
    if components == 1:
        starts = [np.log([d, s]) for d, s in product([.03, .3, 3], [.02, .05])]
        bounds = [d_bounds, s_bounds]
    else:
        starts = [np.array([math.log(d1), math.log(d2), math.log(.035), math.log(w/(1-w))])
                  for d1, d2, w in product([.005, .03, .15], [.5, 3, 10], [.25, .75])]
        bounds = [d_bounds, d_bounds, s_bounds, (math.log(.01/.99), math.log(.99/.01))]
    receipts, successful = [], []
    for start in starts:
        result = minimize(lambda x: -float(np.sum(weights * log_density(x, data, components)) / weights.sum()),
                          start, method='L-BFGS-B', bounds=bounds,
                          options={'maxiter': 500, 'ftol': 1e-11, 'gtol': 1e-7})
        receipts.append({'initial': start.tolist(), 'success': bool(result.success), 'status': int(result.status),
                         'message': str(result.message), 'objective': float(result.fun), 'theta': result.x.tolist(),
                         'iterations': int(result.nit)})
        if result.success and np.isfinite(result.fun):
            successful.append(result)
    if not successful:
        save('optimizer_failure.json', {'components': components, 'all_starts': receipts})
        raise RuntimeError('No successful optimizer start')
    best = min(successful, key=lambda r: r.fun)
    near_bounds = [i for i, (value, bound) in enumerate(zip(best.x, bounds))
                   if min(value-bound[0], bound[1]-value) < 1e-5]
    return best.x, {'parameters': physical_parameters(best.x, components),
                    'train_mean_marginal_log_score': -float(best.fun), 'theta': best.x.tolist(),
                    'near_bound_parameter_indices': near_bounds, 'all_starts': receipts}


def radial_cdf(theta, data, components, radii):
    # Every included observation at one exact frame lag has the same elapsed time.
    duration = float(np.median(data[:, 4])) - EXPOSURE / 3
    if components == 1:
        d, sigma = np.exp(theta)
        return 1 - np.exp(-radii**2 / (4 * (d * duration + sigma**2)))
    d1, d2, sigma = np.exp(theta[:3]); w = expit(theta[3])
    return 1 - w * np.exp(-radii**2/(4*(d1*duration+sigma**2))) - (1-w) * np.exp(-radii**2/(4*(d2*duration+sigma**2)))


def score(data, t1, t2, seed):
    s1, s2 = log_density(t1, data, 1), log_density(t2, data, 2)
    ids, inv, counts = np.unique(data[:, 0].astype(int), return_inverse=True, return_counts=True)
    assert len(ids) >= 100
    per1 = np.bincount(inv, weights=s1) / counts
    per2 = np.bincount(inv, weights=s2) / counts
    delta = per2 - per1
    rng = np.random.default_rng(seed)
    boot = np.array([delta[rng.integers(0, len(delta), len(delta))].mean() for _ in range(1000)])
    by_lag = {}
    for lag in LAGS:
        subset = data[data[:, 1] == lag]
        r = np.sort(np.sqrt(np.sum(subset[:, 2:4]**2, axis=1)))
        empirical_right = np.arange(1, len(r)+1) / len(r)
        empirical_left = np.arange(len(r)) / len(r)
        discrepancies = {}
        for key, theta, c in [('M1', t1, 1), ('M2', t2, 2)]:
            predicted = radial_cdf(theta, subset, c, r)
            discrepancies[key] = float(max(np.max(np.abs(predicted-empirical_right)), np.max(np.abs(predicted-empirical_left))))
        var = np.var(subset[:, 2:4], axis=0)
        by_lag[str(lag)] = {'trajectories': len(subset), 'seconds': float(np.median(subset[:, 4])),
            'mean_log_score_M1': float(log_density(t1, subset, 1).mean()),
            'mean_log_score_M2': float(log_density(t2, subset, 2).mean()),
            'mean_displacement_um': np.mean(subset[:, 2:4], axis=0).tolist(),
            'variance_x_over_y': float(var[0]/var[1]), 'radial_CDF_max_discrepancy': discrepancies}
    return {'eligible_trajectories': len(ids), 'marginal_displacements': len(data),
            'mean_track_averaged_log_score_M1': float(per1.mean()),
            'mean_track_averaged_log_score_M2': float(per2.mean()),
            'paired_score_gain_M2_minus_M1': float(delta.mean()),
            'trajectory_bootstrap_95pct_interval': np.quantile(boot, [.025, .975]).tolist(),
            'uncertainty_scope': 'Conditional on fitted models; trajectory resampling within one cell. Not independent-cell population inference.',
            'by_lag': by_lag}


def plots(held, secondary, t1, t2):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
    for row, (dataset, title) in enumerate([(held, 'Rep1 cell01: held-out trajectories'), (secondary, 'Rep3 cell01: no refit')]):
        for col, lag in enumerate([1, 4]):
            ax = axes[row, col]; d = dataset[dataset[:, 1] == lag]
            r = np.sort(np.sqrt(np.sum(d[:, 2:4]**2, axis=1)))
            ax.step(r, np.arange(1,len(r)+1)/len(r), where='post', color='#111111', lw=1.7, label='Observed')
            grid = np.linspace(0, 1.0, 401)
            ax.plot(grid, radial_cdf(t1,d,1,grid), color='#ba4f2a', label='One component')
            ax.plot(grid, radial_cdf(t2,d,2,grid), color='#246da6', label='Two components')
            ax.set_title(f'{title}\nLag {lag}: {np.median(d[:,4])*1000:.1f} ms')
            ax.set_xlim(0,1); ax.set_ylim(0,1.02); ax.grid(alpha=.2)
            if row==1: ax.set_xlabel('Observed displacement (µm)')
            if col==0: ax.set_ylabel('Cumulative fraction')
    axes[0,0].legend(fontsize=8, loc='lower right')
    fig.suptitle('Real CTCF trajectories: a limited observation-model comparison', weight='bold')
    fig.text(.5,.015,'First valid jump per trajectory per lag. Simplified models omit defocalization; weights are not physical bound fractions.',ha='center',fontsize=8)
    fig.tight_layout(rect=[0,.035,1,.95]); fig.savefig(ROOT/'ctcf_heldout_cdfs.png',dpi=180); plt.close(fig)


def execute():
    seal = verify_seal()
    if (ROOT/'results.json').exists():
        raise RuntimeError('Refusing to overwrite results')
    rep1, q1 = ingest(INPUTS[0]); rep3, q3 = ingest(INPUTS[1])
    train_mask = np.array([partition(int(i))=='train' for i in rep1[:,0]])
    train, held = rep1[train_mask], rep1[~train_mask]
    assert len(np.unique(train[:,0])) >= 100
    assert not set(train[:,0]) & set(held[:,0])
    save('data_quality.json', {'rep1': q1, 'rep3': q3,
        'train_trajectories': len(np.unique(train[:,0])), 'heldout_trajectories': len(np.unique(held[:,0])),
        'split_disjoint': True, 'selection': 'First named cell in each supplied replicate directory, fixed before fitting.'})
    t1, model1 = fit(train,1); t2, model2 = fit(train,2)
    primary = score(held,t1,t2,20261123)
    secondary = score(rep3,t1,t2,20261124)
    receipt = {'schema':'CTCFDisplacementExploratoryResultsV1', 'status':'PASS',
        'completed_utc':datetime.now(timezone.utc).isoformat(), 'frozen_analysis_sha256':sha(ROOT/'FROZEN_ANALYSIS.json'),
        'source_paper':'10.7554/eLife.33125', 'inputs':seal['inputs'], 'model_M1':model1,'model_M2':model2,
        'primary_heldout_rep1':primary, 'secondary_rep3_no_refit':secondary,
        'scope':'Actual empirical displacement reanalysis of two named author-provided cells, using simplified observation models.',
        'limits':['Not a full Spot-On reproduction; no defocalization correction or state-transition inference.',
                  'Mixture weights describe selected observed displacements, not molecular bound fractions.',
                  'Tracked coordinates are processed detections, not raw images; tracking and detection biases remain.',
                  'Overlapping multi-lag increments are not treated as independent biological replicates; scoring is trajectory-averaged and bootstrap clusters by trajectory.',
                  'Two selected cells do not establish population generalization; bootstrap is conditional on the model fit.',
                  'Equal observation law in this comparison does not show that the law is complete or biologically correct.',
                  'No TORUS-specific mechanism, fourteen-layer result, or causally identified count of molecular states.']}
    save('results.json',receipt); plots(held,rep3,t1,t2); verify_seal()
    print(json.dumps({'status':'PASS','model_M1':model1['parameters'],'model_M2':model2['parameters'],
                     'primary':primary,'secondary':secondary},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--freeze',action='store_true');g.add_argument('--execute',action='store_true')
    args=parser.parse_args();freeze() if args.freeze else execute()
