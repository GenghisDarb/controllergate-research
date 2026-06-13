# v2.8l BugsInPy Third Scoreable Episode Recovery

Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.

- Executed BugsInPy episodes: 3.
- Scoreable episodes: 2.
- Positive memory-only episodes: 0.
- Targeted recovery candidate: `black:8`.
- v2.8k blocker: source-only safety budget rejected candidate at 16 changed lines.
- v2.8l strategy: compact source-only comment/comma relocation guard.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated unless aggregate criteria are met.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_002 | black:8 | failed_both | false | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |

No fixed/gold patches, future outcome logs, fixed-state diagnostic hints, or test edits are used at decision time. Blocked episodes are not counted as scoreable.
