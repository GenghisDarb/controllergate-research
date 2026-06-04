# v1.7-beta Limited TatMapper Pilot Critic Review

ControllerGate v1.7-beta limited TatMapper scoring was run on 11 normalized TatMapper external real repo episodes. This is tiny second-repo exploratory evidence only, not proof of self-maintaining software.

## Accepted Result

Result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`

This is a real limited second-repo pilot result with caveats. It is not a clean performance win, not full scoring, and not a memory-lift demonstration.

## What Passed

- Scope gate passed: only v1.7-beta TatMapper `external_real_repo_episode` entries were used.
- Exclusion gate passed: v1.7-alpha TORUS episodes, v1.6 controlled benchmark evidence, and correction-review episodes were excluded.
- Limited-mode gate passed: scoring mode remained `limited_pilot_only`.
- Full scoring gate passed: full scoring remained disallowed.
- Caveat-preservation gate passed: all weak, ambiguous, warning-only, closed-unmerged, unavailable-CI, and `review_required` episodes remained visible.
- Future-leakage guard passed with caveats: `decision_time_outcome_overlap_episode_count: 0`.
- Non-claim boundary passed: no self-maintaining software, production-readiness, cross-repo generalization, or memory-lift claim is allowed.

## Counts

| Metric | Count |
| --- | --- |
| Eligible beta external episodes | 11 |
| Passed | 0 |
| Failed | 0 |
| Warning only | 0 |
| Review required | 11 |
| Deterministic pass/fail | 0 |
| Decision-time/outcome overlap episodes | 0 |
| Dependency/config drift detected | 9 |
| Generated artifact mismatch detected | 2 |
| Stale-read or false-completion review required | 4 |

## Caveats That Remain

- All 11 TatMapper episodes remain `review_required`.
- No deterministic pass/fail episode-level performance result was produced.
- Full GitHub Actions logs are unavailable for the selected PRs and commits.
- Fresh local reruns are current-head-only, timed out, unavailable, or blocked by Java, Flutter, OpenCV, or tooling gaps.
- Original agent/tool transcripts are unavailable for the TatMapper episodes.
- No ControllerGate discovered-memory, no-memory, predefined-memory, or poisoned-memory baselines are available for TatMapper evidence.
- The run supports guarded evidence-pipeline scoring readiness, not real-repo memory lift.

## Episode Drivers

| Episode | Reference | Outcome type | Critic read |
| --- | --- | --- | --- |
| `beta_episode_001` | PR #93 | `flutter_availability_failure_or_environment_gap` | Environment-gap evidence; review-required because Flutter rerun and full CI logs are unavailable. |
| `beta_episode_002` | PR #92 | `ndk_tooling_review` | Configuration-review evidence; review-required because command output and workflow logs are unavailable. |
| `beta_episode_003` | commit `7eb2e48` | `windows_checkout_breakage` | Strong maintenance candidate; review-required because no checkout reproduction or CI log is available. |
| `beta_episode_004` | commit `5019f6f` | `android_scaffold_ndk_cmake_setup` | Android scaffold signal; review-required because Codecov status is not full app build evidence. |
| `beta_episode_005` | commit `a63a5ea` | `sdk_v2_embedding_alignment` | Second-repo domain signal; review-required because full Flutter or Android build evidence is unavailable. |
| `beta_episode_006` | commit `d9a6bbe` | `pubspec_conflict_marker_risk` | Generated-artifact risk signal; review-required because deterministic Flutter tooling reproduction is unavailable. |
| `beta_episode_007` | PR #98 | `export_opencv_helper_repair` | Repair-style evidence; review-required because current-head OpenCV failure is outcome-only, not PR-head proof. |
| `beta_episode_008` | PR #97 | `closed_unmerged_gradle_entrypoint_regression` | Closed-unmerged compile-risk evidence; review-required but future-leakage overlap is corrected to zero. |
| `beta_episode_009` | PR #96 | `gradle_config_not_run` | Merged repair with verification gap; review-required because testing was not run and Java blocks local Gradle verification. |
| `beta_episode_010` | PR #94 | `manual_override_precedence_review` | Guard evidence with manual override caveat; review-required because Flutter reruns timed out. |
| `beta_episode_011` | PR #90 | `codecov_patch_coverage_warning` | Warning-only guardrail evidence; review-required because full build/test logs and PR-head rerun are unavailable. |

## Gate Fairness

The eligibility rules were fair for a tiny exploratory second-repo pilot: there were 11 external TatMapper episodes, useful diversity, explicit exclusion of non-beta evidence, and preserved decision/outcome separation.

Those same rules are too weak for full scoring. All episodes remain `review_required`, deterministic pass/fail evidence is absent, and memory baselines are unavailable.

## Not Accepted As

- Proof of self-maintaining software.
- Full v1.7-beta scoring.
- Production readiness.
- Broad cross-repo generalization.
- Real-repo memory-lift demonstration.

## Recommendation

Do not expand scoring yet. Strengthen TatMapper evidence with full CI logs, PR-head reruns, deterministic Flutter or Android build checks, original agent traces, and memory-baseline instrumentation before any full-scoring or memory-lift claim.
