# v2.14 capability recovery lane

Status: `PASS_WITH_BOUNDED_BLOCKERS`

This lane is a bounded non-Ansible capability-recovery check. It does not promote v2.14 to current, does not run full scoring, and does not change v2.13 scientific results.

## Scope

- Candidate order: `PySnooper:1`, then `PySnooper:2`.
- Forbidden candidates were not attempted: FastAPI, Black, youtube-dl, ansible, or any new candidate.
- Diagnostic probes used: `2` of `4`.
- Revised patch attempts used: `0` of `2`.

## Result

- Baseline preservation: `PASS`.
- PySnooper:1 final classification: `pysnooper1_dependency_recovery_execution_blocked`.
- PySnooper:2 final classification: `pysnooper2_fixture_materialization_forbidden_or_unavailable`.
- No non-Ansible scoreable/positive-memory result was produced.
- Updated scoreable count: `5`.
- Updated positive-memory count: `2`.
- Non-Ansible positive-memory count: `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software remains false / not demonstrated.

## Exact blocker

PySnooper:1 stopped at dependency recovery execution because the policy declaration was safe but the isolated recovery executor was not authorized/available in this bounded lane; PySnooper:2 stopped because tests/mini_toolbox.py fixture/helper materialization remains forbidden or unavailable.
