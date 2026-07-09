Batch063 is the latest limited pre-repair replay boundary. It officially ingests Batch058c and runs fresh replay only for the two Batch058c-approved candidates, Pytest and Freezegun, before any later patch gate can be considered.

Batch063 status:

- Batch058c official ingest: `PASS`.
- Candidate replay scope: `pytest_13895_pytest9_skiptest_behavior`, `freezegun_547_py313_datetimes_assertion`.
- Pytest pre-repair replay classification: `blocked_target_command_invalid`.
- Freezegun pre-repair replay classification: `pre_repair_failure_materialized`.
- Materialized failure count: `1`.
- Failure-not-reproduced count: `0`.
- Provider/runtime blocked count: `1`.
- Future patch-gate candidate count: `1`.
- Future decomposition candidate count: `0`.
- Next allowed action: `batch064_source_only_patch_gate_for_materialized_batch063_candidates`.
- Issue-derived repair count preserved at `3`.
- Native external repair count preserved at `4`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success.
Pre-repair replay is not repair success.
Diagnostic replay is not repair success.
Provider/runtime setup is not repair success.
Future patch license is not repair success.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.
