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

Current status: `undemonstrated_equal_performance`. Batch003 did not verify a challenge candidate, and batch004 has not verified either a native challenge candidate or an issue-derived feasibility candidate, so no new matched-null ensemble comparison has been authorized.
