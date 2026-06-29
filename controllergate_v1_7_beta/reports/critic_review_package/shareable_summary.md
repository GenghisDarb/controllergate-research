# ControllerGate shareable research summary

ControllerGate is a provenance-first software repair research harness. It emphasizes artifact byte custody, decision-time-safe candidate evidence, replay discipline, source-only patch safety, and explicit claim boundaries.

## Current evidence boundary

- Current protocol: `v2.13` / `minimal_forensic_context_lane`.
- Confirmed external non-Ansible native repair episodes after official ingest: `3` (`py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`).
- Full scoring: `NOT_RUN/disallowed`.
- Memory lift on external real bugs: `undemonstrated_equal_performance`.
- Self-maintaining software: `false/not_demonstrated`.
- Public technical-validation readiness: not claimed.

## v2.35 Automated Candidate #2 Acquisition Status

v2.35 is preserved as historical acquisition evidence. It ran a bounded candidate #2 acquisition sprint but did not acquire a verified second seed.

- Verified seed acquired: `false`.
- Repositories attempted: `5`.
- Candidate commits attempted: `17`.
- Exact blocker: `blocked_no_verified_candidate2_seed_acquired`.
- Matched-null experiment attempted: `false`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

## v2.36 Resolved-Commit Replay and Candidate Admission Status

v2.36 is officially ingested as a blocked candidate-admission lane. It preserves the v2.35 boundary, verifies the v2.36 artifact, and records the architecture-debt carry-forward that led into v2.37.

- Native replay candidate acquired: `false`.
- Issue-derived fallback attempted: `true`.
- Issue-derived candidate acquired: `false`.
- Exact blocker: `blocked_no_native_or_issue_derived_candidate2_seed_acquired`.
- Structural Navigation Map: `implemented_active_v2_36`.
- Active Probe Router: `implemented_active_v2_36`.
- Coupled Dependency Projection Map: `implemented_active_v2_36`.
- Interlock Invariant Map: `implemented_active_v2_36`.
- Proof Coordinate Ledger: `PASS`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

## v2.37 Core Consolidation and Clean Replication Protocol

v2.37 transitions ControllerGate from a sequence of one-purpose lanes toward a maintained research framework.

- Shared core gate helpers: implemented under `controllergate/core/`.
- Core unit tests: implemented under `tests/core/`.
- Reusable workflow: `.github/workflows/controllergate_reusable_lane.yml`.
- Clean replication protocol adapter: implemented.
- Consolidated state format: implemented.
- Clean replication batch 001: blocked honestly because no manually reviewed seed draft is present.
- Additional external repairs acquired in v2.37: `0`.
- Public readiness status: `pre_alpha_research_archive_ready`, not technical-validation ready.
- Current protocol remains `v2.13`.

## Post-v2.37 Hardening

Post-v2.37 hardening adds transport integrity, bounded exploration budget, context-boundary, environment-normalization, evidence-class separation, risk regulation, clean artifact packaging, real-lead acquisition, and structured environment resolution gates.

- Clean replication batch 002 keeps native and issue-derived counts separate.
- Batch 002 uses an explicit lead pool with 5 native-capable leads.
- Batch 002 performs clone, commit resolution, checkout, environment resolution, collection, and replay probes.
- Batch 002 produced one additional successful native external repair: `darker_non_ascii_drop_changes`.
- The repair passed source-only patch safety, target validation, and duplicate clean replay 3/3.
- The no-overreach evidence for `darker_non_ascii_drop_changes` is target-file bounded only; stronger robustness is not claimed.
- The matched-null official ingest records a successful `darker_stdin_filename` native repair in both arms. Because both arms succeeded equivalently, preliminary memory separation evidence remains false.
- Batch003 deterministic matched-null ensemble calibration is officially ingested. It attempted 3 challenge candidates, verified 0, did not run the ensemble, and records `clean_replication_batch_003_no_verified_challenge_candidate`.
- The next objective is dual-track challenge acquisition: native candidates first, issue-derived ephemeral reproduction harnesses only as separate lower-confidence evidence.
- BugsInPy remains globally blocked for active use.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `undemonstrated_equal_performance`.
- Self-maintaining software remains `false/not_demonstrated`.

## Safest next step

After the batch003 workflow completes, manually download the memory-challenge artifact and ingest it through the same byte-custody boundary.
