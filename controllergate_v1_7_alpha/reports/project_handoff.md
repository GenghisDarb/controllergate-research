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
- Ledger contains 10 normalized evidence records.
- Schema is valid JSON.
- Ledger validation passes with 10 records.
- Audit reports `REVIEW_REQUIRED`.
- Episode review classification passes.
- Classification counts: 2 correction-review episodes, 8 controlled benchmark evidence episodes, 0 external real repo episodes.
- Scoring eligibility count for v1.7-alpha real repo pilot: 0.
- Scoring has not been run.
- GitHub remote is configured at `https://github.com/GenghisDarb/controllergate-research.git`.
- External source discovery has started with `GenghisDarb/TORUS-Theory`.
- TORUS-Theory candidate inventory exists, but no TORUS episode is normalized yet.

## Blocker

The project cannot honestly score v1.7-alpha until external real repository / real agent maintenance episodes are supplied and classified as scoring eligible.

Current threshold: at least 10 scoring-eligible external real repo episodes with complete evidence bundles must be collected, normalized, reviewed, and classified before scoring.

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

Immediate blocker for scoring: the reviewed normalized trace ledger has 0 `external_real_repo_episode` entries. The audit is no longer blocked, but it is not a scoring approval.

Audit review reasons:

- iota and pi are false-success correction records with original builder/critic transcript custody still marked for review.
- kappa, lambda, mu, nu, xi, omicron, rho, and psi are controlled-benchmark evidence episodes and are not eligible for the v1.7-alpha real repo pilot score.

Required minimum next input:

- one populated Git repository with commits and a configured remote, or
- exported real maintenance episode bundles containing CI logs, patch diffs, agent/tool traces, generated artifact manifests, and outcome evidence.

Current external candidate source:

- `GenghisDarb/TORUS-Theory`
- strongest initial candidates: PR #16, PR #15, PR #17, PR #19/#20, and PR #32/#33/#34
- blocker: sampled historical GitHub Actions job logs returned HTTP 410, so complete bundles must either capture fresh reruns, locate archived logs, or mark logs explicitly unavailable.

## Do Not Claim Yet

Do not claim:

- v1.7-alpha passes;
- ControllerGate repairs real repositories;
- ControllerGate supervises real agent tool loops;
- hidden/downstream improvement on real traces.

Those claims require scoring-eligible external real repo episodes, review classification approval, and a passing future-leakage audit.
