# ControllerGate

ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.

It remains a provenance-first software repair research harness with a conservative pre-alpha research archive boundary.

It turns AI-generated fixes into auditable, sandboxed, rollback-safe software-change candidates, blocking unverified patches before they can contaminate accepted software state.

## Validated protocol and static frontier

The validated current protocol is `v2.15 semantic_frontier_planning_and_bounded_probe_lane`. Batch068h replaces generic planning passthroughs with 11 step-specific semantic handlers and 11 independent verifiers, then deterministically reprocesses the frozen 25-candidate inventory. The preceding `v2.14 capability_recovery_lane` remains directly selectable and audited.

Batch068h also defines an authorization-bound, collection-only OCI provider probe for the sole Tier-3 candidate. Static protocol promotion is independent of probe success. A substrate, exact-runtime, source-custody, provider, collection, or immutability block stops the probe without patch authority, target-test execution, or repair-count changes.

Canonical generated frontier status: [docs/CURRENT_FRONTIER_STATUS.md](docs/CURRENT_FRONTIER_STATUS.md).

- Confirmed issue-derived repair episodes: `4`.
- Confirmed native external repair episodes: `4`.
- Runtime connectors and live-device repair: inactive.
- Patches generated or applied by Batch068h: `0`.
- Target-test bodies executed by Batch068h: `0`.
- Full scoring: `NOT_RUN/disallowed`.
- Memory lift: `not_demonstrated`.
- Self-maintaining software: `false/not_demonstrated`.

## Batch063e Pytest Runner-Target Split Evidence Intake

Batch063e evaluates Pytest runner-target import origin after Batch063d normalized version-origin metadata. It tests whether Pytest can be run as a declared self-hosted test runner or through a proven external runner-target split. These are command-boundary controls and replay-readiness evidence, not repair proof. No repair is counted without source-only target pass, duplicate clean replay, and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated.

Batch063e status:

- Batch063d artifact ingest: `PASS`.
- Batch063d tag authority preservation: `PASS`.
- Self-hosted runner model: `declared_self_hosted_runner_unproven`.
- External runner model: `external_runner_target_import_origin_unproven`.
- Selected runner-target model: `blocked_unproven_runner_target_model`.
- Pytest pre-repair replay: `pytest_runner_target_model_unproven`.
- Pytest terminal state: `pytest_runner_target_split_unresolved_after_model_probe`.
- Seed harvest authorization: `AUTHORIZED`.
- Issue-derived repair count remains `4`.
- Native external repair count remains `4`.
- Next allowed action: `batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_063d_063e_controls`.

## Batch063d Pytest Safe Tag Acquisition Hardening

Batch063d adds a predeclared ancestor-tag authority lifecycle for Pytest version-origin recovery. It compares committed Batch063c evidence with the manually supplied Batch063c workflow artifact, records any committed-vs-workflow artifact divergence, and then attempts a bounded tag-authority path using remote tag metadata plus a blobless candidate commit graph. The tag manifest is allowed only for version-origin reconstruction, never as patch authority or count evidence.

Batch063d status:

- Batch063c artifact reconciliation: `committed_vs_workflow_artifact_ingest_status_divergence_recorded`.
- Safe tag authority: `predeclared_ancestor_tag_authority_manifest_PASS`.
- Tag authority lifecycle: `PASS`.
- Version-origin status: `pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority`.
- Runner-target import-origin status: `runner_target_split_requires_external_runner_identity`.
- Command-boundary status: `pytest_command_boundary_blocked_runner_target_split_after_version_origin_normalized`.
- Pre-repair replay: `NOT_RUN_blocked_runner_target_split_after_safe_tag_authority`.
- Issue-derived repair count remains `4`.
- Native external repair count remains `4`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `batch063e_pytest_runner_target_split_evidence_intake`.

## Batch063c Pytest Command-Boundary Follow-up

Batch063c applies the Batch067 wrapper infrastructure to Pytest command-boundary recovery and restores missing pre-generation, reward-signal, baseline-drift, and structural-transfer controls. These are engineering controls and routing evidence, not repair proof. No repair is counted without source-only target pass, duplicate clean replay, and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated.

Batch063c status:

