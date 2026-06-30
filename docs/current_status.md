# Current status

ControllerGate is a provenance-first software repair research harness. The current protocol remains `v2.13` / `minimal_forensic_context_lane`.

## Evidence boundary

- Confirmed external non-Ansible native repair episodes after the Batch008 implementation boundary: 4 (`py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, `darker_skip_glob_failing_test`). The Batch008 artifact still requires manual download and official ingest before that artifact boundary is complete.
- Clean replication batch002 lead pool: loaded with 5 native-capable leads.
- Clean replication batch002 acquisition: real clone, checkout, environment resolution, collection, and replay paths are attempted.
- Clean replication batch002 repair generation: one additional native source-only repair officially ingested for `darker_non_ascii_drop_changes` with target validation PASS and duplicate clean replay 3/3.
- `darker_non_ascii_drop_changes` no-overreach evidence is target-file bounded only; broader robustness is not claimed.
- Matched-null status for `darker_stdin_filename`: both arms succeeded equivalently; preliminary single-candidate memory separation evidence is `false`.
- Clean replication batch003 status: officially ingested; 3 challenge candidates attempted, 0 verified, matched-null ensemble did not run, exact blocker `clean_replication_batch_003_no_verified_challenge_candidate`.
- Clean replication batch004 status: native-first dual-track challenge acquisition is implemented with issue-derived ephemeral reproduction harness fallback as a separate evidence class; 1 native lead is carried forward, 0 native candidates verified, 0 issue-derived candidates verified, exact blocker `batch004_no_native_or_issue_derived_challenge_candidate_verified`.
- The official Batch005 source-materialized artifact verified byte custody and source materialization, but the native target-node replay did not verify in that artifact. The corrected Batch005 workflow adds intended target-node selection, source-stack extraction, patchable source subset derivation, and no-patch taxonomy before any repair attempt.
- Clean replication Batch006 status: bounded fragment patch assembly is implemented for `darker_skip_glob_failing_test`, with coupled dependency interlock mapping, dual projection consistency checks, passive failure-memory weighting, and proof-chain custody. It blocks before patch bytes with `fragment_patch_plan_not_generated`.
- Clean replication Batch007 status: target-intent reachability and precondition resolution are implemented for `darker_skip_glob_failing_test`, with trace-feedback alignment, iterative dual projection recheck, and an explicit completion decision ladder. The candidate is retired with `target_precondition_unresolved` because the replay remains blocked before the intended import-sorting skip behavior.
- Clean replication Batch008 status: declared formatter precondition materialization is corrected for `darker_skip_glob_failing_test` by materializing a fresh ephemeral runtime workspace, installing declared formatter extras and declared target-test tooling, rerunning target-intent reachability, and validating one source-only patch with target validation, duplicate replay, and target-file no-overreach evidence.
- Full scoring: `NOT_RUN/disallowed`.
- Matched-null memory status: `undemonstrated_equal_performance`.
- Self-maintaining software: `false/not_demonstrated`.
- Technical validation release readiness: not claimed.

## Operational status

The repository has byte-custody checks, artifact hygiene, registry validation, current-protocol audits, a clean replication adapter, bounded repair generation, deterministic matched-null ensemble scaffolding, native-first dual-track challenge acquisition, issue-derived evidence-class separation, source-materialized native retry support, target-node semantic selection, source-stack extraction, bounded fragment patch assembly, target-intent reachability, trace-feedback alignment, declared precondition materialization, and reusable workflow support. Batch008 adds a bounded source-only repair endpoint for the previously blocked challenge candidate, but it remains a pre-alpha research archive until broader external replication and audited comparison evidence exist.

## Current operational gate status

- Implemented active gates: artifact byte custody, workspace transport integrity, registry validation, semantic failure signatures, candidate admission decisions, target-intent reachability, formatter/dependency precondition resolution, trace-feedback alignment, iterative dual projection recheck, matched-null arm separation, duplicate clean replay, bounded exploration budget, environment normalization, context boundary pinning, claim-boundary audit, and release-readiness blocking.
- Partial gates: baseline registry snapshot standardization, structural navigation, active probe routing, issue-derived harness execution, issue text temporal guard, matched-null ensemble execution, failure-memory weighting, post-patch revalidation for blocked candidates, global-block exception research, and broader evidence-ledger standardization.
- Deferred gates: bounded micro-reversal and v3.0 readiness.
- Current evidence counts: confirmed external native repair episodes `4` after Batch008 implementation evidence; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.
