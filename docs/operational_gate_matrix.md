# Operational gate matrix

The public terminology for ControllerGate is expressed as neutral operational gates. Each gate has an evidence class, a claim boundary, and an audit expectation.

See `configs/operational_gate_matrix.json` for the machine-readable matrix.

## Current operational gate status

- Implemented active gates: artifact byte custody, workspace transport integrity, registry validation, semantic failure signatures, candidate admission decisions, matched-null arm separation, duplicate clean replay, bounded exploration budget, environment normalization, context boundary pinning, public claim boundary audit, and release-readiness blocking.
- Implemented active Batch006 gates: bounded fragment patch assembly policy, coupled dependency interlock mapping, dual projection consistency checking, and blocked-lane proof-chain custody.
- Implemented active Batch007 gates: target-intent reachability, formatter/dependency precondition resolution, trace-feedback alignment, iterative dual projection recheck, and explicit completion decision enforcement.
- Implemented active Batch008 gates: declared formatter precondition materialization, target replay after declared extras, bounded source-only fragment assembly, target validation, duplicate replay, and target-file no-overreach validation.
- Implemented active Batch009 gates: patch artifact quarantine, context access denylist, retrospective matched-null calibration, and prospective memory-lift claim boundary.
- Partial gates: baseline registry snapshot standardization, structural navigation, active probe routing, issue-derived harness execution, issue text temporal guard, matched-null ensemble execution, failure-memory weighting, post-patch revalidation for blocked candidates, global-block exception research, and broader evidence-ledger standardization.
- Deferred gates: bounded micro-reversal and v3.0 readiness.
- Current evidence counts: confirmed external native repair episodes `4` after official Batch008 ingest; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.

The NotebookLM advice traceability matrix cross-references these operational gates in `configs/notebooklm_advice_traceability_matrix.json` and records carry-forward blockers for partial or deferred gates.