- Batch067 artifact/result preservation: `PASS`.
- Pre-generation state lock: `PASS`.
- Reward signal: `PASS`.
- Baseline registry precheck: `baseline_drift_precheck_PASS_isolated_runtime`.
- Structural transfer ledger: `PASS`.
- Pytest safe tag acquisition: `blocked_no_predeclared_ancestor_tag_authority`.
- Pytest version-origin status: `pytest_version_origin_missing_tags`.
- Pytest runner-target status: `runner_target_collision_unresolved_self_runner`.
- Pytest command-boundary status: `pytest_command_boundary_blocked_version_origin`.
- Pytest pre-repair replay: `NOT_RUN_blocked_version_origin_missing_tags_safe_tag_authority_absent`.
- Issue-derived repair count remains `4`.
- Native external repair count remains `4`.
- Next allowed action: `batch063d_pytest_safe_tag_acquisition_hardening`.

## Batch067 Universal Wrapper Hardening Implementation

Batch067 adds reusable wrapper and failure-translation infrastructure. These controls improve candidate intake, environment classification, command-boundary handling, and terminal-state routing. They are engineering controls, not repair proof.

Batch067 status:

- Artifact custody module: `working_reusable_batch067`.
- Step contract module: `working_reusable_batch067`.
- Workspace purity module: `working_reusable_batch067`.
- Command translation module: `working_reusable_batch067`.
- Harness origin module: `working_reusable_batch067`.
- Version-origin module: `working_reusable_batch067`.
- Runner-target module: `working_reusable_batch067`.
- Terminal-state module: `working_reusable_batch067`.
- Safe-abstention module: `working_reusable_batch067`.
- Source-topology module: `working_reusable_batch067`.
- Proof-ledger fork-point module: `working_reusable_batch067`.
- Public summary guard: `PASS`.
- Cross-environment equivalence layer: `working_reusable_batch067`.
- Candidate seed classification gate: `working_reusable_batch067`.
- Failure translation layer: `working_reusable_batch067`.
- Source approval gate: `working_reusable_batch067`.
- Probe-to-candidate promotion policy: active and routing-only until promoted.
- Issue-derived repair count remains `4`.
- Native external repair count remains `4`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `batch063c_pytest_command_boundary_followup`.

Batch067 did not generate or apply a patch, did not run duplicate clean replay, did not run a count gate, and did not increment any repair count.

## Batch063b Pytest provider/runtime recovery follow-up

Batch063b is the latest Pytest command-boundary and wrapper-hardening boundary. It officially ingests Batch066, keeps repair counts unchanged, creates a fresh candidate-isolated Pytest workspace, and verifies that provider/runtime setup alone does not authorize a repair.

Batch063b status:

- Batch066 official ingest: `PASS`.
- Issue-derived repair count preserved at `4`.
- Native external repair count preserved at `4`.
- Pytest version-origin bootstrap status: `pytest_version_origin_missing_tags`.
- Pytest runner-target import-origin status: `runner_target_collision_unresolved_self_runner`.
- Pytest command-boundary status: `pytest_command_boundary_blocked_version_origin`.
- Pytest provider/runtime setup status: `provider_runtime_recovered_from_declared_metadata`.
- Pytest pre-repair replay status: `blocked_target_command_invalid`.
- Future patch-license state: `pytest_patch_license_closed_command_boundary_blocked`.
- Universal wrapper hardening status: `scaffolded_active_batch063b`.
- Workspace purity policy status: `scaffolded_active_batch063b`.
- Candidate-isolated runtime policy status: `scaffolded_active_batch063b`.
- Command translation layer status: `scaffolded_active_batch063b`.
- Non-circular harness origin policy status: `scaffolded_active_batch063b`.
- AST topology requirement status: `future_patch_gate_law_scaffolded`.
- Cross-family homology ledger status: `routing_memory_only_scaffolded`.
- Confidence abstention policy status: `active_terminal_state_closure`.
- Terminal-state registry status: `scaffolded_active_batch063b`.
- Repo public-readiness status: `research_archive_not_release_ready`.
- Duplicate-function review status: `reviewed_no_refactor`.
- Permanent-fix backlog status: `updated`.
- Historical requirements recovery status: `PASS`.
- Recovered historical requirement count: `15`.
- Historical requirements implemented now: `1`.
- Historical requirements scaffolded with audit: `12`.
- Historical requirements blocked with exact reason: `0`.
- Historical requirements assigned to named future batches: `12`.
- False-win verification gate status: `scaffolded_with_config_and_audit`.
- Deterministic replay readiness gate status: `scaffolded_with_config_and_audit`.
- Matched baseline/null-wrapper status: `null_wrapper_scaffolded`.
- Provider/cofactor lock status: `scaffolded_with_config_and_audit`.
- Command normalization / workflow snapshot guard status: `scaffolded_with_config_and_audit`.
- Harness origin policy status: `scaffolded_active_batch063b`.
- Workspace purity status: `scaffolded_active_batch063b`.
- Source-topology precondition status: `future_patch_gate_law_scaffolded`.
- Safe-abstention policy status: `active_terminal_state_closure`.
- Terminal-state/reopen-condition policy status: `scaffolded_active_batch063b`.
- Repo-hygiene pressure status: `high_but_not_dominant_over_pytest_followup`.
- Recommended next proof path: `batch063c_pytest_command_boundary_followup`.
- Recommended next wrapper-hardening path: `batch067_universal_wrapper_hardening_implementation`.
- Project health grade: `A-`.
- Traffic-light status: `yellow`.
- Distance to issue-derived repair count 5: `one_counted_issue_repair`.
- Distance to self-maintaining claim: `far`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success. Version-origin recovery is not repair success. Command-boundary normalization is not repair success. Provider/runtime setup is not repair success. Pre-repair replay is not repair success. ControllerGate is being hardened as a high-integrity maintenance wrapper, but self-maintaining software remains false/not_demonstrated. These wrapper-hardening artifacts are engineering controls, not repair proof. No source repair is counted without source-only target pass, duplicate clean replay, and count gate. A repair is counted only after source-only target pass, duplicate clean replay, and count gate. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.

