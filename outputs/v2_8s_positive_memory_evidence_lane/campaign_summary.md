# v2.8s Positive Memory Evidence Lane

Aggregate result: `insufficient_positive_memory_evidence`.

- Preserved v2.8r baseline gate: PASS.
- Harness sanity: PASS.
- Memory arm separation: PASS.
- Memory evidence eligibility: PASS.
- Candidates preflighted: 28 / available 28.
- Memory-evidence candidates attempted: 1.
- Executed BugsInPy episodes: 4.
- Scoreable episodes: 4.
- Positive memory-only episodes: 1.
- Full scoring: NOT_RUN / disallowed.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |
| episode_006 | fastapi:1 | inconclusive_equal_performance | true | false |
| episode_010 | ansible:2 | positive_memory_only | true | true |
