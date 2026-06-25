# v2.13 Minimal Forensic Context Lane

- Status: `official_runner_completed_pending_independent_audit_and_zip_verification`.
- Exact five-candidate v2.12 baseline rerun: `PASS`.
- ansible:2 positive-memory-only preservation: `PASS`.
- ansible:5 positive-memory-only preservation: `PASS`.
- PySnooper:1 policy recheck: `dependency_recovery_allowed_by_policy_not_executed_in_minimal_lane`.
- PySnooper:2 deterministic failed-patch classification: `fixture_materialization_incomplete`.
- Diagnostic probes used: `0`.
- Revised patch authorized: `false`; attempted: `false`.
- PySnooper:2 remains non-scoreable because the target test directly imports missing `tests/mini_toolbox.py`; source-only repair cannot modify tests or fixtures.
- Scoreable episodes: `5`; positive-memory-only episodes: `2`; non-Ansible positive-memory episodes: `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
