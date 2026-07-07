# Batch057b failure-family decomposition elbow recovery

- Status: `PASS`
- Batch057 official ingest status: `PASS`
- Minimal subtarget replay count: `5`
- Elbow-open candidate count: `1`
- Elbow-closed candidate count: `3`
- Retired Wave 1 candidate count: `1`
- Batch057c recommended candidates: `freezegun_547_py313_datetimes_assertion`
- Next allowed action: `batch057c_source_only_patch_recovery_wave_1`

| Candidate | Elbow state | Bug layers |
| --- | --- | --- |
| `datasette_2461_async_event_loop_cli_tests` | `elbow_closed_multi_family_ambiguous` | `dependency_install_bug, environment_provider_bug, multi_causal_failure_surface, primary_source_bug, secondary_source_bug` |
| `freezegun_547_py313_datetimes_assertion` | `elbow_open_primary_family_only_diagnostic_patch_allowed` | `primary_source_bug, secondary_source_bug` |
| `venusian_91_py313_frameinfo_callinfo` | `elbow_closed_test_expectation_or_interpreter_behavior` | `interpreter_behavior_change` |
| `pexpect_699_replwrap_bash_assertions` | `elbow_closed_environment_provider` | `environment_provider_bug` |
