# Clean replication batch 013

Status: BLOCK.

Batch013 implements acquisition/materialization locks, gate-chain binding, tracked seed enforcement, active context filtering records, and frozen routing-score policy before any new candidate can run.

The configured targeted seed is absent, so the lane stops after the locks are ready and before source checkout, native replay, issue-derived fallback, repair-only fallback, or matched-null comparison.

Exact blocker: `targeted_prospective_seed_missing_or_invalid_after_locks_ready`.
