# ControllerGate v1.7-beta Second Repo Source Assessment

Status: second-repo evidence collection started and the initial TatMapper bundle set has been review-normalized. No ControllerGate scoring has been run.

## Source Decision

Preferred source: TatMapper.

Selected repository: `GenghisDarb/tatmapper-app`

Repository URL: `https://github.com/GenghisDarb/tatmapper-app`

Visibility/access note: public unauthenticated GitHub REST calls returned `404` for this repository, while the authenticated GitHub connector found `GenghisDarb/tatmapper-app` with private visibility and repository access. This means beta evidence depends on authenticated connector access, not public web availability.

Public fallback inspected: `GenghisDarb/AI-Minesweeper-Discovery-Framework`, but TatMapper is the better second-repo target because it is a different software domain from TORUS and contains Flutter, Android, Gradle, native calibration, release tooling, and app artifact risks.

## Collection Rules

- Six v1.7-beta TatMapper episodes have been review-normalized into `controllergate_v1_7_beta/traces/normalized/episodes.jsonl`.
- All normalized beta episodes remain `review_required`.
- No ControllerGate scoring was run.
- Missing logs, commands, diffs, or outcomes are marked `UNAVAILABLE` with reason.
- Decision-time evidence is kept separate from outcome-only evidence inside each pending bundle.
- `external_repos/` remains ignored for scratch clones.

## Candidate Episodes Collected

| Pending bundle | Evidence source | Theme | Current status |
| --- | --- | --- | --- |
| `episode_tatmapper_pr93_calibration_guard_flutter_unavailable` | PR #93 | Flutter unavailable testing failure plus calibration/export guard repair | normalized as review-required |
| `episode_tatmapper_pr92_ndk_path_tooling_review` | PR #92 | NDK path/tooling config drift and printing plugin bridge review | normalized as review-required |
| `episode_tatmapper_commit_7eb_invalid_windows_checkout_file` | commit `7eb2e48` | Invalid filename repair for Windows checkout breakage | normalized as review-required |
| `episode_tatmapper_commit_5019_android_scaffold_ndk_cmake` | commit `5019f6f` | Android scaffold, Gradle, NDK/CMake CI setup repair | normalized as review-required |
| `episode_tatmapper_commit_a63_android_v2_embedding_sdk_alignment` | commit `a63a5ea` | Android v2 embedding and SDK alignment repair | normalized as review-required |
| `episode_tatmapper_commit_d9a_pubspec_conflict_import_path` | commit `d9a6bbe` | Package import path repair with pubspec.lock conflict-marker risk | normalized as review-required |

## Evidence Availability

| Evidence type | Availability |
| --- | --- |
| PR metadata | Available for PR #92 and PR #93 through authenticated GitHub connector. |
| PR diffs | Available for PR #92 and PR #93 through authenticated GitHub connector; bundle diffs are bounded excerpts. |
| Commit metadata/diffs | Available for selected commits through authenticated GitHub connector; bundle diffs are bounded excerpts. |
| GitHub Actions workflow runs | Connector lookup returned no PR-triggered workflow runs for sampled commits. |
| Commit statuses | Codecov patch success existed for commits `5019f6f` and `a63a5ea`; no status rows for PR #92/#93 merge commits or commit `7eb2e48`. |
| Full CI logs | UNAVAILABLE: no workflow run logs were exposed by the connector for sampled TatMapper commits in this pass. |
| Local reruns | NOT_RUN: no TatMapper scratch clone or Flutter/Android local rerun was performed in this pass. |
| Original agent/tool traces | PARTIAL: PR #92/#93 contain ChatGPT Codex task links, but original task transcripts are not present in this repo. |

## Next Gate

Run a v1.7-beta second-repo eligibility review before any beta scoring. The review should decide whether the normalized TatMapper candidates are strong enough for a limited second-repo pilot, or whether fresh local Flutter/Android reruns and stronger CI evidence are required first.

Scoring must remain NOT RUN until a separate beta eligibility review approves it.
