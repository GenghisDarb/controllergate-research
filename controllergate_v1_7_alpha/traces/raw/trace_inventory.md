# ControllerGate v1.7-alpha Trace Inventory

Status: trace discovery and custody setup only. No v1.7-alpha policy scoring or pass claim is made here.

Generated: 2026-06-03 session date. Supplied artifact timestamps observed on disk were 2026-06-02 America/Los_Angeles.

Repository path: `C:\Users\thisb\OneDrive\Documents\ControllerGate`

Current branch: `controllergate-v1.7-alpha-real-trace-pilot`

## Local Repository Status

The local checkout now has an alpha scaffold commit on `controllergate-v1.7-alpha-real-trace-pilot`, but no configured remote.

Observed commands:

```powershell
git status --short --branch
git log --oneline --decorate -n 30
rg --files
git remote -v
Get-ChildItem -Force
Get-ChildItem -Force -Recurse -Depth 3
git status --porcelain=v1 -uall
git branch --all --verbose
```

Observed facts:

| Evidence source | Status | Reason |
| --- | --- | --- |
| Local Git commits | PARTIAL | Scaffold commit `46ca47c` exists, but no real maintenance history exists in this repo yet. |
| Local branch history | PARTIAL | Initial discovery observed no commits on `master`; the scaffold now sits on branch `controllergate-v1.7-alpha-real-trace-pilot`. |
| Git remotes | UNAVAILABLE | `git remote -v` returned no configured remotes. |
| Working-tree files before scaffold | UNAVAILABLE | `rg --files` returned no files; recursive listing found only `.git/`. |
| CI configuration | UNAVAILABLE | No `.github/`, workflow files, package files, or build/test configuration files existed in the working tree. |
| Issues / PR metadata | UNAVAILABLE | No GitHub remote is configured locally, so issue and PR history cannot be discovered from this checkout. |
| CI logs / failed runs | UNAVAILABLE | No local workflow files, artifacts, logs, or remote run references were present. |
| Agent/tool traces | UNAVAILABLE | No trace files or agent-run artifacts existed in the working tree. |
| Generated artifacts | PARTIAL | Supplied v1.6-psi benchmark ZIPs and notebook exist outside the repo and were inspected as controlled benchmark artifacts. |

## Supplied v1.6-psi Artifacts

The following supplied files were inspected:

| Artifact | Path | SHA256 |
| --- | --- | --- |
| External fixture artifact ZIP | `C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_ExternalFixtureArtifact.zip` | `1231ed48b78421f2850f1bf776d6ff9fdce12a94429ef8a83b4b6fccdb7f9c0d` |
| Benchmark package ZIP | `C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_SeparateFixtureArtifactCustodyTrial_Package.zip` | `0bfd1541f4c8e542efd846a72e30b60fdbe3657cae6f95c6fdff8a8a14f87243` |
| Notebook | `C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_SeparateFixtureArtifactCustodyTrial.ipynb` | `d3211e046f04c5f318911bd5010f41c9704d01fefd5f7dfc547d068b12622050` |

These artifacts support v1.6 freeze/custody claims. They do not supply real repository maintenance episodes for v1.7-alpha scoring.

## Candidate Maintenance Episodes

The episode ingestion scaffold is ready under `controllergate_v1_7_alpha/episodes_pending/`.

Current pending bundles:

- `episode_001` through `episode_010`: generic real maintenance episode templates.
- `episode_iota_misreport`: starter skeleton for the known v1.6-iota false success/report mismatch correction.
- `episode_pi_misreport`: starter skeleton for the known v1.6-pi false success/failed criterion correction.
- `episode_kappa_verified_recovery`: package-backed v1.6-kappa recovery evidence.
- `episode_lambda_noisy_drift`: package-backed v1.6-lambda noisy drift evidence.
- `episode_mu_discovery_vs_predefinition`: package-backed v1.6-mu discovery-vs-predefinition evidence.
- `episode_nu_sparse_recurrence`: package-backed v1.6-nu sparse recurrence evidence.
- `episode_xi_temporal_inversion`: package-backed v1.6-xi temporal inversion evidence.
- `episode_omicron_scripted_spoofing`: package-backed v1.6-omicron scripted spoofing evidence.
- `episode_rho_pi_recovery_repair`: package-backed v1.6-rho pi-recovery repair evidence.
- `episode_psi_custody_closure`: package-backed v1.6-psi custody closure evidence.

