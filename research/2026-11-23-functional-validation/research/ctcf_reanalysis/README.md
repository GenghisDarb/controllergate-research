# Real CTCF displacement reanalysis

This folder contains a completed exploratory reanalysis of two named, real author-provided CTCF tracking files. The original comparison was locally sealed before fitting. A separately sealed post-result Gaussian sensitivity follows it without changing the original outputs.

## Main result

A two-component displacement model has higher heldout trajectory-averaged marginal log score than the tested one-component model in rep1 cell01, and also in rep3 cell01 without refitting. Gains are 0.615888 and 0.877488 nats respectively. After the one-component localization-error estimate reached its cap, a stronger post-result null used a separate free mean/full-covariance Gaussian at each lag. The original mixture still gains 0.624185 and 0.877628 nats respectively.

These are descriptive observed-displacement comparisons. The analysis does not identify a physical bound fraction, prove exactly two molecular states, reproduce the full Spot-On pipeline, test a biological intervention, or validate a TORUS-specific mechanism. Remaining CDF discrepancies are visible in `ctcf_heldout_cdfs.png`.

## Provenance and inputs

Source paper: Hansen et al., eLife 2018, 7:e33125, https://doi.org/10.7554/eLife.33125. Publisher repository: https://github.com/elifesciences-publications/spot-on-matlab, pinned commit `f155c4c889ea124a8f55ab8f620e540628e18f92`.

The parent directory holds the exact decoded `ctcf_rep1_cell01.mat` and `ctcf_rep3_cell01.mat`, the author `SpotOn_main.m`, README, GPLv3 license and compact source manifest. Both MAT files match their provider Git-blob SHA1 and frozen SHA256 receipts. They are the first named cells in the rep1 and rep3 directories, chosen before model fitting.

Coordinates are micrometers. Stored timestamps and settings use 0.0075 s per frame. The author example script says 0.007477 s; the 0.3076% difference is disclosed in `data_quality.json`. We use stored timestamps consistently. One-millisecond illumination and the simple exposure correction are modeling assumptions based on file identity and author example conventions; no independent camera calibration was performed.

## Statistical contract

The whole trajectory is assigned to train or heldout by a fixed hash. Only rep1 trains the models; rep3 is never refitted. At each lag 1–4, use the first exact-lag endpoint pair per trajectory, with no displacement-size selection. Compute each trajectory's average marginal vector log density, then average across trajectories. The training objective uses identical weights.

Marginal increments across lags can overlap; the score is explicitly not an independent-increment joint likelihood. Bootstrap intervals resample complete trajectory-average score differences. They condition on the fitted model and within-cell trajectory exchangeability, and do not include parameter uncertainty, repeated-molecule identity, shared-cell dependence, or between-cell population variability.

The primary mixture uses a constant observed weight across lags and omits defocalization, tracking selection and state switching. These omissions prevent interpreting its 0.788235 observed slow weight as the physical fraction of bound molecules. The post-result Gaussian sensitivity removes the primary Gaussian's cap, isotropy and mean restrictions, but does not address those observation-selection mechanisms.

## Receipts

| File | Purpose |
|---|---|
| `analysis_spec.json` | Primary selection, score, models, bounds and limitations fixed before fitting |
| `analyze_ctcf.py` | Parser, provenance checks, deterministic split, fitting, scoring and plot |
| `FROZEN_ANALYSIS.json` | Local before-fit SHA256 seal of code, specification and inputs |
| `data_quality.json` | Identity, units, timing, missing displacement eligibility and track counts |
| `results.json` | All optimizer starts/statuses, parameter bounds, per-lag diagnostics and primary results |
| `gaussian_null_spec.json` | Explicitly post-result sensitivity contract |
| `gaussian_sensitivity.py` | Weighted analytic Gaussian null and unchanged-mixture comparison |
| `GAUSSIAN_SENSITIVITY_SEAL.json` | Sensitivity seal binding the original results |
| `gaussian_sensitivity_results.json` | Sensitivity results and original-output preservation receipt |

The local seals establish an inspectable sequence; they are not external preregistration or independent timestamp attestation.

## Inspect and verify without refitting

From this directory:

```bash
python -c "from analyze_ctcf import verify_seal; verify_seal(); print('Primary inputs and code verified')"
python -c "from gaussian_sensitivity import verify; verify(); print('Sensitivity and original outputs verified')"
```

The recorded environment was Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, with Matplotlib for the plot. Small optimizer/rounding differences may occur in other environments. Exact source bytes and the numerical method are both recorded.

## Replay in a new directory

Do not delete or overwrite the existing results. Create a fresh directory with this layout:

```text
replay/
  ctcf_rep1_cell01.mat
  ctcf_rep3_cell01.mat
  SpotOn_main.m
  spoton_matlab_README.md
  SpotOn_LICENSE.md
  ctcf_reanalysis/
    analysis_spec.json
    analyze_ctcf.py
    FROZEN_ANALYSIS.json
    gaussian_null_spec.json
    gaussian_sensitivity.py
```

Copy those files exactly, then from the fresh `ctcf_reanalysis` directory run:

```bash
python analyze_ctcf.py --execute
python gaussian_sensitivity.py --freeze
python gaussian_sensitivity.py --execute
```

The original primary seal validates the unchanged code/specification/inputs. The new run emits a new completion time, so the sensitivity must receive a new seal over those new output bytes. Compare scientific values against the archived results with a stated numerical tolerance; whole result-file hashes will differ because the completion times differ. The scripts deliberately refuse to overwrite existing result files.

## Relation to the accompanying reaction-network benchmark

The CTCF observations are not observations of the LDH/GAPDH network. The two workstreams test different obligations: faithful execution of a declared reaction/resource contract, and quantitative adequacy of an observation model on a small real dataset. Their combination motivates an auditable validation workflow; it does not establish a literal one-to-one biological mechanism across the two systems.
