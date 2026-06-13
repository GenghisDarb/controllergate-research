# v2.8p BugsInPy Harness Repair Broad Harvest

Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.

- Preserved reference gate: PASS.
- Harness sanity: PASS.
- Broad candidates preflighted: 28 / available 28.
- Returncode-127 failures after normalization: 0.
- Preflight-passing replacement candidates: 19.
- Repair-attempted replacements: 3.
- Executed BugsInPy episodes: 5.
- Scoreable episodes: 2.
- Positive memory-only episodes: 0.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated unless aggregate criteria are met.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |
| episode_006 | ansible:8 | blocked_no_safe_patch_candidate_generated | false | false |
| episode_007 | ansible:12 | blocked_no_safe_patch_candidate_generated | false | false |
| episode_008 | ansible:13 | blocked_no_safe_patch_candidate_generated | false | false |
