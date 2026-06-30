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

Current status: `undemonstrated_equal_performance`. Batch003 did not verify a challenge candidate, and Batch004 did not verify either a native challenge candidate or an issue-derived feasibility candidate. Batch005 corrected target-node selection and patchable source-subset extraction for the native challenge candidate. Batch006 implements bounded fragment patch assembly, but blocks before patch bytes with passive failure-memory weighting, so no matched-null ensemble runs and no memory separation evidence is added. Issue-derived evidence remains separate and cannot establish native memory separation by itself.

## Current operational gate status

- Matched-null comparison arms: implemented active for the existing `darker_stdin_filename` comparison.
- Matched-null baseline ensemble: partial; it remains gated on a verified challenge candidate and a successful memory-enabled repair.
- Failure-memory weighting: partial; active memory separation requires a real routing delta, not passive marker presence.
- Current evidence counts: confirmed external native repair episodes `3`; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.