Artifact intake folders have been created under `controllergate_v1_7_alpha/artifacts_intake/`. The iota and pi package ZIPs are present, and their notebooks were extracted from inside the supplied packages into the expected intake filenames.

The iota, pi, kappa, lambda, mu, nu, xi, omicron, rho, and psi pending episodes now contain package-backed runner/analyzer, decision report, and SHA manifest evidence.

These 10 episodes have also been normalized into `traces/normalized/episodes.jsonl`.

Normalization status:

- normalized records: `10`
- validator: PASS
- audit: REVIEW_REQUIRED
- review classification audit: PASS
- correction_review_episode: `2`
- controlled_benchmark_evidence: `8`
- external_real_repo_episode: `0`
- scoring eligibility count for real repo pilot: `0`
- scoring allowed: `false`
- scoring: NOT RUN

The audit requires review because iota/pi are false-success correction records with transcript custody still marked for review, and kappa through psi are controlled-benchmark evidence episodes. The review classification confirms none of the current records are external real repo maintenance episodes.

Review classification:

| Category | Count | Allowed use |
| --- | ---: | --- |
| correction_review_episode | 2 | report-integrity training/evaluation only |
| controlled_benchmark_evidence | 8 | scaffold validation, provenance verification, benchmark-history context only |
| external_real_repo_episode | 0 | required for real repo pilot scoring |
| excluded_from_scoring | 0 | not allowed for scoring |

## Non-Episode Evidence: v1.6-psi Custody Closure

The supplied v1.6-psi benchmark package and fixture artifact were verified separately:

```text
benchmark complete: 51 / 51 passed
separate external fixture artifact verified
verified fixture artifact only scored
decision report: 51 / 51 passed
all criteria passed
```

Use this as prior benchmark custody evidence only.

Do not load it into `episodes.jsonl` as a real trace episode.

## Required Next Evidence

Scoring is blocked because the reviewed normalized ledger contains 0 `external_real_repo_episode` entries.

## External Source Discovery

First external source inspected: `GenghisDarb/TORUS-Theory`.

Discovery result: viable candidate source, not yet normalized evidence.

TORUS-Theory has real GitHub pull requests, merged maintenance patches, notebook repairs, CI workflow edits, and GitHub Actions run/job metadata. Candidate details are recorded in `controllergate_v1_7_alpha/traces/raw/external_sources/torus_theory_candidate_inventory.md`.

Important blocker: sampled historical GitHub Actions job logs returned HTTP 410 from the job-log endpoint. Workflow run metadata and job conclusions are available, but original GitHub-hosted CI logs are not currently available through that endpoint.

Fresh local rerun evidence has been added for the first linked candidate pair:

- PR #15 local rerun reproduced failure at head SHA `6f6380bcf75c7488b98d7a903eb51ede50e21435`: `nbformat.reader.NotJSONError`.
- PR #16 local rerun reproduced success at head SHA `e8e5c5b181e83261c2a2e12ff4a287d824053b15`: `TORUS-POSITIVE` found in output notebook.
- PR #19 local rerun reproduced failure at head SHA `4df944b396fc683ba0ed1cc6e2b7386033825bff`: NumPy version assertion.
- PR #20 local rerun reproduced failure at head SHA `b8514854d032286cbbf6e8b2f0607fa50502384e`: NumPy version assertion; PR was closed unmerged.
- These are local reruns, not original GitHub Actions logs.

Current external candidate status:

