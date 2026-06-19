# v2.10 Materialization Recovery and Topological Repair

- Status: `official_runner_completed_pending_zip_verification`.
- Preserved v2.9 baseline gate: `PASS`.
- Bounded materialization records: `6`; recovered: `4`.
- Executed episodes: `9`; scoreable episodes: `5`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

| Episode | Candidate | Classification | Scoreable | Memory outperformed |
| --- | --- | --- | --- | --- |
| episode_001 | youtube-dl:1 | inconclusive_equal_performance | true | false |
| episode_003 | black:4 | inconclusive_equal_performance | true | false |
| episode_006 | fastapi:1 | inconclusive_equal_performance | true | false |
| episode_010 | ansible:2 | positive_memory_only | true | true |
| episode_020 | ansible:5 | positive_memory_only | true | true |
| episode_030 | fastapi:2 | materialization_recovered_but_no_safe_repair_path | false | false |
| episode_031 | fastapi:3 | materialization_recovered_but_no_safe_repair_path | false | false |
| episode_032 | fastapi:4 | materialization_recovered_but_no_safe_repair_path | false | false |
| episode_033 | PySnooper:1 | materialization_recovered_but_no_safe_repair_path | false | false |
