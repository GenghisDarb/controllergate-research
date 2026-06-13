# v2.8n BugsInPy Replacement Preflight Third Scoreable

Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.

- Executed BugsInPy episodes: 5.
- Scoreable episodes: 2.
- Positive memory-only episodes: 0.
- Candidate preflight runs before repair generation.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated unless aggregate criteria are met.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_002 | black:8 | blocked_no_safe_patch_candidate_generated | false | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |
| episode_004 | black:6 | blocked_replay_or_materialization_failure | false | false |
| episode_005 | black:7 | blocked_no_safe_patch_candidate_generated | false | false |
