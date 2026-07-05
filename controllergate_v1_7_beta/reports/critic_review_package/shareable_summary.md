# ControllerGate shareable summary

Latest boundary: Batch031 `PASS_WITH_BATCH031_HARNESS_V9_EXECUTION_BLOCKED` with blocker `issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context`.

## Current operational gate status

- Batch031 ingests the official Batch030 artifact boundary and records the provider source commit predicate correction.
- Batch031 records expected and observed provider source commit values before harness execution.
- Batch031 does not use relative `GIT_DIR=.git` as an active command context.
- Batch031 does not run repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a verified harness and a real patch candidate.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0` unless issue-derived repair validates in a later gated phase.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Batch032 preserves four native repair episodes and zero issue-derived repair episodes while classifying safe.directory telemetry separately from target reproduction.

Batch033 keeps four native repair episodes and zero issue-derived repair episodes; it defines only a decision-time-safe retargeting design path for Darker issue #112.

Batch034 keeps four native repair episodes and zero issue-derived repair episodes; v10 execution evidence is pre-repair only.
