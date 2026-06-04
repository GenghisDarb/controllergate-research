# TatMapper Deterministic Replay Readiness Audit

Status: v1.7-beta Evidence Strengthening Pass 1 completed. Do not expand scoring.

ControllerGate v1.7-beta limited TatMapper scoring remains `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`. Full scoring remains disallowed, ControllerGate full scoring remains NOT RUN, and `decision_time_outcome_overlap_episode_count` remains 0.

## Summary

| Field | Value |
| --- | --- |
| TatMapper normalized episodes reviewed | 11 |
| Deterministic replay ready | 0 |
| Full scoring allowed | false |
| ControllerGate full scoring | NOT RUN |
| Memory-baseline instrumentation | unavailable |
| Decision-time/outcome overlap episodes | 0 |

## Classification Counts

| Classification | Count |
| --- | --- |
| `deterministic_replay_ready` | 0 |
| `blocked_missing_ci_log` | 5 |
| `blocked_pr_head_unavailable` | 1 |
| `blocked_toolchain_gap` | 2 |
| `blocked_timeout` | 1 |
| `blocked_missing_agent_trace` | 0 |
| `review_required_insufficient_evidence` | 2 |

No episode is converted to pass/fail. The audit improves evidence visibility, especially for PR #92 and PR #93, but it does not make any TatMapper episode scoring-clean.

## GitHub Actions Lookup

The GitHub Actions connector was queried for the 11 TatMapper source SHAs.

| Episode | Reference | Workflow result |
| --- | --- | --- |
| `beta_episode_001` | PR #93 / `36189ae` | Flutter CI run `17986583215` found, conclusion failure. Jobs `test` (`51166385920`) and `android-build` (`51166385937`) failed. Decoded job logs returned GitHub API `410`, so full logs remain unavailable. |
| `beta_episode_002` | PR #92 / `41c483f` | Flutter CI run `17984606083` found, conclusion failure. Jobs `test` (`51159403854`) and `android-build` (`51159403859`) failed. Decoded job logs returned GitHub API `410`, so full logs remain unavailable. |
| `beta_episode_003` | commit `7eb2e48` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_004` | commit `5019f6f` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_005` | commit `a63a5ea` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_006` | commit `d9a6bbe` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_007` | PR #98 / `bc2fff0` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_008` | PR #97 / `7e401a0` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_009` | PR #96 / `9753a1d` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_010` | PR #94 / `e64ecfc` | No PR-triggered workflow run exposed through connector. |
| `beta_episode_011` | PR #90 / `ccc9a44` | No PR-triggered workflow run exposed through connector; Codecov status/comment only. |

## Current-Head Toolchain Context

Earlier local strengthening logs were current-head-only, not PR-head proof.

Current-head SHA: `8f49190a6e9ae29c8c49301a7736e0f838dfd369`

| Tool or command | Result |
| --- | --- |
| `flutter --no-version-check --version` | timed out after 120000 ms |
| Dart version | unavailable because Flutter version timed out |
| `where.exe java` | exit code 1, Java not found |
| `app/android/gradlew.bat --version` | exit code 9009, `JAVA_HOME` not set and no `java` in PATH |
| Android SDK/NDK versions | unavailable in this pass |
| `./scripts/guard_calibration.sh` | passed, exit code 0 |
| `./scripts/export_opencv_dir.sh` | failed, `OpenCVConfig.cmake` not found in known paths |
| `flutter --no-version-check analyze --no-pub` | timed out after 120000 ms |
| `flutter --no-version-check test --no-pub --concurrency=1` | timed out after 120000 ms |

## Episode Readiness Table

| Episode | Reference | Head status | Primary classification | Why not deterministic replay-ready |
| --- | --- | --- | --- | --- |
| `beta_episode_001` | PR #93 / `36189ae` | PR-head CI metadata available; no local PR-head rerun | `blocked_missing_ci_log` | Failed Flutter CI run and jobs are visible, but decoded logs return `410`; local replay is blocked by Flutter timeout and Java gap. |
| `beta_episode_002` | PR #92 / `41c483f` | PR-head CI metadata available; no local PR-head rerun | `blocked_missing_ci_log` | Failed Flutter CI run and jobs are visible, but decoded logs return `410`; PR body command output is unavailable. |
| `beta_episode_003` | commit `7eb2e48` | commit metadata only | `review_required_insufficient_evidence` | No workflow run, no exact failing checkout command, no Windows checkout reproduction, and no original agent trace. |
| `beta_episode_004` | commit `5019f6f` | commit metadata only | `blocked_missing_ci_log` | Codecov status exists, but no full Android/Flutter workflow log or exact build command is available. |
| `beta_episode_005` | commit `a63a5ea` | commit metadata only | `blocked_missing_ci_log` | Codecov status exists, but no full Android/Flutter workflow log or exact build command is available. |
| `beta_episode_006` | commit `d9a6bbe` | commit metadata only | `review_required_insufficient_evidence` | Generated-artifact risk is visible, but no deterministic Flutter tooling reproduction or exact failing command is available. |
| `beta_episode_007` | PR #98 / `bc2fff0` | current-head-only local rerun | `blocked_toolchain_gap` | OpenCV helper failed only at current head because `OpenCVConfig.cmake` is missing; this is not PR-head proof. |
| `beta_episode_008` | PR #97 / `7e401a0` | PR-head not rerun | `blocked_pr_head_unavailable` | Closed-unmerged compile-risk review evidence is real, but no PR-head CI or local rerun is available. |
| `beta_episode_009` | PR #96 / `9753a1d` | current-head-only Gradle check | `blocked_toolchain_gap` | PR body says testing was not run; current-head Gradle check is blocked by missing Java/JAVA_HOME. |
| `beta_episode_010` | PR #94 / `e64ecfc` | current-head-only guard and Flutter attempts | `blocked_timeout` | Guard passed at current head, but Flutter analyze/test timed out and the manual override review caveat was not replayed. |
| `beta_episode_011` | PR #90 / `ccc9a44` | PR-head not rerun | `blocked_missing_ci_log` | Codecov warning evidence exists, but full build/test logs and PR-head replay are unavailable. |

## Strategic Read

This pass improves the evidence map but does not change the pilot interpretation. The best new evidence is that PR #92 and PR #93 have failed Flutter CI run/job metadata; however, the full logs are expired or unavailable through the decoded log endpoint. The rest of the cluster still lacks PR-head deterministic replay.

The correct state remains:

- Limited pilot result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`
- Deterministic replay-ready episodes: 0
- Real-repo memory lift: not demonstrated
- Self-maintaining software: not demonstrated
- Full scoring: blocked

## Next Actions

1. Recover full GitHub Actions logs for runs `17986583215` and `17984606083` if possible outside the expired GitHub log endpoint.
2. Check out PR-head or merge-head SHAs in ignored scratch space and rerun exact commands.
3. Make toolchain versions explicit: Flutter, Dart, Java, Gradle, Android SDK/NDK, and OpenCV.
4. Install or expose Java/JAVA_HOME before Android/Gradle replay.
5. Install or point `OpenCV_DIR` to a valid `OpenCVConfig.cmake` before replaying PR #98.
6. Recover original agent/tool transcripts for PR-linked episodes where possible.
7. Add ControllerGate memory-baseline instrumentation before any real-repo memory-lift scoring.
