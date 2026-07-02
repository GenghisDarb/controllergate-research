# Artifact packaging policy

Batch017 begins thin artifact packaging for the primary workflow artifact.

The primary artifact includes the current batch outputs, latest ingest verification records, an artifact lineage index, and an evidence carry-forward manifest. Prior batch evidence remains valid through artifact SHA256 values, ingest commits, manifest hashes, and claim-boundary summaries.

The primary artifact must not recursively include all prior `clean_replication_batch_*` directories. A full lineage artifact may be produced separately only when explicitly configured.

Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

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
