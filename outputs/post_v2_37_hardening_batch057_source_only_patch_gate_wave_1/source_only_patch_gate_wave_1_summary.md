# Batch057 source-only patch gate wave 1

Batch057 verified the Batch056 artifact, reran fresh pre-repair replay for the four Wave 1 materialized candidates, and applied the source-only patch gate.

- Fresh pre-repair reproductions: `4`
- Source-only patches generated: `0`
- Target-pass source-only patches: `0`
- Blocked/no-safe-patch candidates: `4`
- Next allowed action: `batch057b_source_discovery_recovery_or_batch056b_wave2_pre_repair_replay`

| Candidate | Classification |
| --- | --- |
| `datasette_2461_async_event_loop_cli_tests` | `blocked_ambiguous_multi_failure_source_surface` |
| `freezegun_547_py313_datetimes_assertion` | `blocked_ambiguous_multi_failure_source_surface` |
| `venusian_91_py313_frameinfo_callinfo` | `blocked_no_safe_source_patch` |
| `pexpect_699_replwrap_bash_assertions` | `blocked_environment_specific_failure` |
