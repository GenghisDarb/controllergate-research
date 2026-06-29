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
- Batch005 corrects Batch004 by materializing the source tree in an ephemeral workspace before native AST/node discovery and by checking targeted issue-derived seed intake before bounded issue discovery fallback.
- Full scoring: `NOT_RUN/disallowed`.
- Matched-null memory status: `undemonstrated_equal_performance`.
- Self-maintaining software: `false/not_demonstrated`.
- Technical validation release readiness: not claimed.

## Operational status

The repository has byte-custody checks, artifact hygiene, registry validation, current-protocol audits, a clean replication adapter, bounded repair generation, deterministic matched-null ensemble scaffolding, native-first dual-track challenge acquisition, issue-derived evidence-class separation, source-materialized native retry support, and reusable workflow support. The next step is a verified native challenge candidate, or an explicitly separated issue-derived feasibility candidate if native acquisition remains blocked. It remains a pre-alpha research archive until broader external replication and audited comparison evidence exist.
