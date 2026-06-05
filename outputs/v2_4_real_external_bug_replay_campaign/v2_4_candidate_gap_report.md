# v2.4 Candidate Gap Report

Result: `blocked_real_external_bug_candidate_acquisition_failure`.

No SWE-bench or BugsInPy candidate promoted to v2.4 execution. This is blocked acquisition evidence, not negative repair-capability evidence.

## SWE-bench Blocker

The SWE-bench repository was acquired, but no bounded concrete Verified/Lite task metadata was locally instantiated and Docker evaluation resources are unavailable in the current environment. SWE-bench gold patches and test patches remain outcome-only and must be excluded from decision-time inputs.

## BugsInPy Blocker

BugsInPy repository metadata was acquired and concrete bug entries were identified for `black:2` and `youtube-dl:1`. Their buggy/fixed revisions and failing commands are known from dataset metadata, but local deterministic replay was not confirmed because the BugsInPy framework requires a Unix-style shell or Docker container, Docker daemon is unavailable, and project-specific old Python runtimes are not available in the bundled environment.

## QuixBugs Boundary

QuixBugs remains preserved as v2.3 algorithmic benchmark evidence only. It is not counted as v2.4 real external bug or organic GitHub issue evidence.

## Next Required Dataset/Source Action

Provide or enable one of:

- a bounded SWE-bench Lite/Verified task workspace with Docker running and exact instance IDs;
- a runnable BugsInPy Docker container or Unix shell environment plus required Python runtimes;
- pre-extracted BugsInPy task worktrees with buggy revision, failing command, and logs captured without fixed-patch leakage.
