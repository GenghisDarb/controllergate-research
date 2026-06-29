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
- Full scoring: `NOT_RUN/disallowed`.
- Matched-null memory status: `undemonstrated_equal_performance`.
- Self-maintaining software: `false/not_demonstrated`.
- Technical validation release readiness: not claimed.

## Operational status

The repository has byte-custody checks, artifact hygiene, registry validation, current-protocol audits, a clean replication adapter, bounded repair generation, deterministic matched-null ensemble scaffolding, and reusable workflow support. The next step is native-first dual-track challenge acquisition with issue-derived evidence kept separate. It remains a pre-alpha research archive until broader external replication and audited comparison evidence exist.
