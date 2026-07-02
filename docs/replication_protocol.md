# Replication protocol

Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift checks, rollback records, replay, validation, duplicate replay, and claim-boundary review.

Batch015 adds runtime-wrapper scaffolds and lock-sequence registry records without changing the current protocol.

## Current operational gate status

- Current protocol remains `v2.13`.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Batch015 adds a runtime-wrapper scaffold, lock-sequence registry, claim tiers, and product-positioning boundaries without live deployment.
