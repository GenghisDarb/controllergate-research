# Memory lift definition

Memory lift requires a preregistered memory-enabled arm and memory-disabled null arm on the same fresh candidate, commit, command, environment, replay rules, and frozen context hashes. The null arm cannot read successful patch bytes or failure-memory ledgers.

Batch015 does not add new memory evidence. Memory lift remains `not_demonstrated`.

Batch016 also does not add memory evidence because target-intent alignment remains blocked.

Batch017 also does not add memory evidence because dependency-era resolution does not reach target-intent alignment.

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