| Source | Candidate PRs | Evidence status | Scoring impact |
| --- | --- | --- | --- |
| `GenghisDarb/TORUS-Theory` | #15, #16, #17, #19, #20, #32, #33, #34 | #15/#16/#19/#20 pending bundles include PR diffs plus local reruns; others remain candidate metadata only | none; external_real_repo_episode count remains 0 |

To proceed with v1.7-alpha, provide at least one of:

1. A populated ControllerGate or TatMapper Git checkout with commits and a configured GitHub remote.
2. A GitHub remote URL for the target repository.
3. Exported CI logs, PR diffs, issue links, agent traces, generated artifact manifests, or rerun outputs from real maintenance episodes.

Each real episode should receive its own evidence bundle:

```text
controllergate_v1_7_alpha/traces/raw/episode_001/
  ci_log.txt
  failing_command.txt
  patch_diff.diff
  agent_trace.md
  files_read.txt
  files_written.txt
  outcome.md
  artifact_manifest.txt
```

If an evidence file is unavailable, the episode bundle should contain a note with `UNAVAILABLE: reason`.

Pending collection instructions are in `controllergate_v1_7_alpha/docs/episode_collection_instructions.md`. External real repo episodes should be normalized and then classified as `external_real_repo_episode` only when their evidence supports that category.

## Current Artifact Intake Status

The first two correction episodes now have these intake files:

```text
controllergate_v1_7_alpha/artifacts_intake/iota/ControllerGate_v1_6_iota_PrecisionGatedBudgetMemoryTrial_Package.zip
controllergate_v1_7_alpha/artifacts_intake/iota/ControllerGate_v1_6_iota_PrecisionGatedBudgetMemoryTrial.ipynb
controllergate_v1_7_alpha/artifacts_intake/pi/ControllerGate_v1_6_pi_AdaptiveAdversaryCounterQuarantineTrial_Package.zip
controllergate_v1_7_alpha/artifacts_intake/pi/ControllerGate_v1_6_pi_AdaptiveAdversaryCounterQuarantineTrial.ipynb
```

Iota package evidence:

- package SHA256: `ae55208bc7062c420032be52feedbc3b59a08f1f85d0c0f3debd9829dcc13e1b`
- notebook SHA256: `09007acdfc4cb59ec0fa70f702b0a94fcf115605320d4bfbc6f4b7224d611533`
- packaged result: `16 / 20`
- package runner plus analyzer rerun: `16 / 20`
- SHA manifest verification: 19 entries checked, 0 mismatches

Pi package evidence:

- package SHA256: `127065cb38316ebcfc9a79c2057b9fedbea347a00071156c22a4392fddbc16c7`
- notebook SHA256: `9837187968c68d5e86276d704970ccabfa9c6fe520284347fe1b53563625ddda`
- packaged result: `27 / 28`
- package runner plus analyzer rerun: `27 / 28`
- SHA manifest verification: 24 entries checked, 0 mismatches

Additional v1.6 ladder package evidence:

| Episode | Packaged result | Rerun result | SHA manifest |
| --- | --- | --- | --- |
| kappa | `20 / 20` | `20 / 20` | 24 entries, 0 mismatches |
| lambda | `20 / 20` | `20 / 20` | 20 entries, 0 mismatches |
| mu | `20 / 20` | `20 / 20` | 20 entries, 0 mismatches |
| nu | `21 / 21` | `21 / 21` | 24 entries, 0 mismatches |
| xi | `23 / 23` | `23 / 23` | 25 entries, 0 mismatches |
| omicron | `25 / 25` | `25 / 25` | 24 entries, 0 mismatches |
| rho | `28 / 28` | `28 / 28` | 24 entries, 0 mismatches |
| psi | `51 / 51` | `51 / 51` | package: 8 entries, 0 mismatches; fixture: 3 entries, 0 mismatches |

Remaining blocker: the normalized and reviewed ledger has 0 external real repo episodes. External repo evidence collection must happen before any v1.7-alpha real repo scoring.
