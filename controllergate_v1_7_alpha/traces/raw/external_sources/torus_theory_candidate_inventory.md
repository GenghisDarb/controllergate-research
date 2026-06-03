# TORUS-Theory External Episode Candidate Inventory

Status: candidate discovery only. No TORUS-Theory episode has been normalized or classified as scoring-eligible.

Generated: 2026-06-03 session date.

Repository inspected: `GenghisDarb/TORUS-Theory`

Repository URL: `https://github.com/GenghisDarb/TORUS-Theory`

## Discovery Summary

TORUS-Theory is a viable external source candidate for v1.7-alpha because it has real GitHub pull requests, merged maintenance patches, notebook repairs, CI workflow edits, and GitHub Actions run metadata.

It is not yet sufficient for scoring because complete episode bundles have not been created and historical GitHub Actions job logs are currently unavailable through the job-log endpoint.

Observed historical log blocker:

```text
GitHub Actions job log fetch returned HTTP 410 for sampled historical jobs.
```

Interpretation: workflow run and job metadata are available, but full historical job logs may have expired. Any episode that depends on those logs must record `UNAVAILABLE: GitHub Actions job log API returned 410` unless fresh reruns or archived logs are supplied.

Fresh local rerun status:

- PR #15 local rerun completed and reproduced failure: `nbformat.reader.NotJSONError: Notebook does not appear to be JSON`.
- PR #16 local rerun completed and reproduced success: `TORUS-POSITIVE` found in the output notebook.
- These are local rerun outputs, not original GitHub-hosted CI logs.

## Candidate PRs

| Candidate | PR | Status | Head SHA | Evidence available | Missing / blocked evidence | Initial priority |
| --- | ---: | --- | --- | --- | --- | --- |
| torus_pr_016_paircorr_rebuild | #16 | merged | `e8e5c5b181e83261c2a2e12ff4a287d824053b15` | PR metadata, local PR diff, body describes corrupt notebook replacement, successful PairCorr workflow metadata, fresh local rerun success | Original GitHub job logs returned 410; original agent/tool trace unavailable | high |
| torus_pr_015_notebook_force_clean | #15 | merged | `6f6380bcf75c7488b98d7a903eb51ede50e21435` | PR metadata, local PR diff, body describes XML-to-nbformat cleanup, PairCorr workflow failure metadata, fresh local rerun failure | Original GitHub job logs returned 410; original agent/tool trace unavailable | high |
| torus_pr_017_latex_workflow | #17 | merged | `b1efc970915b84f9bcdc70cff76eed34cc9bdf93` | PR metadata, workflow patch target, body describes XeTeX/lacheck/portable grep/log dumping changes, CI success metadata | Need actual book workflow failure/success logs or archived output | medium |
| torus_pr_019_paircorr_kernelspec | #19 | merged | `4df944b396fc683ba0ed1cc6e2b7386033825bff` | PR metadata, one-file notebook patch, CI Full success metadata, PairCorr failure metadata | Full job logs returned 410; relationship to #20/#16 needs evidence review | medium |
| torus_pr_020_paircorr_hann_fallback | #20 | closed unmerged | `b8514854d032286cbbf6e8b2f0607fa50502384e` | PR metadata, one-file notebook patch, explicit scipy hann fallback title | Not merged; needs outcome evidence and reason for closure before use | medium |
| torus_pr_032_ci_fix | #32 | merged | `3b29ef7af7745cc74f4482f0a19e5247f808726b` | PR metadata, 72 changed files, CI repair title/body, mixed failure/success workflow metadata | Large patch needs bounded evidence extraction; full failed job logs returned 410 | medium |
| torus_pr_033_ci_allgreen | #33 | merged | `871b806f75392f7f2a96c6ab925bf74cfd13a80c` | PR metadata, CI repair title/body, six changed files, mixed failure/success workflow metadata | Full failed job logs returned 410; need clarify duplicate CI Full workflows | medium |
| torus_pr_034_pylance_fix | #34 | merged | `fef86da17bfaf087f6ba5143e617bad3fea6b033` | PR metadata, 15 changed files, Pylance/CI title, mixed failure/success workflow metadata | Full failed job logs returned 410; needs patch and outcome evidence extraction | low |

## Sampled Workflow Metadata

| PR | Workflow run | Workflow | Conclusion | Jobs observed |
| ---: | ---: | --- | --- | --- |
| #16 | `15372746933` | Execute PairCorr Notebooks | success | `run-paircorr-benchmark`: success |
| #16 | `15372746936` | CI Full | success | metadata available |
| #16 | `15372746950` | CI Full | success | `validate-structure`: success |
| #15 | `15372702999` | Execute PairCorr Notebooks | failure | `run-paircorr-benchmark`: failure |
| #17 | `15373254396` | CI Full | success | metadata available |
| #17 | `15373254397` | CI Full | success | metadata available |
| #17 | `15373254400` | Execute PairCorr Notebooks | failure | `run-paircorr-benchmark`: failure |
| #19 | `15788453686` | CI Full | success | metadata available |
| #19 | `15788453688` | CI Full | success | metadata available |
| #19 | `15788453699` | Execute PairCorr Notebooks | failure | metadata available |
| #32 | `16085973917` | CI Full | failure | test, lint, notebooks, README, and structure failures |
| #32 | `16085974136` | CI Full | success | `validate-structure`: success |
| #33 | `16086043836` | CI Full | failure | test, lint, notebooks, README, and structure failures |
| #33 | `16086043837` | CI Full | success | `validate-structure`: success |
| #34 | `16086568962` | CI Full | failure | metadata available |
| #34 | `16086568970` | CI Full | success | metadata available |

## Candidate Completion Requirements

Starter pending bundles now exist for PR #15 and PR #16 under `controllergate_v1_7_alpha/episodes_pending/`.

Before any TORUS-Theory episode can become a normalized `external_real_repo_episode`, create a complete evidence bundle with:

- PR metadata and canonical URL.
- Patch diff or bounded per-file patches.
- CI log or explicit `UNAVAILABLE: GitHub Actions job log API returned 410`.
- Failing command or workflow/job name.
- Files read and written by the repair.
- Outcome evidence, including merge status and relevant workflow conclusions.
- Decision-time versus outcome-only separation.
- Artifact manifest with GitHub URLs, SHAs, and log availability.

## Current Classification Impact

This inventory does not change v1.7-alpha scoring eligibility.

- normalized episodes: `10`
- external_real_repo_episode entries: `0`
- scoring eligibility count for real repo pilot: `0`
- scoring allowed: `false`
- scoring: NOT RUN
