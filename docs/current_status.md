# Current status

ControllerGate is a provenance-first software repair research harness. The current protocol remains `v2.13` / `minimal_forensic_context_lane`.

## Evidence boundary

- Confirmed external non-Ansible native repair episodes after official ingest: 3 (`py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`).
- Clean replication batch002 lead pool: loaded with 5 native-capable leads.
- Clean replication batch002 acquisition: real clone, checkout, environment resolution, collection, and replay paths are attempted.
- Clean replication batch002 repair generation: one additional native source-only repair officially ingested for `darker_non_ascii_drop_changes` with target validation PASS and duplicate clean replay 3/3.
- `darker_non_ascii_drop_changes` no-overreach evidence is target-file bounded only; broader robustness is not claimed.
- Matched-null status for `darker_stdin_filename`: both arms succeeded equivalently; preliminary single-candidate memory separation evidence is `false`.
- Clean replication batch003 status: officially ingested; 3 challenge candidates attempted, 0 verified, matched-null ensemble did not run, exact blocker `clean_replication_batch_003_no_verified_challenge_candidate`.
- Clean replication batch004 status: native-first dual-track challenge acquisition is implemented with issue-derived ephemeral reproduction harness fallback as a separate evidence class; 1 native lead is carried forward, 0 native candidates verified, 0 issue-derived candidates verified, exact blocker `batch004_no_native_or_issue_derived_challenge_candidate_verified`.
- The official Batch005 source-materialized artifact verified byte custody and source materialization, but the native target-node replay did not verify in that artifact. The corrected Batch005 workflow adds intended target-node selection, source-stack extraction, patchable source subset derivation, and no-patch taxonomy before any repair attempt.
- Clean replication Batch006 status: bounded fragment patch assembly is implemented for `darker_skip_glob_failing_test`, with coupled dependency interlock mapping, dual projection consistency checks, passive failure-memory weighting, and proof-chain custody. It blocks before patch bytes with `fragment_patch_plan_not_generated`.
- Full scoring: `NOT_RUN/disallowed`.
- Matched-null memory status: `undemonstrated_equal_performance`.
- Self-maintaining software: `false/not_demonstrated`.
- Technical validation release readiness: not claimed.

## Operational status

The repository has byte-custody checks, artifact hygiene, registry validation, current-protocol audits, a clean replication adapter, bounded repair generation, deterministic matched-null ensemble scaffolding, native-first dual-track challenge acquisition, issue-derived evidence-class separation, source-materialized native retry support, target-node semantic selection, source-stack extraction, bounded fragment patch assembly, and reusable workflow support. The next step is resolving the Batch006 source-facing precondition or recording a continued block. It remains a pre-alpha research archive until broader external replication and audited comparison evidence exist.

## Current operational gate status

- Implemented active gates: artifact byte custody, workspace transport integrity, registry validation, semantic failure signatures, candidate admission decisions, matched-null arm separation, duplicate clean replay, bounded exploration budget, environment normalization, context boundary pinning, claim-boundary audit, and release-readiness blocking.
- Partial gates: baseline registry snapshot standardization, structural navigation, active probe routing, issue-derived harness execution, issue text temporal guard, matched-null ensemble execution, failure-memory weighting, post-patch revalidation for blocked candidates, global-block exception research, and broader evidence-ledger standardization.
- Deferred gates: bounded micro-reversal and v3.0 readiness.
- Current evidence counts: confirmed external native repair episodes `3`; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.
