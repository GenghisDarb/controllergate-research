# v2.8k BugsInPy Third Scoreable Episode Recovery

Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.

- Executed BugsInPy episodes: 3.
- Scoreable episodes: 2.
- Positive memory-only episodes: 0.
- Targeted recovery candidate: `black:8`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated unless aggregate criteria are met.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_002 | black:8 | blocked_no_safe_patch_candidate_generated | false | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |

v2.8k reuses the same BugsInPy target-matched pool and anti-leakage rules. It attempts to recover the missing third scoreable episode with a source-only Black comma relocation guard. Fixed/gold patches, future outcome evidence, fixed-state hints, and test edits are forbidden.
