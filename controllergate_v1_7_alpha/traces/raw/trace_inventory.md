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

Artifact intake folders have been created under `controllergate_v1_7_alpha/artifacts_intake/`, but the expected iota and pi package ZIPs and notebooks are not present in the repo.

No pending episode is complete yet, and no episode has been normalized into `traces/normalized/episodes.jsonl`.

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

## Current Artifact Intake Blocker

The first two correction episodes cannot be completed until these files are supplied:

```text
controllergate_v1_7_alpha/artifacts_intake/iota/ControllerGate_v1_6_iota_PrecisionGatedBudgetMemoryTrial_Package.zip
controllergate_v1_7_alpha/artifacts_intake/iota/ControllerGate_v1_6_iota_PrecisionGatedBudgetMemoryTrial.ipynb
controllergate_v1_7_alpha/artifacts_intake/pi/ControllerGate_v1_6_pi_AdaptiveAdversaryCounterQuarantineTrial_Package.zip
controllergate_v1_7_alpha/artifacts_intake/pi/ControllerGate_v1_6_pi_AdaptiveAdversaryCounterQuarantineTrial.ipynb
```

Until those artifacts are present, no packaged `decision_report.json`, rerun analyzer output, or SHA verification can be extracted for iota or pi.