## Batch065 duplicate clean replay and Freezegun count gate

Batch065 is the latest duplicate clean replay and issue-derived repair count-gate boundary. It officially ingests Batch064, verifies the exact Freezegun source-only patch identity, recreates a clean duplicate workspace, reproduces the pre-repair failure, applies the exact Batch064 patch, and runs the original target command again before the count gate.

Batch065 status:

- Batch064 official ingest: `PASS`.
- Freezegun duplicate clean replay: `duplicate_clean_replay_pass`.
- Pre-repair duplicate reproduction: `freezegun_staged_source_family_preserved`.
- Exact patch identity: `PASS`.
- Post-patch duplicate target replay: `PASS`.
- Count gate status: `PASS`.
- Issue-derived repair count before/after: `3` -> `4`.
- Native external repair count preserved at `4`.
- Project health grade: `A-`.
- Traffic-light status: `yellow`.
- Post-count acceleration status: `PASS`.
- Next count opportunity queue: `PASS`.
- Recommended next proof path: `batch066_next_issue_repair_candidate_selection_or_pytest_recovery`.
- Public-readiness audit: `PASS`.
- Repo topology review: `PASS`.
- Duplicate-function review: `PASS`.
- Permanent-fix queue: `PASS`.
- Provider-capsule utilization review: `advisory_complete`.
- Governance utilization review: `advisory_complete`.
- Self-maintaining wrapper capability gap status: `open`.
- Next allowed action: `batch066_next_issue_repair_candidate_selection_or_pytest_recovery`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success. Provider/runtime setup is not repair success. A repair is counted only after duplicate clean replay and count gate pass. The public-readiness and repo-topology reviews are advisory and do not constitute repair proof. No repo refactor was performed in this proof-gate batch. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.

## Batch066 next issue-repair candidate selection and Pytest recovery

Batch066 is the latest strategic transition and Pytest command-boundary recovery boundary. It officially ingests Batch065, preserves the counted Freezegun repair, keeps the issue-derived repair count at 4, and evaluates whether Pytest can move from command-boundary blocked status toward a future source-only patch gate.

Batch066 status:

- Batch065 official ingest: `PASS`.
- Freezegun counted repair preservation: `PASS`.
- Issue-derived repair count preserved at `4`.
- Native external repair count preserved at `4`.
- Pytest command-boundary recovery status: `pytest_command_boundary_blocked_config_minversion`.
- Pytest provider/runtime status: `provider_runtime_recovered_from_declared_metadata`.
- Pytest pre-repair materialization status: `blocked_target_command_invalid`.
- Next count opportunity status: `PASS`.
- Repo-hygiene pressure status: `medium_high_not_dominant`.
- Public-readiness pressure status: `medium_not_dominant`.
- Recommended next action: `batch063b_pytest_provider_runtime_recovery_followup`.
- Project health grade: `A-`.
- Traffic-light status: `yellow`.
- Distance to issue-derived repair count 5: `one_counted_issue_repair`.
- Distance to self-maintaining claim: `far`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success. Command-boundary normalization is not repair success. Provider/runtime setup is not repair success. Pre-repair replay is not repair success. A repair is counted only after source-only target pass, duplicate clean replay, and count gate. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.

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

