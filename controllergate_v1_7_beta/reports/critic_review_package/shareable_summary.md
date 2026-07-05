# ControllerGate shareable summary

Latest boundary: Batch027 `PASS_WITH_BATCH027_HARNESS_V9_EXECUTION_BLOCKED` with blocker `docker_runtime_provider_unavailable`.

## Current operational gate status

- Batch026 official artifact ingestion found the harness v9 state inconsistency: the harness file exists, but generation and verification records are `NOT_RUN`.
- Batch027 reconciles that state and executes harness v9 only under approved provider command contexts.
- Relative `GIT_DIR=.git` is not used as the active command context.
- Batch027 does not run repair, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a verified harness and a real patch candidate.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0` unless issue-derived feasibility validates.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
