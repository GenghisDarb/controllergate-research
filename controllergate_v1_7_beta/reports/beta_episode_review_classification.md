# ControllerGate v1.7-beta Episode Review Classification

Status: eleven TatMapper pending evidence bundles have been reviewed and normalized as second-repo external evidence. ControllerGate scoring was not run.

## Summary

| Field | Value |
| --- | --- |
| Pending TatMapper bundles present | 11 |
| Pending TatMapper bundles reviewed and normalized | 11 |
| Newly pending unnormalized bundles | 0 |
| Normalized beta episodes | 11 |
| External real repo episodes | 11 |
| Pending incomplete after review | 0 |
| Scoring eligibility count | 0 |
| Beta scoring allowed | false |
| Scoring mode | blocked_pending_renewed_eligibility_review |
| ControllerGate scoring | NOT RUN |

All normalized beta episodes are classified as `external_real_repo_episode` with `scoring_allowed_for_v1_7_beta_second_repo_claim: review_required`.

## Episode Classifications

| Episode | Source | Outcome type | Verified result | Classification note |
| --- | --- | --- | --- | --- |
| `beta_episode_001` | TatMapper PR #93 | `flutter_availability_failure_or_environment_gap` | `review_required` | Real PR/diff/review evidence exists, but full CI logs and local Flutter rerun are unavailable. |
| `beta_episode_002` | TatMapper PR #92 | `ndk_tooling_review` | `review_required` | Real PR/diff/review evidence exists, but command output and workflow logs are unavailable. |
| `beta_episode_003` | TatMapper commit `7eb2e48` | `windows_checkout_breakage` | `review_required` | Commit/diff evidence shows an invalid Windows filename repair, but no reproduction or CI log is available. |
| `beta_episode_004` | TatMapper commit `5019f6f` | `android_scaffold_ndk_cmake_setup` | `review_required` | Android scaffold and NDK/CMake setup evidence exists; Codecov patch status is not a full build verification. |
| `beta_episode_005` | TatMapper commit `a63a5ea` | `sdk_v2_embedding_alignment` | `review_required` | Android v2 embedding and SDK alignment evidence exists; full Flutter/Android build verification is unavailable. |
| `beta_episode_006` | TatMapper commit `d9a6bbe` | `pubspec_conflict_marker_risk` | `review_required` | Bounded diff shows generated lockfile conflict-marker risk, but local Flutter tooling failure was not rerun. |
| `beta_episode_007` | TatMapper PR #98 | `export_opencv_helper_repair` | `review_required` | CI helper repair evidence exists, but current-head OpenCV rerun is outcome-only and full CI logs are unavailable. |
| `beta_episode_008` | TatMapper PR #97 | `closed_unmerged_gradle_entrypoint_regression` | `review_required` | Closed-unmerged PR with review-identified compile risks; PR-head rerun and full CI logs are unavailable. |
| `beta_episode_009` | TatMapper PR #96 | `gradle_config_not_run` | `review_required` | Gradle config repair evidence exists, but PR body says testing was not run and local Gradle verification is blocked by missing Java. |
| `beta_episode_010` | TatMapper PR #94 | `manual_override_precedence_review` | `review_required` | Calibration guard evidence exists alongside a manual override review caveat and local Flutter timeouts. |
| `beta_episode_011` | TatMapper PR #90 | `codecov_patch_coverage_warning` | `review_required` | Codecov patch coverage warning evidence exists, but full workflow logs and PR-head rerun are unavailable. |

## Protected Interpretation

v1.7-beta has normalized an eleven-episode second-repo evidence cluster. The normalized episodes remain review-only. This supports multi-repo evidence readiness, not a memory-lift claim and not a self-maintaining software claim.

## Newly Normalized TatMapper Bundles

These bundles were collected after the first eligibility review and are now normalized as review-required:

- `episode_tatmapper_pr98_export_opencv_helper_repair`
- `episode_tatmapper_pr97_closed_unmerged_gradle_entrypoint_regression`
- `episode_tatmapper_pr96_gradle_config_not_run`
- `episode_tatmapper_pr94_manual_override_precedence_review`
- `episode_tatmapper_pr90_codecov_patch_coverage_warning`

## Next Gate

Run a renewed v1.7-beta second-repo eligibility review. Scoring remains blocked until that later review explicitly allows a limited pilot.
