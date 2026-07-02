# Clean replication Batch017 dependency-era resolution and thin artifact packaging

Status: PASS_WITH_BATCH017_SAFE_STOP.

Batch017 officially preserves Batch016, introduces thin artifact packaging and lineage carry-forward, and attempts decision-time dependency-era resolution for Darker issue #112.

No decision-time dependency lock could be proven from committed evidence, so target-intent retry, harness v3, repair-only fallback, and matched-null diagnostics remain blocked.

Exact blocker: `dependency_era_lock_unavailable`.
