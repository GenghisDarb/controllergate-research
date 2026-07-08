# ControllerGate shareable summary

ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.

Current evidence boundary: four confirmed external native repair episodes, zero confirmed issue-derived repair episodes, full scoring disabled, memory lift not demonstrated, and self-maintaining software not demonstrated.

Batch015 adds runtime-wrapper scaffold modules, a lock-sequence operation registry, claim tiers, a capability catalog, public positioning, and roadmap-only compiler directions. It does not claim production readiness or new repair evidence.

Batch017 attempts decision-time dependency-era resolution for Darker issue #112 and starts thin artifact packaging. It blocks rather than patching when no decision-time dependency lock is proven.

## Current operational gate status

- Current protocol remains `v2.13`.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Batch015 adds a runtime-wrapper scaffold, lock-sequence registry, claim tiers, and product-positioning boundaries without live deployment.
- Batch016 addresses target-intent alignment for the issue-derived Darker seed and safe-stops before repair because the observed failure is pre-target/precondition.
- Batch017 attempts decision-time dependency-era resolution and starts thin artifact packaging; it safe-stops if no decision-time dependency lock can be proven.

## Batch039 secondary cofactor governance

- Batch039 ingests the official Batch038 artifact and preserves the verified target-resolution progress.
- The remaining blocker is classified as a declared but unpinned secondary cofactor, so provider materialization is blocked until a reviewed pinned lock exists.
- Missing secondary tooling is not counted as the original target failure or as repair success.
- Confirmed native repair episodes remain `4`; confirmed issue-derived repair episodes remain `0`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

### Batch052 Lemon Reader source-only patch candidate gate

- Batch052 status: `PASS_WITH_BATCH052_TARGET_REPLAY_PASSED`.
- Current protocol remains: `v2.14`.
- Source-only suitability: `source_repair_suitable`.
- Patch generation status: `PASS`.
- Patch apply status: `PASS`.
- Post-repair target replay status: `PASS_WITH_BATCH052_TARGET_REPLAY_PASSED`.
- Duplicate replay status: `NOT_RUN`; reason: `waits_for_batch053_duplicate_clean_replay_gate`.
- Exact blocker: `None`.
- Next allowed action: `batch053_duplicate_clean_replay_gate`.
- External native repair episodes remain `4`; issue-derived repair episodes remain `1`.
- Batch052 does not run duplicate replay, full scoring, memory-lift claims, self-maintaining claims, or production-readiness claims.

### Batch053 duplicate clean replay and evidence contract hardening

- Batch053 status: `PASS_WITH_BATCH053_SECONDARY_BLOCKER_OBSERVED`.
- Current protocol remains: `v2.14`.
- Duplicate clean replay status: `PASS_WITH_BATCH053_SECONDARY_BLOCKER_OBSERVED`.
- Duplicate clean replay return code: `None`.
- Issue-derived repair validated candidate: `false`.
- Exact blocker: `host_environment_not_ubuntu_latest_python311`.
- Next allowed action: `secondary_blocker_governance_gate`.
- External native repair episodes remain `4`; issue-derived repair episodes remain `1`.
- Batch053 does not increment repair counts, run full scoring, claim memory lift, claim self-maintaining software, or claim production readiness.

### Batch054 issue-derived repair count gate and next patch preparation

