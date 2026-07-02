# Current status

ControllerGate is currently an evidence-bound repair validation kernel and runtime-wrapper scaffold. The current protocol remains `v2.13`.

Batch014 remains blocked at `issue_derived_harness_intent_mismatch`; Batch015 preserves that validation path and adds scaffolded runtime controls, lock-sequence records, and claim tiers.

Batch016 records that the issue-derived harness failure is a target-intent mismatch caused by a pre-target/precondition failure. Repair remains blocked.

Batch017 attempts decision-time dependency-era resolution, records the missing dependency lock as a safe-stop, and switches the primary workflow artifact to thin/delta packaging.

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