Batch064 is the latest Freezegun source-only patch-gate boundary. It officially ingests Batch063, preserves the Pytest command-boundary blocker, replays the Freezegun failure in a fresh workspace, performs source discovery, applies a bounded source-only patch when licensed, and runs post-repair target validation.

Batch064 status:

- Batch063 official ingest: `PASS`.
- Freezegun pre-repair reproduction: `pre_repair_failure_materialized`.
- Failure split classification: `freezegun_two_source_families`.
- Source discovery status: `PASS`.
- Patch license state: `freezegun_patch_license_open_staged_source_family`.
- Patch generated/applied: `True` / `True`.
- Post-repair original target outcome: `source_only_patch_target_pass`.
- Pytest command-boundary preservation: `blocked_target_command_invalid`.
- Future duplicate replay candidate count: `1`.
- Project health grade: `B+`.
- Traffic-light status: `yellow`.
- Distance to issue-derived repair count 4: `near`.
- Distance to self-maintaining claim: `far`.
- Next allowed action: `batch065_duplicate_clean_replay_and_issue_repair_count_gate_freezegun`.
- Issue-derived repair count preserved at `3`.
- Native external repair count preserved at `4`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success.
Pre-repair replay is not repair success.
Future patch license is not repair success.
Partial improvement is not repair success.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.

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

Batch058c is the latest seed-discovery and salvage-reassessment boundary. It officially ingests Batch060f, closes Audioread as a provider/backend-unavailable terminal state unless provider availability changes, and selects a small bounded future replay set without replaying or patching.

Batch058c status:

- Batch060f official ingest: `PASS`.
- Audioread terminal-state closure: `provider_backend_unavailable_declared`.
- Audioread reopen condition: `closed_until_provider_availability_changes`.
- Negative seed patterns learned: optional backend unavailable, declared external provider missing, provider capsule unavailable, unbounded provider risk, compiled dependency risk, missing SHA or command.
- Leads screened: `47`.
- Deduplicated leads: `47`.
- Provider-risk rejections: `19`.
- Approved future replay candidates: `2`.
- Highest-ranked future replay or salvage candidates: `pytest_13895_pytest9_skiptest_behavior, freezegun_547_py313_datetimes_assertion`.
- Wave 1/Wave 2 salvage reassessment: `PASS`.
- Project health grade: `B`.
- Traffic-light status: `yellow`.
- Distance to issue-derived repair count 4: `near_to_medium`.
- Distance to self-maintaining claim: `far`.
- Next allowed action: `batch063_wave3_or_salvage_pre_repair_replay_limited`.
- Issue-derived repair count preserved at `3`.
- Native external repair count preserved at `4`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success.
Seed discovery is not repair success.
Provider/runtime pre-screening is not repair success.
Provider/backend setup is not repair success.
Partial improvement is not repair success.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.

Batch060f is the latest Audioread branch-replay boundary. It officially ingests Batch058b, preserves the exact prior Audioread patch branch, and tests the provider/backend capsule route without generating a new patch or changing repair counts.

Batch060f status:

- Batch058b official ingest: `PASS`.
- Audioread prior branch preservation: `PASS`.
- Pre-repair reproduction: `pre_repair_failure_reproduced_module_aifc_missing`.
- Exact prior patch identity: `PASS`.
- Provider/backend capsule classification: `provider_backend_capsule_unavailable`.
- Provider install status: `NOT_RUN`.
- Replay matrix outcome: `audioread_provider_backend_unavailable_declared`.
- Target pass after exact prior patch plus bounded provider capsule: `False`.
- Issue-derived repair count preserved at `3`.
- Native external repair count preserved at `4`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `batch058c_seed_discovery_expansion_or_salvage_reassessment`.

Workflow success is not equivalent to repair success.
Provider/backend setup is not repair success.
Partial improvement is not repair success.
Applying an exact prior patch for branch replay is not a new repair.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.

Batch058b is the latest seed-discovery boundary. It officially ingests Batch062, preserves the current repair counts, and hardens the provider-screened Wave 3 intake path without replaying, patching, or changing repair counts.

Batch058b status:

