# v2.12 Dependency Cofactor Recovery and Locked Non-Ansible Repair Validation

- Status: `verified_official_artifact`.
- Workflow run: `27847714846`; artifact ID: `7758557460`.
- Outer ZIP SHA256: `153bb7a7626268c82aab9ddd06f09a6f300688c5585209ca274f471c09ac5454`.
- Internal SHA256SUMS: `3313` checked across `39` manifests, `0` missing, `0` malformed, `0` failures; root coverage complete.
- Tar snapshots excluded from Git ingest: `5`; retained in the verified ZIP.
- Preserved v2.11 baseline gate: `PASS`.
- PySnooper:1 classification: `dependency_recovery_forbidden_by_policy`. The verified artifact simultaneously records `declared_in_project_metadata=true`, `recovery_allowed_by_policy=true`, and `recovery_performed=false` with no forbidden reason; this internal discrepancy is preserved for v2.13 recheck.
- PySnooper:2 declared cofactor recovery: `cofactor_recovered`.
- PySnooper:2 patch validation: `blocked_target_test_failed`.
- Executed episodes: `10`; scoreable episodes: `5`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

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
| episode_033 | PySnooper:1 | blocked_no_safe_patch_candidate_generated | blocked_undeclared_dependency_cofactor | dependency_recovery_forbidden_by_policy | false |
| episode_034 | PySnooper:2 | blocked_no_safe_patch_candidate_generated | blocked_target_test_failed | blocked_target_test_failed | false |
