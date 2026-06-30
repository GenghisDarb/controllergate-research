# Clean replication batch 006 bounded fragment patch assembly

Status: `BLOCKED`.

Batch006 implements bounded fragment patch assembly, coupled dependency interlock mapping, dual projection consistency checking, passive failure-memory weighting records, and a proof-chain lock for the verified native `darker_skip_glob_failing_test` candidate.

The run does not generate patch bytes. The observed replay reaches formatter loading and declared dependency or entry-point preconditions before the import-sorting skip behavior is reached, so the source-facing projection does not authorize a source-only repair fragment.

Exact blocker: `fragment_patch_plan_not_generated`.
Full scoring remains `NOT_RUN/disallowed`; memory lift remains undemonstrated; self-maintaining software is not demonstrated.
