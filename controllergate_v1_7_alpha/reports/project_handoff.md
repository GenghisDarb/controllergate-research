# ControllerGate Project Handoff

## Completed

- Created alpha branch: `controllergate-v1.7-alpha-real-trace-pilot`.
- Froze v1.6 at psi with corrected claim boundary.
- Recorded supplied v1.6-psi artifact hashes and custody evidence.
- Fresh-reran the psi verifier and analyzer from the supplied package and external fixture artifact.
- Created v1.7-alpha trace folder structure.
- Added v1.7-alpha episode schema and artifact manifest schema.
- Added raw episode template files.
- Added ledger validation and trace audit scripts.
- Added episode review classification and scoring eligibility audit.
- Added `episodes_pending/` collection area with 10 generic templates.
- Added starter pending skeletons for iota and pi correction events.
- Added `artifacts_intake/` folders for iota and pi.

## Current Verification State

v1.6 psi:

- Packaged report: `51 / 51`.
- Fresh rerun: `51 / 51`.
- Analyzer: all criteria passed.
- Package SHA manifest: verified.
- Fixture SHA manifest: verified.

v1.7-alpha:

- Ledger exists.
- Ledger contains 20 normalized evidence records.
- Schema is valid JSON.
- Ledger validation passes with 20 records.
- Audit reports `REVIEW_REQUIRED`.
- Episode review classification passes.
- Classification counts: 2 correction-review episodes, 8 controlled benchmark evidence episodes, 10 external real repo episodes.
- Scoring eligibility count for v1.7-alpha limited real repo pilot: 10.
- Scoring mode: `limited_pilot_only`.
- Full scoring allowed: `false`.
- Limited pilot scoring has been run.
- Limited pilot result review is complete.
- Full scoring has not been run.
- GitHub remote is configured at `https://github.com/GenghisDarb/controllergate-research.git`.
- External source discovery has started with `GenghisDarb/TORUS-Theory`.
- TORUS-Theory candidate inventory exists, and PR #15/#16/#17/#19/#20/#32/#33/#34 are normalized as external real repo episodes eligible only for a limited exploratory pilot.

## Blocker

The project cannot honestly run full v1.7-alpha scoring yet. The limited exploratory pilot has run and has been reviewed as `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`.

Current limited-pilot state: 10 external real repo episodes have been collected, normalized, reviewed, and classified as eligible for `limited_pilot_only`. Controlled benchmark evidence and correction-review episodes remain excluded from real repo scoring.

Current recommended next milestone: v1.7-beta second-repo external evidence collection, preferably TatMapper or another non-TORUS repository with real CI/build/test failures.

Iota/pi package evidence status:

- iota package ZIP and extracted notebook are present in `artifacts_intake/iota/`.
- pi package ZIP and extracted notebook are present in `artifacts_intake/pi/`.
- iota package runner plus analyzer rerun: `16 / 20`.
- pi package runner plus analyzer rerun: `27 / 28`.
- iota package SHA manifest: 19 entries checked, 0 mismatches.
- pi package SHA manifest: 24 entries checked, 0 mismatches.

Additional v1.6 ladder evidence status:

- kappa package/rerun evidence: `20 / 20`, SHA manifest 24 entries checked, 0 mismatches.
- lambda package/rerun evidence: `20 / 20`, SHA manifest 20 entries checked, 0 mismatches.
- mu package/rerun evidence: `20 / 20`, SHA manifest 20 entries checked, 0 mismatches.
- nu package/rerun evidence: `21 / 21`, SHA manifest 24 entries checked, 0 mismatches.
- xi package/rerun evidence: `23 / 23`, SHA manifest 25 entries checked, 0 mismatches.
- omicron package/rerun evidence: `25 / 25`, SHA manifest 24 entries checked, 0 mismatches.
- rho package/rerun evidence: `28 / 28`, SHA manifest 24 entries checked, 0 mismatches.
- psi package/rerun evidence: `51 / 51`, package SHA manifest 8 entries checked, fixture SHA manifest 3 entries checked, 0 mismatches.

Immediate blocker for full scoring: the reviewed normalized trace ledger has 10 `external_real_repo_episode` entries approved for limited exploratory pilot mode only. The audit is no longer blocked, but it is not full scoring approval.

Limited pilot review:

- technical report: `controllergate_v1_7_alpha/reports/limited_pilot_scoring/v1_7_alpha_limited_pilot_result_review.md`
- short summary: `controllergate_v1_7_alpha/reports/limited_pilot_scoring/README.md`
- audit JSON: `controllergate_v1_7_alpha/traces/audits/limited_pilot_scoring/limited_pilot_result_review.json`

Audit review reasons:

- iota and pi are false-success correction records with original builder/critic transcript custody still marked for review.
- kappa, lambda, mu, nu, xi, omicron, rho, and psi are controlled-benchmark evidence episodes and are not eligible for the v1.7-alpha real repo pilot score.
- TORUS PR #15/#16/#17/#19/#20/#32/#33/#34 are external real repo episodes approved only for a limited exploratory pilot because historical job logs returned HTTP 410, reruns are bounded or unavailable, and original agent/tool traces are unavailable.

Required minimum next input:

- one populated non-TORUS Git repository with commits and a configured remote, preferably TatMapper, or
- exported real maintenance episode bundles from a second repo containing CI logs, patch diffs, agent/tool traces, generated artifact manifests, and outcome evidence.

Current external candidate source:

- `GenghisDarb/TORUS-Theory`
- strongest initial candidates: PR #16, PR #15, PR #17, PR #19/#20, and PR #32/#33/#34
- PR #15 and PR #16 now have normalized external real repo episodes with captured PR diffs and fresh local rerun evidence.
- PR #19 and PR #20 now have normalized external real repo episodes with captured PR diffs and fresh local rerun failure evidence.
- Reviewed TORUS episode folders now exist for PR #15, #16, #19, and #20 using the `episode_torus_*` naming.
- PR #32/#33 target report has been updated; both are promising CI repair candidates and now have four normalized review-required evidence bundles.
- PR #32/#33 normalized bundles:
  - `episode_torus_pr32_notebook_kernel_failure`
  - `episode_torus_pr32_validation_workflow_failure`
  - `episode_torus_pr33_notebook_selector_repair`
  - `episode_torus_pr33_readme_guard_warning_only`
- These PR #32/#33 bundles are normalized and eligible only for the limited exploratory pilot.
- PR #17/#34 now have normalized external evidence bundles:
  - `episode_torus_pr17_latex_workflow_repair`
  - `episode_torus_pr34_readme_guard_failure`
- These PR #17/#34 bundles are normalized and eligible only for the limited exploratory pilot.
- blocker: sampled historical GitHub Actions job logs returned HTTP 410, and original agent/tool traces are unavailable, so normalization requires review of whether fresh local reruns plus PR metadata are sufficient.

## Do Not Claim Yet

Do not claim:

- v1.7-alpha passes;
- ControllerGate repairs real repositories;
- ControllerGate supervises real agent tool loops;
- hidden/downstream improvement on real traces.

Those claims require scoring-eligible external real repo episodes, review classification approval, and a passing future-leakage audit.

The limited pilot result review also forbids claiming real-repo memory lift because discovered/no-memory/predefined/poisoned memory baselines were unavailable in the TORUS external evidence.
