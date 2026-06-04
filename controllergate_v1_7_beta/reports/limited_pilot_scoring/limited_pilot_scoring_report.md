# v1.7-beta Limited TatMapper Scoring

ControllerGate v1.7-beta limited TatMapper scoring was run on 11 normalized TatMapper external real repo episodes. This is tiny second-repo exploratory evidence only, not proof of self-maintaining software.

## Scope

Scoring mode: `limited_pilot_only`

Full scoring allowed: `false`

Only v1.7-beta TatMapper `external_real_repo_episode` entries were included. v1.7-alpha TORUS episodes, v1.6 controlled benchmark evidence, and correction-review episodes were excluded from beta scoring.

## Counts

| Metric | Count |
| --- | --- |
| eligible beta external episodes | 11 |
| passed | 0 |
| failed | 0 |
| warning_only | 0 |
| review_required | 11 |
| deterministic pass/fail | 0 |
| warning or review_required | 11 |

## Episode-Level Decision Table

| Episode | Reference | Outcome type | Verified result | CI logs | Fresh rerun | Dependency/config drift |
| --- | --- | --- | --- | --- | --- | --- |
| beta_episode_001 | PR #93 | flutter_availability_failure_or_environment_gap | review_required | false | false | true |
| beta_episode_002 | PR #92 | ndk_tooling_review | review_required | false | false | true |
| beta_episode_003 | 7eb2e48 | windows_checkout_breakage | review_required | false | false | false |
| beta_episode_004 | 5019f6f | android_scaffold_ndk_cmake_setup | review_required | partial_status_only | false | true |
| beta_episode_005 | a63a5ea | sdk_v2_embedding_alignment | review_required | partial_status_only | false | true |
| beta_episode_006 | d9a6bbe | pubspec_conflict_marker_risk | review_required | false | false | true |
| beta_episode_007 | PR #98 | export_opencv_helper_repair | review_required | false | false | true |
| beta_episode_008 | PR #97 | closed_unmerged_gradle_entrypoint_regression | review_required | false | false | true |
| beta_episode_009 | PR #96 | gradle_config_not_run | review_required | false | false | true |
| beta_episode_010 | PR #94 | manual_override_precedence_review | review_required | false | false | true |
| beta_episode_011 | PR #90 | codecov_patch_coverage_warning | review_required | partial_status_only | false | false |

## Memory Baselines

| Baseline | Result | Reason |
| --- | --- | --- |
| discovered-memory result | UNAVAILABLE | The TatMapper external evidence does not contain ControllerGate discovered-memory condition outputs. |
| no-memory baseline | UNAVAILABLE | No no-memory baseline was available in the normalized TatMapper external evidence. |
| predefined-memory baseline | UNAVAILABLE | No predefined-memory baseline was available in the normalized TatMapper external evidence. |
| poisoned-memory baseline | UNAVAILABLE | No poisoned-memory baseline was available in the normalized TatMapper external evidence. |

## Detection Results

| Detection area | Result |
| --- | --- |
| false-success detection | No explicit false-success TatMapper episode was present; all beta episodes remain review_required. |
| stale-read or false-completion detection | true=0, false=7, review_required=4, null=0 |
| dependency/config drift detection | true=9, false=2, review_required=0, null=0 |
| generated artifact mismatch detection | true=2, false=9, review_required=0, null=0 |
| future leakage check | decision-time/outcome-only overlap episodes=0; review-required caveats preserved |

## Limitations

- All eleven TatMapper episodes remain `review_required`.
- Full GitHub Actions logs are unavailable for the selected PRs/commits.
- Fresh local reruns are current-head-only, timed out, unavailable, or blocked by local Java/Flutter/OpenCV/tooling gaps.
- Original agent/tool transcripts are unavailable for the TatMapper episodes.
- No ControllerGate memory-condition baselines are available for the TatMapper external evidence.
- Warning-only, closed-unmerged, weak, ambiguous, and unavailable-CI evidence remains included.

## Non-Claims

- This is not proof of self-maintaining software.
- This is not full v1.7-beta scoring.
- This is not broad production readiness.
- This is not broad cross-repo generalization.
- This does not demonstrate real-repo memory lift.

## Result

Overall limited pilot result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`
