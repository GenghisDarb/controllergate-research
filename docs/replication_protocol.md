# Replication protocol

Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift checks, rollback records, replay, validation, duplicate replay, and claim-boundary review.

Batch015 adds runtime-wrapper scaffolds and lock-sequence registry records without changing the current protocol.

Batch016 adds target-intent alignment and dependency-era precondition checks before any issue-derived repair.

Batch017 adds decision-time dependency lock policy, lineage indexing, and thin artifact packaging to keep manual artifact custody manageable.

## Current operational gate status

- Current protocol remains `v2.13`.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Batch015 adds a runtime-wrapper scaffold, lock-sequence registry, claim tiers, and product-positioning boundaries without live deployment.
- Batch016 addresses target-intent alignment for the issue-derived Darker seed and safe-stops before repair because the observed failure is pre-target/precondition.
- Batch017 attempts decision-time dependency-era resolution and starts thin artifact packaging; it safe-stops if no decision-time dependency lock can be proven.
