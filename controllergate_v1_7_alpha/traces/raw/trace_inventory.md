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
- scoring: NOT RUN

The audit requires review because iota/pi are false-success correction records with transcript custody still marked for review, and kappa through psi are controlled-benchmark evidence episodes that must be reviewed before being treated as real-trace scoring input.

| Field | Value |
| --- | --- |
| episode_id | PENDING: `episode_iota_misreport` and `episode_pi_misreport` are known candidate correction events; `episode_001` through `episode_010` are templates. |
| commit or PR reference | UNAVAILABLE: no commits, PR refs, or remotes available |
| failing command or CI job | UNAVAILABLE: no real CI/test commands or logs available |
| failure log path or URL | UNAVAILABLE: no real logs or remote URLs available |
| patch attempt or diff | UNAVAILABLE: no real commits, diffs, or patch attempts available |
| files read or changed | UNAVAILABLE: no real episode files available |
| agent/tool trace | TODO_REQUIRED: starter summaries exist for iota and pi, but original traces/transcripts are not present in the repo. |
| visible test result | UNAVAILABLE: no real tests or CI runs available |
| downstream/hidden result | UNAVAILABLE: no downstream result evidence available |
| stale read / false completion / drift / artifact mismatch signal | UNAVAILABLE: no real episode evidence available |
| evidence available at decision time | UNAVAILABLE: no real episode evidence available |
| future outcome evidence forbidden during policy selection | UNAVAILABLE: no real episode evidence available |

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

Scoring is blocked until at least 10 real episodes have complete evidence bundles and are normalized into `traces/normalized/episodes.jsonl`.

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

Pending collection instructions are in `controllergate_v1_7_alpha/docs/episode_collection_instructions.md`.

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

Remaining blocker: the evidence is still pending, not normalized. A trace-ledger structure review and future-leakage audit must happen before any v1.7-alpha scoring.
