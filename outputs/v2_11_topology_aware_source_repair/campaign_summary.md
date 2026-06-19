# v2.11 Topology-Aware Source Repair

- Status: `official_runner_completed_pending_zip_verification`.
- Preserved v2.10 baseline gate: `PASS`.
- Generated source patch candidates: `1`.
- Executed episodes: `9`; scoreable episodes: `5`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
- Tooling note: the v2.10 artifact handling issue was a session/tooling surface problem, not ControllerGate evidence.

| Episode | Candidate | No-memory | Memory-enabled | Classification | Scoreable |
| --- | --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | equal | equal | inconclusive_equal_performance | true |
| episode_003 | black:4 | equal | equal | inconclusive_equal_performance | true |
| episode_006 | fastapi:1 | equal | equal | inconclusive_equal_performance | true |
| episode_010 | ansible:2 | blocked_no_safe_patch_candidate_generated | repaired | positive_memory_only | true |
| episode_020 | ansible:5 | blocked_no_safe_patch_candidate_generated | repaired | positive_memory_only | true |
| episode_030 | fastapi:2 | blocked_no_safe_patch_candidate_generated | blocked_no_safe_patch_candidate_generated | topology_context_recovered_but_no_safe_patch | false |
| episode_031 | fastapi:3 | blocked_no_safe_patch_candidate_generated | blocked_no_safe_patch_candidate_generated | topology_context_recovered_but_no_safe_patch | false |
| episode_032 | fastapi:4 | blocked_no_safe_patch_candidate_generated | blocked_no_safe_patch_candidate_generated | topology_context_recovered_but_no_safe_patch | false |
| episode_033 | PySnooper:1 | blocked_no_safe_patch_candidate_generated | blocked_target_test_failed | blocked_target_test_failed | false |
