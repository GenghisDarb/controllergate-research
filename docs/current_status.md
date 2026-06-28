# Current status

ControllerGate is a provenance-first software repair research harness. The current protocol remains `v2.13` / `minimal_forensic_context_lane`.

## Evidence boundary

- Confirmed external non-Ansible repair episodes: 2 (`py_bugger_issue_65`, `darker_non_ascii_drop_changes`).
- Clean replication batch002 lead pool: loaded with 5 native-capable leads.
- Clean replication batch002 acquisition: real clone, checkout, environment resolution, collection, and replay paths are attempted.
- Clean replication batch002 repair generation: one additional native source-only repair validated for `darker_non_ascii_drop_changes` with duplicate clean replay 3/3.
- Full scoring: `NOT_RUN/disallowed`.
- Memory lift: `undemonstrated`.
- Self-maintaining software: `false/not_demonstrated`.
- Technical validation release readiness: not claimed.

## Operational status

The repository has byte-custody checks, artifact hygiene, registry validation, current-protocol audits, a clean replication adapter, bounded repair generation, and reusable workflow scaffolding. It remains a pre-alpha research archive until broader external replication and audited comparison evidence exist.