- Batch054 status: `PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED`.
- Current protocol remains: `v2.14`.
- Issue-derived repair episodes after Batch054: `2`.
- External native repair episodes remain `4`.
- Exact blocker: `None`.
- Next allowed action: `batch055_next_patch_seed_gate`.
- Next seed fastlane status: `WAITING_FOR_FRESH_SEED`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`; production readiness remains `false/not_demonstrated`.

### Batch050 manual fresh-seed intake fast lane

- Batch050 status: `PASS_WITH_BATCH050_MANUAL_SEED_PACKAGE_REQUIRED`.
- Current protocol remains: `v2.14`.
- Manual seed package found: `false`.
- Approved unused issue seed count: `0`.
- Exact blocker: `manual_seed_artifact_absent`.
- Next allowed action: `provide_manual_seed_package`.
- Environment elbow classification: `source_acquisition_boundary`.
- Shell closure status: `open_waiting_for_fresh_seed`.
- External native repair episodes remain `4`; issue-derived repair episodes remain `1`.
- Batch050 is an intake/template gate only; repair generation, target replay, dependency install, full scoring, memory-lift claims, and production-readiness claims remain disabled.

### Batch051 Lemon Reader manual seed pre-repair replay gate

- Batch051 status: `PASS_WITH_BATCH051_PRE_REPAIR_FAILURE_MATERIALIZED`.
- Candidate approved: `true`.
- Approved unused issue seed count: `1`.
- Pre-repair replay status: `PASS_WITH_BATCH051_PRE_REPAIR_FAILURE_MATERIALIZED`.
- Exact blocker: `None`.
- Next allowed action: `batch052_source_only_patch_candidate_gate`.
- External native repair episodes remain `4`; issue-derived repair episodes remain `1`.
- Batch051 is a seed-approval and pre-repair replay gate only; repair generation, patch generation, duplicate replay, full scoring, memory-lift claims, and production-readiness claims remain disabled.

### Batch055 seed discovery wave 1

- Batch054 official ingest status: `PASS`.
- Batch055 seed discovery wave 1 status: `PASS`.
- Issue-derived repair count preserved at `2`; native external repair count preserved at `4`.
- Weak leads screened: `24`; Codex-augmented leads: `10`.
- Commit-resolved candidates: `23`; approved for Batch056 pre-repair replay: `8`.
- Next allowed action: `batch056_pre_repair_replay_wave_1`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

### Batch056 pre-repair replay wave 1 plus wave 2 intake

- Batch055 official ingest status: `PASS`.
- Batch056 Wave 1 pre-repair replay status: `PASS`.
- Wave 1 candidates: `5`; materialized failures: `4`; blocked/non-materialized: `1`.
- Batch057 patch-gate recommendation count: `4`.
- Wave 2 leads screened: `23`; commit-resolved: `18`; approved for future replay: `7`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Next allowed action: `batch057_source_only_patch_gate_wave_1`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

### Batch057 source-only patch gate wave 1

- Batch056 official ingest status: `PASS`.
- Batch057 source-only patch gate status: `PASS`.
- Fresh Batch057 pre-repair reproduction count: `4`.
- Patch-generated count: `0`; source-only target-pass count: `0`; target-fail count: `0`.
- Blocked/no-safe-patch count: `4`.
- Batch058 duplicate replay candidate count: `0`.
- Wave 2 future plan is preserved only; no Wave 2 replay, patch, or count gate ran.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Next allowed action: `batch057b_source_discovery_recovery_or_batch056b_wave2_pre_repair_replay`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

### Batch057b failure-family decomposition elbow recovery

- Batch057 official ingest status: `PASS`.
- Batch057b decomposition status: `PASS`.
- Minimal subtarget replay count: `5`.
- Elbow-open candidate count: `1`.
- Elbow-closed candidate count: `3`.
- Retired Wave 1 candidate count: `1`.
- Batch057c recommended candidates: `freezegun_547_py313_datetimes_assertion`.
- Wave 2 pre-repair replay recommendation: `defer_because_batch057c_has_elbow_open_candidate`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Next allowed action: `batch057c_source_only_patch_recovery_wave_1`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

| Candidate | Elbow state | Bug layers |
| --- | --- | --- |
| `datasette_2461_async_event_loop_cli_tests` | `elbow_closed_multi_family_ambiguous` | `dependency_install_bug, environment_provider_bug, multi_causal_failure_surface, primary_source_bug, secondary_source_bug` |
| `freezegun_547_py313_datetimes_assertion` | `elbow_open_primary_family_only_diagnostic_patch_allowed` | `primary_source_bug, secondary_source_bug` |
| `venusian_91_py313_frameinfo_callinfo` | `elbow_closed_test_expectation_or_interpreter_behavior` | `interpreter_behavior_change` |
| `pexpect_699_replwrap_bash_assertions` | `elbow_closed_environment_provider` | `environment_provider_bug` |

### Batch057c layered source-only patch recovery Freezegun

- Batch057b official ingest status: `PASS`.
- Batch057c Freezegun layered patch status: `PASS`.
- Fresh pre-repair replay status: `pre_repair_failure_reproduced`.
- Primary family patch status: `stage1_primary_patch_partial_improvement_secondary_still_fails`.
- Secondary family patch status: `stage2_not_authorized`.
- Full original target post-repair status: `FAIL`.
- Batch058 duplicate replay candidate exists: `False`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Next allowed action: `batch056b_wave2_pre_repair_replay`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

### Batch056b Wave 2 pre-repair replay plus AMDS bridge

- Batch057c official ingest status: `PASS`.
- Freezegun partial-improvement evidence is preserved and remains uncounted.
- Freezegun secondary provider blocker is preserved for future provider-compatible investigation.
- AMDS and MinimalProbe are recorded as existing capabilities; Batch056b adds bridge instrumentation only.
- Wave 2 replay candidate count: `7`.
- Wave 2 materialized failure count: `0`; blocked count: `7`.
- Future patch-gate candidates: `none`.
- Decomposition candidates: `codex_wave2_nousresearch_hermes_agent_48986, codex_wave2_nousresearch_hermes_agent_60243, codex_wave2_nousresearch_hermes_agent_57197, codex_wave2_m0smith_genia_2026_518`.
- Provider/dependency recovery candidates: `pairtools_250_py313_pipes_removed, pytest_13480_wdefault_unraisable_threadexception, snapshottest_177_py312_imp_removed`.
- Next allowed action: `batch056d_wave2_provider_dependency_recovery`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.