- Batch062 official ingest: `PASS`.
- Issue-derived repair count preserved at `3`.
- Native external repair count preserved at `4`.
- Wave 3 seed expansion: `PASS`.
- Leads screened: `37`.
- Deduplicated leads: `35`.
- Duplicate rejections: `2`.
- Provider/runtime risk rejections: `34`.
- Approved for future replay: `0`.
- Highest-ranked future replay candidates: `none`.
- Project health grade: `B`; traffic-light status `yellow`.
- Distance to next repair-count milestone: `medium`.
- Distance to self-maintaining claim: `far`.
- Next allowed action: `batch060f_audioread_provider_backend_capsule_replay`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success.
Seed discovery is not repair success.
Provider/runtime pre-screening is not repair success.
Repair count increments require duplicate clean replay and count gate.
The project health grade is advisory and does not constitute proof.
Self-maintaining software remains false/not_demonstrated.

Batch062 is the latest strategic selection boundary. It officially ingests Batch061, preserves the counted Cloudpickle issue-derived repair, and reviews the next candidate route without patching, replaying, or changing repair counts.

Batch062 status:

- Batch061 official ingest: `PASS`.
- Cloudpickle counted repair preservation: `PASS`.
- Issue-derived repair count preserved at `3`.
- Native external repair count preserved at `4`.
- Candidate pool review: `PASS`.
- Wave 1/Wave 2 salvage review: `PASS`, 10 previously blocked candidates reviewed.
- Recommended reopening or bounded reassessment candidates: `4`.
- Recommended parked/manual-review candidates: `3`.
- Recommended retirement confirmations: `3`.
- Highest-ranked parked candidate: `audioread_144_py313_aifc_removed`.
- New-seed expansion still outranks salvage: `true`.
- Highest-impact next path: `batch058b_seed_discovery_wave_3_expansion`.
- Project health grade: `B`; traffic-light status `yellow`.
- Distance to next repair-count milestone: `medium`.
- Distance to self-maintaining claim: `far`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `batch058b_seed_discovery_wave_3_expansion`.

Self-maintaining wrapper function gap summary: candidate intake, provider capsule reuse, and generalized duplicate replay/count-gate automation remain partial or single-candidate. A self-maintaining wrapper should process every encountered bug into an auditable route or terminal state, but it should not claim it can fix every bug. Some bugs may be unrecoverable under current policy because they require forbidden evidence, unbounded providers, unavailable runtimes, or test mutation.

Workflow success is not equivalent to repair success. Provider/runtime recovery is not repair success. Partial improvement is not repair success. Repair count increments require duplicate clean replay and count gate. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.

Batch061 is the latest validation-path boundary. It officially ingests Batch060d and runs the duplicate clean replay/count gate for the Cloudpickle issue-derived source-only repair candidate.

Batch061 preserved the exact Batch060d patch and did not generate or modify a new patch. A fresh duplicate Cloudpickle workspace reproduced the pre-repair class-dict failure, applied the exact preserved patch, and passed the post-patch class-dict target, distutils-family checks, and original full target. The duplicate replay outcome is `duplicate_clean_replay_pass`; the count gate status is `PASS`.

Batch061 status:

- Batch060d official ingest: `PASS`.
- Pre-repair duplicate reproduction: `PASS`.
- Exact patch identity: `PASS`.
- Duplicate clean replay outcome: `duplicate_clean_replay_pass`.
- Issue-derived repair count: `2` -> `3`.
- Native external repair count preserved at `4`.
- Project health grade: `B`; traffic-light status `yellow`.
- Current protocol remains `v2.14`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `batch062_next_issue_repair_candidate_selection_or_wave3_expansion`.

Workflow success is not equivalent to repair success. Provider/runtime recovery is not repair success. A repair is counted only after duplicate clean replay and count-gate pass. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.

Batch060d is the latest validation-path boundary. It officially ingests Batch060c and runs the bounded Cloudpickle class-dict source-only patch gate. The remaining `class_dict_firstlineno` family freshly reproduced after provider/runtime preservation; a one-file source-only Cloudpickle patch was generated and applied only in the isolated Cloudpickle workspace; the minimal class-dict target and original full target passed after the patch.

Batch060d does not run duplicate clean replay, does not run count gates, does not increment repair counts, does not run full scoring, does not claim memory lift, and does not claim self-maintaining software. It installs AMDS Full Bug-Tree Closure Mode and an advisory project health review. The project health grade is advisory and does not constitute proof. Workflow success is not equivalent to repair success. Provider recovery is not repair success. Partial improvement is not repair success. Self-maintaining software remains false/not_demonstrated.

Batch060d status:

