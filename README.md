# ControllerGate

ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.

It remains a provenance-first software repair research harness with a conservative pre-alpha research archive boundary.

It turns AI-generated fixes into auditable, sandboxed, rollback-safe software-change candidates, blocking unverified patches before they can contaminate accepted software state.

## What ControllerGate is

- An evidence-bound AI repair validation kernel.
- A proof-gated AI repair runtime scaffold.
- An AI patch hallucination containment layer.
- An AI code governance kernel.
- An admissibility compiler scaffold for future agentic software actions.
- A runtime incident-to-repair quarantine architecture.
- A structure-first software compiler roadmap.

## What ControllerGate is not

- It does not claim hallucination elimination.
- It does not claim absolute uncrashability.
- It does not claim fully self-maintaining software.
- It does not claim autonomous production repair.
- It does not claim production-ready runtime wrapping.
- It does not claim full memory lift or full scoring.
- It is not a formal verification replacement.
- It is not a sector deployment readiness claim.

## Current evidence status

Batch059 is the latest validation-path boundary. It officially ingests Batch058, preserves the Wave 3 provider-capsule prescreen, and runs bounded pre-repair replay for exactly two approved Wave 3 candidates: `audioread_144_py313_aifc_removed` and `cloudpickle_507_py313_typevar_distutils`.

Both candidates materialized target-code failures under declared provider setup. Batch059 does not generate or apply patches, does not run post-repair replay, does not run duplicate replay, and does not run a count gate.

Confirmed external native repair episodes remain `4`. Confirmed issue-derived repair episodes remain `2`. Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

Confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.

Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.

Clean replication batch002 now attempts real external leads and preserves environment-resolution evidence before replay.

Batch059 candidate replay classifications:

- `audioread_144_py313_aifc_removed`: provider capsule setup `provider_capsule_setup_pass`; pre-repair replay `pre_repair_failure_materialized`; AMDS bridge `target_failure_materialized_single_source_family`; future patch-gate candidate.
- `cloudpickle_507_py313_typevar_distutils`: provider capsule setup `provider_capsule_setup_pass`; pre-repair replay `pre_repair_failure_materialized`; AMDS bridge `target_failure_materialized_future_decomposition_recommended`; future patch-gate and decomposition candidate.
- Next allowed action: `batch060_source_only_patch_gate_wave_3`.

## Claim Tier System

ControllerGate uses tiers 0 through 5: Proposed, Demonstrated, Reproduced, Cross-Domain, Predictive, and Theorem/Formal. Every public capability must have a tier, evidence paths or evidence gaps, blockers, and forbidden overclaims.

## Capability Catalog

The capability catalog is stored in `configs/controllergate_capability_catalog.json` and summarized in `docs/capability_inventory.md`.

## Skeptic's Acceptance Checklist

The checklist in `docs/skeptics_acceptance_checklist.md` requires registry-first provenance, decision-time/outcome-time separation, immutable SHA256 custody, fresh workspace purity, target validation, duplicate replay, no-overreach validation, rollback records, and claim tiers.

## Runtime-wrapper roadmap

Batch015 introduces scaffold modules for incident capture, execution-boundary control, isolated sandboxes, dependency drift classification, AST excision diagnostics, syntax rollback, telemetry, compute budgets, simulated blue/green promotion, and proof-to-action manifests. These are MVP scaffolds only.

## Agentic admissibility compiler roadmap

Future work may compile agent intentions into evidence-bound audited action manifests. This is roadmap-only; no integration is implemented.

## Safe public claims

- Evidence-bound repair validation kernel.
- Proof-gated patch admission and quarantine.
- Runtime-wrapper scaffold for audited local fixtures.
- Claim-tiered capability catalog.

## Forbidden claims

- Hallucination elimination.
- Absolute uncrashability.
- Fully self-maintaining software.
- Production-ready runtime wrapper.
- Full scoring.
- Full memory lift.
- Universal bug repair.
- Sector deployment readiness.

## Current operational gate status

