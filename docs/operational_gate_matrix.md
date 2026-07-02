# Operational gate matrix

Batch015 records runtime-wrapper gates and lock-sequence operations in `configs/operational_gate_matrix.json` and `configs/lock_sequence_operation_registry.json`.

Batch016 records target-intent signature alignment, dependency-era chaperone, variant matrix, and safe-stop gates.

Batch017 records dependency-era resolution policy, decision-time dependency lock status, artifact lineage indexing, evidence carry-forward, and thin artifact packaging gates.

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
