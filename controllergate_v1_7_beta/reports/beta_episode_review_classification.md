# ControllerGate v1.7-beta Episode Review Classification

Status: six TatMapper pending evidence bundles were reviewed and normalized as second-repo external evidence. A later strengthening pass added five additional pending TatMapper bundles, but they are not normalized. ControllerGate scoring was not run.

## Summary

| Field | Value |
| --- | --- |
| Pending TatMapper bundles present | 11 |
| Pending TatMapper bundles reviewed and normalized | 6 |
| Newly pending unnormalized bundles | 5 |
| Normalized beta episodes | 6 |
| External real repo episodes | 6 |
| Pending incomplete after review | 0 |
| Scoring eligibility count | 0 |
| Beta scoring allowed | false |
| Scoring mode | blocked_insufficient_second_repo_evidence |
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

## Protected Interpretation

v1.7-beta has normalized a second-repo evidence cluster and now has additional pending TatMapper candidates. The normalized episodes remain review-only. This supports multi-repo evidence readiness, not a memory-lift claim and not a self-maintaining software claim.

## Newly Pending TatMapper Bundles

These bundles were collected after the eligibility review and are not normalized:

- `episode_tatmapper_pr98_export_opencv_helper_repair`
- `episode_tatmapper_pr97_closed_unmerged_gradle_entrypoint_regression`
- `episode_tatmapper_pr96_gradle_config_not_run`
- `episode_tatmapper_pr94_manual_override_precedence_review`
- `episode_tatmapper_pr90_codecov_patch_coverage_warning`

## Next Gate

Review-normalize the newly pending TatMapper bundles only if the evidence is strong enough, then rerun the v1.7-beta second-repo eligibility review. Scoring remains blocked until that later review explicitly allows a limited pilot.
