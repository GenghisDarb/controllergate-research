# v2.8t Positive Memory Replication Lane

Aggregate result: `replicated_positive_memory_signal`.

- Preserved v2.8s baseline gate: PASS.
- ansible:2 positive-memory baseline preserved: True.
- Harness sanity: PASS.
- Memory arm separation: PASS.
- Memory evidence eligibility: PASS.
- Memory replication integrity: PASS.
- Candidates preflighted: 28 / available 28.
- Memory-replication candidates attempted: 1.
- Executed BugsInPy episodes: 5.
- Scoreable episodes: 5.
- Positive memory-only episodes: 2.
- New positive memory-only episodes: 1.
- Full scoring: NOT_RUN / disallowed.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |
| episode_006 | fastapi:1 | inconclusive_equal_performance | true | false |
| episode_010 | ansible:2 | positive_memory_only | true | true |
| episode_020 | ansible:5 | positive_memory_only | true | true |
