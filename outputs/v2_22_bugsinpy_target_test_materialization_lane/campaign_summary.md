# v2.22 BugsInPy Target-Test Materialization Lane

- Campaign: `v2_22_bugsinpy_target_test_materialization_lane`.
- Scope: `PySnooper:1` only; PySnooper:2 was not pursued.
- v2.21 official ingest verified: `true`.
- Pinned BugsInPy framework: `https://github.com/soarsmu/BugsInPy.git` at `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Official framework materialization attempted: `true`.
- Framework checkout is treated as metadata/framework, not materialized source: `true`.
- Target-test search result: `found`.
- Target-test provenance: `BLOCK`.
- Fixed/future/gold/synthetic source guard: `BLOCK`.
- PySnooper:1 terminal provenance decision: `terminal_blocked`.
- Dependency recovery: `not_executed_target_test_provenance_blocked`.
- Pre-repair replay: `not_run_target_test_provenance_blocked`.
- Patch generated / authorized / attempted: `false` / `false` / `false`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Final blocker: `blocked_target_test_requires_fixed_or_future_source`.
- Current protocol remains `v2.13`; v2.22 is not promoted to current.