- Current protocol remains `v2.14`.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `2`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Batch058 screens Wave 3 leads and approves two candidates for bounded replay.
- Batch059 materializes pre-repair target-code failures for both approved Wave 3 candidates and routes future work to `batch060_source_only_patch_gate_wave_3`.
- Batch059 remains replay/materialization-only; repair counts do not change.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core tests/runtime -q
python scripts/validate_external_candidate_registry.py
python scripts/audit_post_v2_37_hardening_and_batch002.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

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

### Batch056d Wave 2 provider/dependency recovery

- Batch056b official ingest status: `PASS`.
- Batch-lineage sanity: `PASS`; Batch056d follows Batch057c as a branch-relative return to the Wave 2 lane, not as a chronological rollback.
- Provider/dependency recovery attempted candidates: `pairtools_250_py313_pipes_removed, pytest_13480_wdefault_unraisable_threadexception, snapshottest_177_py312_imp_removed`.
- Provider/dependency recovery succeeded count: `1`.
- Post-recovery materialized target-code failure count: `0`.
- Still-blocked candidates: `pairtools_250_py313_pipes_removed, pytest_13480_wdefault_unraisable_threadexception, snapshottest_177_py312_imp_removed`.
- Timeout decomposition candidates deferred: `codex_wave2_nousresearch_hermes_agent_48986, codex_wave2_nousresearch_hermes_agent_60243, codex_wave2_nousresearch_hermes_agent_57197, codex_wave2_m0smith_genia_2026_518`.
- Future decomposition recommendations: `codex_wave2_nousresearch_hermes_agent_48986, codex_wave2_nousresearch_hermes_agent_60243, codex_wave2_nousresearch_hermes_agent_57197, codex_wave2_m0smith_genia_2026_518`.
- Future patch-gate recommendations: `none`.
- Freezegun provider portability recommendation: `future_explicit_authorization_required`.
- Next allowed action: `batch056e_timeout_candidate_decomposition_wave_2`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

### Batch056e timeout decomposition and provider capsules

- Batch056d official ingest status: `PASS`.
- Provider Materialization Capsule standard: `implemented_future_only`.
- Reactome release-download-directory is recorded only as an infrastructure pattern, not as a repair seed or repair evidence.
- Timeout candidates decomposed: `codex_wave2_nousresearch_hermes_agent_48986, codex_wave2_nousresearch_hermes_agent_60243, codex_wave2_nousresearch_hermes_agent_57197, codex_wave2_m0smith_genia_2026_518`.
- Timeout split replay candidates: `codex_wave2_nousresearch_hermes_agent_48986, codex_wave2_nousresearch_hermes_agent_60243, codex_wave2_nousresearch_hermes_agent_57197, codex_wave2_m0smith_genia_2026_518`.
- Provider capsule replay candidates: `none`.
- Manual-review/rejected candidates: `none`.
- Next allowed action: `batch056f_timeout_split_replay_wave_2`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

## Batch056f timeout split replay wave 2

- Batch056e official ingest: `PASS`.
- Timeout split replay standard: `PASS`.
- Reactome step-gating pattern: `infrastructure_pattern_only`.
- Timeout candidates processed: `4`.
- Target-code failure materialization count: `0`.
- Provider/network/model blocked count: `3`.
- Retired/manual-review count: `1`.
- Future patch-gate candidates: `none`.
- Wave 3 recommendation: `recommended`.
- Next allowed action: `batch058_seed_discovery_wave_3`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

## Batch058 seed discovery wave 3 provider prescreen

- Batch056f official ingest: `PASS`.
- Wave 2 timeout/provider paths remain closed without target-code failure materialization.
- Reactome/provider-capsule lesson carried forward as infrastructure pattern only.
- Wave 3 leads screened: `37`.
- Codex-augmented leads count: `30`.
- Commit-resolved candidates: `37`.
- Provider-capsule prescreen pass count: `2`.
- Approved for Batch059 replay: `2`.
- Rejected/unbounded provider count: `0`.
- Batch059 planned candidates: `audioread_144_py313_aifc_removed, cloudpickle_507_py313_typevar_distutils`.
- Next allowed action: `batch059_pre_repair_replay_wave_3_limited`.
- Issue-derived repair count remains `2`; native external repair count remains `4`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.
