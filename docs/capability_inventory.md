# Capability inventory

Batch031 adds provider source commit predicate correction and harness execution telemetry records after the official Batch030 artifact boundary.

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

Batch032 adds safe-directory precondition classification and provider-only normalization telemetry for the issue-derived harness path.

Batch033 adds issue-derived seed retargeting analysis and v10 design policy while preserving claim boundaries.

Batch034 adds gated v10 issue-stimulus harness execution while preserving native and issue-derived claim boundaries.

Batch035 adds a bounded source-only repair attempt after verified issue-derived pre-repair replay.

Batch036 adds post-repair failure decomposition and a single bounded source-only refinement candidate.

- Batch037 Provider Execution Substage Recovery: implemented for explicit candidate v2 patch/replay substages; no repair success claim is made by candidate generation alone.

- Batch038 Governance Backfill and Patch Serialization Recovery: implemented as a bounded candidate v2 continuation with no full-scoring or memory-lift claim.

## Batch039 secondary cofactor governance

- Batch039 ingests the official Batch038 artifact and preserves the verified target-resolution progress.
- The remaining blocker is classified as a declared but unpinned secondary cofactor, so provider materialization is blocked until a reviewed pinned lock exists.
- Missing secondary tooling is not counted as the original target failure or as repair success.
- Confirmed native repair episodes remain `4`; confirmed issue-derived repair episodes remain `0`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

## Batch040 reviewed cofactor lock gate

- Batch040 ingests the official Batch039 boundary and records a reviewed provider-only lock gate for declared secondary cofactors.
- The first reviewed case is `pylint`, because the selected source declares it but did not pin it.
- Provider materialization, target replay, duplicate replay, and repair counts remain governed by empirical execution gates.
- Confirmed native repair episodes remain `4`; confirmed issue-derived repair episodes remain `0` unless replay and duplicate replay validate under the reviewed lock.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.
- Batch040 status: `PASS_WITH_BATCH040_REVIEWED_LOCK_MATERIALIZATION_BLOCKED`; exact blocker: `provider_batch040_execution_failed`.
