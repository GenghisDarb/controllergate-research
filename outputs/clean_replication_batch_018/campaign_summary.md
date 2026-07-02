# Clean replication Batch018 manual dependency lock intake

Status: PASS_WITH_BATCH018_SAFE_STOP.

Batch018 preserves Batch017 thin-artifact lineage, reconciles the Darker issue #112 timestamp conflict, and checks for the canonical manual dependency lock JSON.

The canonical manual dependency lock is absent, so decision-time dependency lock validation, environment materialization, target-intent retry, harness v4, repair-only fallback, and matched-null diagnostics remain not run.

Dependency cutoff timestamp: `2021-01-02T00:00:00Z`.

Exact blocker: `manual_dependency_lock_absent`.
