# TORUS PR #32/#33 Evidence Review Report

Status: pending evidence collected, review-normalized, and included only in the limited exploratory pilot. Full scoring remains blocked.

Source repo: `GenghisDarb/TORUS-Theory`

Generated: 2026-06-03 session date.

## Summary

PR #32 and PR #33 form a promising external real repo CI repair cluster. Both are merged PRs from July 5, 2025. They touch actual CI workflow behavior, notebook execution, dependency setup, linting, README checks, and supporting scripts.

The cluster now has four evidence bundles normalized as external real repo episodes. They were included in the limited exploratory pilot only because full historical GitHub Actions job logs are unavailable through the log endpoint, only bounded local reruns were performed, and no original agent/tool transcript custody is available.

Review-normalized bundles:

- `episode_torus_pr32_notebook_kernel_failure`
- `episode_torus_pr32_validation_workflow_failure`
- `episode_torus_pr33_notebook_selector_repair`
- `episode_torus_pr33_readme_guard_warning_only`

## PR #32

PR: https://github.com/GenghisDarb/TORUS-Theory/pull/32

Title: `CI green: expand env, skip heavy notebooks, add papermill & docker README, run black/ruff`

Status:

- merged: true
- head SHA: `3b29ef7af7745cc74f4482f0a19e5247f808726b`
- merge commit SHA: `ea9b9aee766b1d0f5fa19919900f355c2a6213ba`
- changed files: 72
- additions/deletions: 2141 / 1370

Failure/repair theme:

- Broad CI repair and environment expansion.
- Adds or modifies dependency/environment files, notebooks, tests, workflow steps, scripts, and Docker documentation.
- Attempts to make notebook execution, linting, README checks, and validation structure more robust.

Available CI metadata:

- Workflow run `16085973917`, `CI Full`, conclusion `failure`.
- Jobs observed in failed run:
  - `test (3.11)`: failure
  - `lattice-regeneration`: success
  - `validate-structure`: failure
  - `test-suite`: failure
  - `lint`: failure
  - `check-readmes`: failure
  - `run-notebooks`: failure
- Workflow run `16085974136`, `CI Full`, conclusion `success`.
  - Job observed: `validate-structure`: success
- Workflow run `16085973915`, `Execute Validation Notebooks`, conclusion `failure`.

Unavailable CI evidence:

- Full historical job logs are unavailable: sampled job-log fetch returned HTTP 410.
- GitHub Actions rerun is unavailable: rerun attempt on failed run `16085973917` returned HTTP 403 because the workflow run was created over a month ago.

Available patch evidence:

- Changed-file list captured through GitHub.
- Patch diff is available from GitHub as `https://github.com/GenghisDarb/TORUS-Theory/pull/32.diff`.
- Patch diff was not stored locally in this pass because the PR changes 72 files and should be bounded before bundle capture.

Local rerun feasibility:

- Possible, but expensive.
- The workflow includes multiple jobs and broad dependency/notebook execution:
  - install requirements
  - editable install
  - register Jupyter kernel
  - run papermill / nbconvert across selected notebooks
  - run black and ruff
  - README presence checks
- Completed bounded local rerun for `episode_torus_pr32_notebook_kernel_failure`:
  - command: `python -m papermill notebooks\validation\bicycle\recursive_controller_validation.ipynb out_pr32_recursive_controller_validation.ipynb`
  - result: failed with `ValueError: No kernel name found in notebook and no override provided.`
- Not completed for `episode_torus_pr32_validation_workflow_failure`:
  - reason: broad validation-suite and placeholder-scan workflow needs narrower subcommands before local execution.

Suitability for future `external_real_repo_episode` normalization:

- promising, but review required.
- Best use: review `episode_torus_pr32_notebook_kernel_failure` first because it has a concrete bounded local rerun failure.
- Normalized as review-required external real repo evidence. Do not make it scoring-eligible until review decides whether bounded local rerun evidence plus unavailable historical logs is sufficient.

## PR #33

PR: https://github.com/GenghisDarb/TORUS-Theory/pull/33

Title: `CI all green: add full deps, kernel, skip PhaseA notebooks, fix lint & README rules`

Status:

- merged: true
- head SHA: `871b806f75392f7f2a96c6ab925bf74cfd13a80c`
- merge commit SHA: `4a23c43744b07d6f9a71e2fd6229382c266a2731`
- changed files: 6
- additions/deletions: 53 / 4

Failure/repair theme:

- Follow-up CI repair after PR #32.
- Narrows notebook execution behavior and dependency setup.
- Adds `requirements-ci.txt`.
- Adds `tools/list_notebooks.py`.
- Updates CI to register a `torus-ci` Jupyter kernel and execute selected notebooks with that kernel.
- Adds README guard logic and Docker README content.

Available CI metadata:

- Workflow run `16086043836`, `CI Full`, conclusion `failure`.
- Jobs observed in failed run:
  - `test-suite`: failure
  - `validate-structure`: failure
  - `test (3.11)`: failure
  - `lattice-regeneration`: success
  - `lint`: failure
  - `run-notebooks`: failure
  - `check-readmes`: failure
- Workflow run `16086043837`, `CI Full`, conclusion `success`.
  - Job observed: `validate-structure`: success
- Workflow run `16086043832`, `Execute Validation Notebooks`, conclusion `failure`.

Unavailable CI evidence:

- Full historical job logs are unavailable: sampled job-log fetch returned HTTP 410.
- GitHub Actions rerun is unavailable: rerun attempt on failed run `16086043836` returned HTTP 403 because the workflow run was created over a month ago.

Available patch evidence:

- PR #33 diff was fetched during inspection.
- Key changed files:
  - `.github/workflows/ci.yml`
  - `docker/README.md`
  - `requirements-ci.txt`
  - `scripts/cmb_analysis_T-HET_vs_LCDM_adjusted_II.py`
  - `tests/README_guard.py`
  - `tools/list_notebooks.py`
- Patch diff is available from GitHub as `https://github.com/GenghisDarb/TORUS-Theory/pull/33.diff`.
- Patch diff excerpt is stored in the PR #33 normalized evidence bundles.

Local rerun feasibility:

- More feasible than PR #32 because the patch is smaller and focused.
- Completed bounded local rerun for `episode_torus_pr33_notebook_selector_repair`:
  - command: `python tools\list_notebooks.py`
  - result: passed with exit code 0 and listed notebooks while excluding PhaseA.
- Completed bounded local rerun for `episode_torus_pr33_readme_guard_warning_only`:
  - command: `python tests\README_guard.py`
  - result: exited 0 while printing missing README notices.
- Full notebook execution loop was not run in this pass.
- Direct historical shell `check-readmes` rerun was not run in this pass.

Suitability for future `external_real_repo_episode` normalization:

- strong candidate, review-required after normalization.
- Good follow-up episode because it is a focused repair after the broader PR #32 cluster.
- Do not make scoring-eligible until the boundary between bounded local evidence and unavailable historical logs is accepted.

## Current Gate Impact

This report does not change the normalized ledger.

- normalized episodes: `20`
- normalized external real repo episodes: `10`
- limited pilot scoring eligibility count: `10`
- scoring mode: `limited_pilot_only`
- full scoring allowed: `false`
- limited pilot scoring: RUN
