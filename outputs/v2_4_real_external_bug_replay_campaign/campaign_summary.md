# v2.4 SWE-bench/BugsInPy Real External Bug Replay Campaign

SWE-bench-style tasks are real GitHub issue tasks when reproduced safely. BugsInPy-style entries are real Python bug benchmark entries.

## Result

`blocked_real_external_bug_candidate_acquisition_failure`

## Counts

- Promoted candidates: 0.
- Executed episodes: 0.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Inconclusive/negative episodes: 0.
- Decision-time/outcome overlap: 0.
- Corruption in positive memory episodes: 0.

## What Happened

The campaign acquired real-bug source families but did not promote any candidate to execution.

- SWE-bench Verified/Lite source was acquired as a source family, but local task execution is Docker/resource dependent and no bounded concrete task was locally instantiated.
- BugsInPy source was acquired and concrete bug metadata was identified for `black:2` and `youtube-dl:1`, but local deterministic replay was blocked by missing Unix-shell/container/runtime support.
- QuixBugs remains preserved as v2.3 algorithmic benchmark evidence only.

Gold/corrected patches are outcome-only and excluded from decision-time inputs. Benchmark evidence must be labeled as benchmark evidence. QuixBugs-only evidence is not counted as real external bug evidence. Fallback controlled fixtures are not counted as real external bug evidence.

## Claim Boundary

This is blocked acquisition evidence, not negative capability evidence. Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.

## Next Required Dataset/Source Action

Enable a bounded replay environment before v2.4 execution: Docker or equivalent container execution for SWE-bench/BugsInPy, exact SWE-bench instance IDs or BugsInPy bug worktrees, project-specific runtimes, and failing logs captured without gold/fixed patch leakage.
