# Operational gate matrix

The public terminology for ControllerGate is expressed as neutral operational gates. Each gate has an evidence class, a claim boundary, and an audit expectation.

See `configs/operational_gate_matrix.json` for the machine-readable matrix.

## Current operational gate status

- Implemented active gates: artifact byte custody, workspace transport integrity, registry validation, semantic failure signatures, candidate admission decisions, matched-null arm separation, duplicate clean replay, bounded exploration budget, environment normalization, context boundary pinning, public claim boundary audit, and release-readiness blocking.
- Implemented active Batch006 gates: bounded fragment patch assembly policy, coupled dependency interlock mapping, dual projection consistency checking, and blocked-lane proof-chain custody.
- Implemented active Batch007 gates: target-intent reachability, formatter/dependency precondition resolution, trace-feedback alignment, iterative dual projection recheck, and explicit completion decision enforcement.
- Implemented active Batch008 gates: declared formatter precondition materialization, target replay after declared extras, bounded source-only fragment assembly, target validation, duplicate replay, and target-file no-overreach validation.
- Implemented active Batch009 gates: patch artifact quarantine, context access denylist, retrospective matched-null calibration, and prospective memory-lift claim boundary.
- Implemented active Batch010 gates: Status-Code Weighting, High-Pass Source Ranking Filter, Two-Candidate Selection Policy, and Strict Minimum-Delta Routing.
- Implemented active Batch011 gates: Curvature-Based Candidate Selection, Two-Winner Source Selection, retired-candidate enforcement, and strict no-run behavior when no fresh candidate verifies.
- Implemented partial Batch012 gates: Targeted Prospective Seed Intake, Native Target Test Verification ordering, issue-derived fallback separation, and prospective memory eligibility blocking when no reviewed seed is present.
- Implemented active Batch013 gates: source-commit environment lock, target command manifest, fresh workspace purity, baseline registry drift precheck, rollback block ledger, gate-chain binding, tracked seed enforcement, routing-score freeze, and five-lock routing cross-gate checks.
- Implemented partial Batch013 gates: active context filtering, routing-score feature vectors, basin stability checks, routing memory diagnostics, fragment planning, and null ensemble routing fairness; all remain blocked before candidate-specific execution until a tracked reviewed seed is supplied.
- Partial gates: structural navigation, active probe routing, Targeted Prospective Seed Intake, Native Target Test Verification, issue-derived harness execution, issue text temporal guard, matched-null ensemble execution, Active Failure-Memory Routing, Prospective Memory Challenge, prospective memory eligibility, failure-memory weighting, post-patch revalidation for blocked candidates, global-block exception research, and broader evidence-ledger standardization.
- Deferred gates: bounded micro-reversal and v3.0 readiness.
- Current evidence counts: confirmed external native repair episodes `4` after official Batch008 ingest; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.

The NotebookLM advice traceability matrix cross-references these operational gates in `configs/notebooklm_advice_traceability_matrix.json` and records carry-forward blockers for partial or deferred gates.
