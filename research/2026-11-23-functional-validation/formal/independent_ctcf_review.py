"""Recompute reported prediction scores with separate parsing and densities.

No model refit or new hypothesis search. This is a computational verification
of the saved model comparison, including the post-result Gaussian check.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from scipy.special import expit, logsumexp
from scipy.stats import multivariate_normal

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'research'
ANALYSIS = DATA / 'ctcf_reanalysis'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(filename):
    m = loadmat(DATA / filename, squeeze_me=True, struct_as_record=False)
    rows = []
    for number, track in enumerate(np.atleast_1d(m['trackedPar'])):
        xy = np.asarray(track.xy).reshape(-1, 2)
        frames = np.atleast_1d(track.Frame)
        times = np.atleast_1d(track.TimeStamp)
        # All actual retained files have contiguous frames. This independently
        # permits the first vector to be obtained by index instead of the
        # analysis implementation's first-valid-endpoint search.
        assert np.all(np.diff(frames) == 1)
        for lag in (1, 2, 3, 4):
            if len(frames) > lag:
                delta = xy[lag] - xy[0]
                rows.append((number, lag, delta[0], delta[1], times[lag] - times[0]))
    return np.asarray(rows)


def component_density(data, diffusion, sigma):
    out = np.empty(len(data))
    for lag in (1, 2, 3, 4):
        use = data[:, 1] == lag
        dt = data[use, 4]
        assert np.ptp(dt) < 1e-12
        variance = 2 * (diffusion * (float(np.mean(dt)) - .001 / 3) + sigma ** 2)
        out[use] = multivariate_normal.logpdf(data[use, 2:4], mean=[0, 0], cov=np.eye(2) * variance)
    return out


def average_by_track(data, scores):
    unique, inv = np.unique(data[:, 0].astype(int), return_inverse=True)
    return np.bincount(inv, weights=scores) / np.bincount(inv)


def main():
    original_path = ANALYSIS / 'results.json'
    sensitivity_path = ANALYSIS / 'gaussian_sensitivity_results.json'
    original = json.loads(original_path.read_text())
    sens = json.loads(sensitivity_path.read_text())
    first = read_rows('ctcf_rep1_cell01.mat')
    selected = np.array([int(hashlib.sha256(f'ctcf-split-v1:{int(n)}'.encode()).hexdigest()[:8], 16) % 10 >= 7
                         for n in first[:, 0]])
    datasets = {'primary_heldout_rep1': first[selected],
                'secondary_rep3_no_refit': read_rows('ctcf_rep3_cell01.mat')}
    m1 = original['model_M1']['parameters']
    m2 = original['model_M2']['parameters']
    w = m2['observed_slow_component_weight']
    checks = {}
    for name, data in datasets.items():
        one = component_density(data, m1['D_um2_per_s'], m1['sigma_um'])
        slow = component_density(data, m2['D_slow_um2_per_s'], m2['sigma_um'])
        fast = component_density(data, m2['D_fast_um2_per_s'], m2['sigma_um'])
        two = logsumexp(np.vstack([slow + np.log(w), fast + np.log1p(-w)]), axis=0)
        free = np.empty(len(data))
        for lag in (1, 2, 3, 4):
            use = data[:, 1] == lag
            model = sens['fitted_gaussian_models'][str(lag)]
            free[use] = multivariate_normal.logpdf(data[use, 2:4], mean=model['mean_um'], cov=model['covariance_um2'])
        one_t, two_t, free_t = [average_by_track(data, v) for v in (one, two, free)]
        primary_gain, sensitivity_gain = float((two_t - one_t).mean()), float((two_t - free_t).mean())
        original_error = abs(primary_gain - original[name]['paired_score_gain_M2_minus_M1'])
        sensitivity_error = abs(sensitivity_gain - sens[name]['paired_gain_M2_minus_free_Gaussian'])
        assert original_error < 1e-11 and sensitivity_error < 1e-11
        assert len(two_t) == original[name]['eligible_trajectories']
        checks[name] = {'trajectories': len(two_t), 'marginal_displacements': len(data),
                        'verified_primary_gain': primary_gain,
                        'verified_sensitivity_gain': sensitivity_gain,
                        'absolute_primary_discrepancy': original_error,
                        'absolute_sensitivity_discrepancy': sensitivity_error}
    output = {'status': 'PASS', 'reviewed_utc': datetime.now(timezone.utc).isoformat(),
              'implementation': 'Separate direct-index parser for verified contiguous tracks; scipy multivariate_normal densities; no imported analysis functions.',
              'source_result_sha256': digest(original_path),
              'sensitivity_result_sha256': digest(sensitivity_path),
              'review_code_sha256': digest(Path(__file__)), 'checks': checks,
              'scope': 'Verifies recorded scores and cohort counts only; does not improve observation-model validity or biological replication.'}
    (ROOT / 'formal/independent_ctcf_review.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