- Cloudpickle patch generated/applied status: `true / true`, isolated workspace only.
- Cloudpickle repair outcome classification: `source_only_patch_target_pass`.
- Source-only target-pass count: `1`.
- Batch061 duplicate replay candidate count: `1`.
- AMDS full bug-tree closure mode: `PASS`; maximum bug-tree depth `2`.
- Project health grade: `B`; traffic-light status `yellow`.
- Strongest capability gained: bounded provider-recovered source-only patch gate that produced a full-target pass candidate.
- Strongest recurring blocker: duplicate clean replay and count-gate evidence remain pending after target pass.
- Distance to next repair-count milestone: `near`, pending Batch061 duplicate clean replay and count gate.
- Distance to self-maintaining claim: `far`, because autonomous repeatable acquisition, repair, duplicate replay, and count evidence are not demonstrated.
- Structural-boundary/provider-capsule/isomorphic correctness status: `PASS` as audit/governance metadata only, not repair proof.
- Issue-derived repair count preserved at `2`.
- Native external repair count preserved at `4`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `batch061_duplicate_clean_replay_and_issue_repair_count_gate_wave_3`.

Batch060c is the latest validation-path boundary. It officially ingests Batch060b, executes Cloudpickle provider/runtime recovery, and adds reusable provider/runtime routing plus maintenance-memory ledgers.

Cloudpickle's `distutils` importability family is resolved by provider/runtime materialization: declared dev requirements alone left `distutils` unavailable in a fresh Python 3.13 venv, while `setuptools` materialization, justified by the buggy `setup.py`, made both `distutils` nodes pass. The full target remains failing only on the Python 3.13 `__firstlineno__` class-dictionary family.

Batch060c generates no patches, applies no patches, runs no duplicate replay, runs no count gate, and does not increment repair counts. Confirmed external native repair episodes remain `4`. Confirmed issue-derived repair episodes remain `2`. Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

Batch060c also adds a reusable Provider/Runtime Recovery Pattern Library, an Autonomic Bottleneck Routing Layer, and maintenance-memory ledgers. These are reusable subsystem improvements and future-routing recommendations, not repair success and not a self-maintaining software claim.

Confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.

Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.

Clean replication batch002 now attempts real external leads and preserves environment-resolution evidence before replay.

Batch060c candidate classifications:

- `cloudpickle_507_py313_typevar_distutils`: provider/runtime recovery classification `provider_runtime_recovery_succeeded_target_failure_materialized`; `distutils` family `distutils_family_resolved_by_provider`; `class_dict` family `class_dict_family_still_fails_interpreter_behavior`; future patch-license state `cloudpickle_patch_license_future_open_class_dict_single_family`.
- `audioread_144_py313_aifc_removed`: preserved as `partial_improvement_preserved_future_provider_backend_capsule`; no Audioread action ran in Batch060c.
- Source-only target-pass count: `0`.
- Batch061 duplicate replay candidate count: `0`.
- Reusable patterns learned: removed stdlib module, optional backend missing, test-runner provider mismatch, interpreter behavior change, compiled dependency boundary, network/model external-service boundary, and source-provider mixed surface.
- Recurring issue classes identified: `18`.
- Repo topology/duplication audit: `PASS`.
- Next allowed action: `batch060d_cloudpickle_class_dict_source_only_patch_gate`.

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
- Batch060 runs the bounded source-only patch gate, records one partial improvement, records zero source-only target passes, and preserves repair counts unchanged.
- Batch060b preserves the Audioread partial-improvement branch, decomposes Cloudpickle failure families, records zero Batch061 candidates, and routes future work to `batch060c_cloudpickle_provider_runtime_recovery`.
- Batch060c resolves the Cloudpickle `distutils` family through provider/runtime materialization, leaves the `class_dict_firstlineno` family for a future source-only patch gate, and installs reusable provider/runtime routing plus maintenance-memory records.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core tests/runtime -q
python scripts/validate_external_candidate_registry.py
python scripts/audit_batch060c_cloudpickle_provider_runtime_recovery.py
python scripts/audit_batch060b_cloudpickle_decomposition_audioread_provider_preservation.py
python scripts/audit_batch060_source_only_patch_gate_wave_3.py
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
- Reference release-output-directory is recorded only as an infrastructure pattern, not as a repair seed or repair evidence.
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
- Reference step-gating pattern: `infrastructure_pattern_only`.
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
- Reference provider-capsule lesson carried forward as infrastructure pattern only.
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
