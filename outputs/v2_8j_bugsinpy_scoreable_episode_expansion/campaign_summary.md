# v2.8j BugsInPy Scoreable Episode Expansion

Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.

- Executed BugsInPy episodes: 3.
- Scoreable episodes: 2.
- Positive memory-only episodes: 0.
- Inconclusive equal-performance episodes: 2.
- Blocked episodes: 1.
- Full scoring: NOT_RUN / disallowed.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_002 | black:8 | failed_both | false | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |

No fixed/gold patches, future outcome logs, or fixed-state diagnostic hints were used at decision time. Source repair candidate patches are separated from replay/materialization artifacts.
