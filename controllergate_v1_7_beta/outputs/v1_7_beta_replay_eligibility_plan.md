# v1.7-beta Replay Eligibility Pathway

Status: Evidence Strengthening Pass 2 complete. This is a missing-evidence ledger, not a scoring expansion.

## Executive Conclusion

0 of 11 TatMapper external real-repo episodes are deterministic-replay-ready.

v1.7-beta remains a limited pilot with review-required caveats:

- Limited pilot status: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`
- Full scoring allowed: false
- ControllerGate full scoring: NOT RUN
- Decision-time/outcome overlap episode count: 0
- Real-repo memory lift: not demonstrated
- Self-maintaining software: not demonstrated

The audit identifies what evidence is missing before deterministic replay scoring could be allowed. It does not convert any episode to pass/fail.

## Replay Eligibility Table

| Episode | Eligible now | Allowed scoring mode | Replay blocker class | Missing fields |
| --- | --- | --- | --- | --- |
| `beta_episode_001` | false | `limited_pilot_review_only` | `multiple_blockers` | base SHA, full changed-file snapshot, full failing job log, failure signature, post-repair command, outcome evidence, PR-head replay, toolchain versions, original agent trace, memory-baseline instrumentation |
| `beta_episode_002` | false | `limited_pilot_review_only` | `multiple_blockers` | base SHA, full changed-file snapshot, full failing job log, failure signature, pre-repair command output, post-repair command, outcome evidence, PR-head replay, toolchain versions, original agent trace, memory-baseline instrumentation |
| `beta_episode_003` | false | `limited_pilot_review_only` | `insufficient_decision_time_evidence` | base SHA, full changed-file snapshot, workflow log, failure signature, exact checkout command, post-repair command, outcome evidence, original agent trace, memory-baseline instrumentation |
| `beta_episode_004` | false | `limited_pilot_review_only` | `no_pr_triggered_workflow_run_found` | base SHA, full changed-file snapshot, full Android/Flutter workflow log, failure signature, exact build command, post-repair command, outcome evidence, toolchain versions, original agent trace, memory-baseline instrumentation |
| `beta_episode_005` | false | `limited_pilot_review_only` | `no_pr_triggered_workflow_run_found` | base SHA, full changed-file snapshot, full Android/Flutter workflow log, failure signature, exact build command, post-repair command, outcome evidence, toolchain versions, original agent trace, memory-baseline instrumentation |
| `beta_episode_006` | false | `limited_pilot_review_only` | `insufficient_decision_time_evidence` | base SHA, full changed-file snapshot, workflow log, failure signature, exact Flutter dependency command, post-repair command, outcome evidence, toolchain versions, original agent trace, memory-baseline instrumentation |
| `beta_episode_007` | false | `limited_pilot_review_only` | `outcome_only_current_head_evidence` | base SHA, full changed-file snapshot, PR workflow log, PR-head failure signature, post-repair command, outcome evidence, PR-head replay, OpenCV toolchain version, original agent trace, memory-baseline instrumentation |
| `beta_episode_008` | false | `limited_pilot_review_only` | `no_pr_triggered_workflow_run_found` | base SHA, full changed-file snapshot, PR workflow log, exact compile failure signature, pre-repair command, post-repair command, outcome evidence, PR-head replay, original agent trace, memory-baseline instrumentation |
| `beta_episode_009` | false | `limited_pilot_review_only` | `outcome_only_current_head_evidence` | base SHA, full changed-file snapshot, PR workflow log, failure signature, pre-repair command, post-repair command, outcome evidence, PR-head replay, Java/Gradle versions, original agent trace, memory-baseline instrumentation |
| `beta_episode_010` | false | `limited_pilot_review_only` | `outcome_only_current_head_evidence` | base SHA, full changed-file snapshot, PR workflow log, failure signature, post-repair command, outcome evidence, PR-head replay, Flutter/Dart versions, original agent trace, memory-baseline instrumentation |
| `beta_episode_011` | false | `limited_pilot_review_only` | `no_pr_triggered_workflow_run_found` | base SHA, full changed-file snapshot, PR workflow log, hard failure signature, pre-repair command, post-repair command, outcome evidence, PR-head replay, original agent trace, memory-baseline instrumentation |

## PR #92 And PR #93 Handling

PR #92 and PR #93 have useful failed CI run/job metadata:

- PR #92 run `17984606083`, failed jobs `test` (`51159403854`) and `android-build` (`51159403859`).
- PR #93 run `17986583215`, failed jobs `test` (`51166385920`) and `android-build` (`51166385937`).

Decoded job logs for those jobs returned GitHub API `410`, so full failing logs remain unavailable. Run/job IDs alone are not deterministic replay proof because they do not provide exact failing commands, step output, failure signatures, or replayable toolchain context.

## Other Nine TatMapper SHAs

The other nine TatMapper source SHAs exposed no PR-triggered workflow runs through the connector during Pass 1/Pass 2 review. Those episodes remain blocked by missing CI logs, missing PR-head replay, toolchain gaps, missing command signatures, or insufficient decision-time evidence.

## Current-Head Evidence Warning

Current-head strengthening SHA: `8f49190a6e9ae29c8c49301a7736e0f838dfd369`

Current-head observations remain outcome-only:

- Flutter version/analyze/test timed out.
- Java was not found.
- Gradle was blocked by missing Java/JAVA_HOME.
- Guard calibration passed.
- OpenCV discovery failed because `OpenCVConfig.cmake` was missing.

None of that current-head evidence is promoted to PR-head replay proof.

## Required Conversion Path

To move an episode from `review_required` to `deterministic_replay_ready`, collect the strict fields needed to rerun the failure and repair without future leakage:

- PR head SHA or commit SHA plus base SHA.
- Full changed-files snapshot or patch.
- Full failing job log or local failing command output.
- Failure signature.
- Pre-repair test/build command.
- Repair patch.
- Post-repair validation command.
- Outcome evidence tied to PR head, merge head, or commit head.
- Toolchain versions.
- Original agent/tool trace when available.
- ControllerGate memory-baseline instrumentation if memory-lift scoring is intended.

## Boundary

The current TatMapper set is not deterministic-replay-ready. v1.7-beta now includes a replay-eligibility pathway, but scoring must not be expanded.
