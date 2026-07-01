# Memory-lift operational definition

Memory lift is a future measurable comparison, not a current result.

Required comparison:

- same candidate,
- same commit,
- same command,
- same environment,
- frozen context hashes,
- memory-enabled arm,
- memory-disabled matched-null arm or deterministic matched-null baseline ensemble,
- no successful patch bytes or failure-memory records visible to the null arm.

A preliminary single-candidate claim requires an accepted matched-null or matched-null ensemble separation score of at least `0.95` with active failure-memory routing. If a memory-disabled arm or null ensemble succeeds equivalently, the score is `0.0` and memory separation evidence remains false. Broader claims require more than one accepted comparison.

Current status: `undemonstrated_equal_performance`. Batch003 did not verify a challenge candidate, and Batch004 did not verify either a native challenge candidate or an issue-derived feasibility candidate. Batch005 corrected target-node selection and patchable source-subset extraction for the native challenge candidate. Batch006 and Batch007 documented the fragment and declared-precondition blockers. Batch008 corrects declared formatter precondition materialization and records a bounded native repair endpoint for `darker_skip_glob_failing_test`. Batch009 runs retrospective patch-quarantined matched-null calibration on that already repaired candidate; the null ensemble fails 5/5, but Arm A still has passive markers, no routing delta, and no generated patch, so the matched-null score remains `0.0`. Batch010 implements active status-code weighting and strict routing-delta auditing, but blocks with `active_memory_routing_delta_not_established`. A prospective memory-lift result still requires a fresh candidate with matched-null rules registered before any successful patch exists. Issue-derived evidence remains separate and cannot establish native memory separation by itself.

## Current operational gate status

- Matched-null comparison arms: implemented active for the existing `darker_stdin_filename` comparison.
- Matched-null baseline ensemble: partial; it remains gated on a verified challenge candidate and a successful memory-enabled repair.
- Status-code weighting and Strict Minimum-Delta Routing: implemented active as Batch010 calibration gates.
- Active Failure-Memory Routing: partial; active memory separation requires a real source, context, or generation routing delta, not passive marker presence.
- Current evidence counts: confirmed external native repair episodes `4` after official Batch008 ingest; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.
