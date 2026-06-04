# ControllerGate v1.7-alpha Trace Audit

Status: normalized ledger review required; limited pilot scoring has been run.

## Audit Result

`validate_ledger.py` passes with 20 normalized evidence records. `audit_trace_ledger.py` reports `REVIEW_REQUIRED`, not `PASS`. Limited pilot scoring has been run on the 10 TORUS-Theory external real repo episodes; full scoring remains blocked.

The review state is intentional: iota and pi are false-success correction episodes, kappa through psi are controlled benchmark evidence episodes, and the TORUS-Theory rows preserve review-required caveats around unavailable historical logs and bounded local reruns.

The companion review-classification audit marks 10 episodes as `external_real_repo_episode` and reports `limited_pilot_only`. Full v1.7-alpha real repo scoring remains blocked.

## Findings

| Check | Result | Reason |
| --- | --- | --- |
| Episode ledger exists | PASS | `traces/normalized/episodes.jsonl` contains 20 normalized records. |
| Evidence bundle count | PASS | Twenty completed pending evidence bundles were normalized. |
| SHA manifest audit | PASS | Normalized records report verified SHA manifests with 0 mismatches. |
| Runner/analyzer audit | PASS | Normalized records report runner and analyzer completion. |
| Correction episode audit | REVIEW_REQUIRED | Iota and pi are false-success / correction episodes and require reviewer custody before scoring use. |
| Controlled benchmark audit | REVIEW_REQUIRED | Kappa through psi are verified benchmark evidence episodes, not external real-repository traces. |
| Unsupported claim audit | PASS | Only limited exploratory pilot scoring is claimed; full scoring and broad real-repo claims remain blocked. |

## Required Before Scoring

Full scoring remains blocked. Any future scoring expansion must keep decision-time evidence separate from outcome-only evidence and must not convert controlled benchmark or correction-review episodes into real repo scoring input.
