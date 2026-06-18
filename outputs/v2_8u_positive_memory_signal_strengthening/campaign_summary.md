# v2.8u positive memory signal strengthening

Aggregate result: `replicated_positive_memory_signal_preserved`.

- Preserved v2.8t baseline gate: PASS.
- ansible:2 positive-memory baseline preserved: True.
- ansible:5 positive-memory baseline preserved: True.
- Harness sanity: PASS.
- Memory arm separation: PASS.
- Memory evidence eligibility: PASS.
- memory generalization integrity: PASS.
- Candidates preflighted: 28 / available 28.
- Memory-generalization candidates attempted: 3.
- Executed BugsInPy episodes: 8.
- Scoreable episodes: 5.
- Positive memory-only episodes: 2.
- New positive memory-only episodes: 0.
- Family generalization: replicated_positive_memory_signal_preserved.
- Full scoring: NOT_RUN / disallowed.
- Self-maintaining software: not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |
| episode_006 | fastapi:1 | inconclusive_equal_performance | true | false |
| episode_010 | ansible:2 | positive_memory_only | true | true |
| episode_020 | ansible:5 | positive_memory_only | true | true |
| episode_030 | ansible:4 | blocked_no_safe_patch_candidate_generated | false | false |
| episode_031 | ansible:12 | blocked_no_safe_patch_candidate_generated | false | false |
| episode_032 | ansible:13 | blocked_no_safe_patch_candidate_generated | false | false |
