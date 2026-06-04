# ControllerGate v1.7-beta Second Repo Source Assessment

Status: second-repo evidence collection has been strengthened and review-normalized. Eleven TatMapper bundles are normalized as review-required evidence, and renewed eligibility allows a limited exploratory beta pilot. No ControllerGate scoring has been run.

## Source Decision

Preferred source: TatMapper.

Selected repository: `GenghisDarb/tatmapper-app`

Repository URL: `https://github.com/GenghisDarb/tatmapper-app`

Visibility/access note: public unauthenticated GitHub REST calls previously returned `404` for this repository, while the authenticated GitHub connector found `GenghisDarb/tatmapper-app`. A direct scratch `git clone` also succeeded after network approval. Beta evidence still records the access path used for each artifact.

Public fallback inspected: `GenghisDarb/AI-Minesweeper-Discovery-Framework`, but TatMapper is the better second-repo target because it is a different software domain from TORUS and contains Flutter, Android, Gradle, native calibration, release tooling, and app artifact risks.

## Collection Rules

- Eleven v1.7-beta TatMapper episodes have been review-normalized into `controllergate_v1_7_beta/traces/normalized/episodes.jsonl`.
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
| `episode_tatmapper_pr98_export_opencv_helper_repair` | PR #98 | OpenCV CI helper repair and local OpenCV discovery failure | normalized as review-required |
| `episode_tatmapper_pr97_closed_unmerged_gradle_entrypoint_regression` | PR #97 | Closed-unmerged Gradle entrypoint repair with compile-risk review findings | normalized as review-required |
| `episode_tatmapper_pr96_gradle_config_not_run` | PR #96 | Android Gradle configuration repair with testing not run and local Java gap | normalized as review-required |
| `episode_tatmapper_pr94_manual_override_precedence_review` | PR #94 | Calibration guard repair with manual override precedence review caveat | normalized as review-required |
| `episode_tatmapper_pr90_codecov_patch_coverage_warning` | PR #90 | Codecov patch coverage warning-only guardrail evidence | normalized as review-required |

## Evidence Availability

| Evidence type | Availability |
| --- | --- |
| PR metadata | Available for PR #90, #92, #93, #94, #96, #97, and #98 through authenticated GitHub connector. |
| PR diffs | Available for sampled PRs through authenticated GitHub connector; bundle diffs are bounded excerpts. |
| Commit metadata/diffs | Available for selected commits through authenticated GitHub connector; bundle diffs are bounded excerpts. |
| GitHub Actions workflow runs | Connector lookup returned no exposed PR-triggered workflow runs for sampled commits. |
| Commit statuses | Codecov patch success existed for commits `5019f6f`, `a63a5ea`, and PR #90 merge commit; no status rows for several sampled PR merge commits. |
| Full CI logs | UNAVAILABLE: no workflow run logs were exposed by the connector for sampled TatMapper commits in this pass. |
| Local reruns | PARTIAL current-head only: guard calibration passed; OpenCV helper failed because OpenCVConfig.cmake was unavailable; Flutter version/analyze/test timed out; Java was unavailable; Android Gradle wrapper failed because JAVA_HOME/java was unavailable. Logs are in `controllergate_v1_7_beta/evidence_strengthening/tatmapper_current_head/`. |
| Original agent/tool traces | PARTIAL: PR #92/#93 contain ChatGPT Codex task links, but original task transcripts are not present in this repo. |

## Next Gate

The renewed v1.7-beta second-repo eligibility review allows a limited exploratory beta pilot. Run beta scoring only after explicit approval, using only the eleven TatMapper external episodes and preserving every review-required caveat.

Scoring remains NOT RUN until the user explicitly approves the limited beta pilot scoring pass.
