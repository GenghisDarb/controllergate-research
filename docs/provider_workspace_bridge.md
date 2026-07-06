# Provider Workspace Bridge

Batch031 records expected and observed provider source commit values before attempting provider-backed harness v9 execution.

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

Batch032 records safe.directory as a provider environment precondition and verifies provider-only normalization without source, test, or HEAD mutation.

Batch033 uses Batch032 provider telemetry to separate safe.directory normalization from target issue reproduction and to define a design-only retargeting path.

Batch034 keeps standard provider context separate from the relative-GIT_DIR issue stimulus and records that distinction in provider command context evidence.

Batch035 applies any repair candidate only inside the provider workspace and preserves the standard provider context versus issue-stimulus distinction.

Batch036 keeps source-only patch application inside the provider workspace and separates target Git indicators from secondary linter preconditions.
