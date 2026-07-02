# ControllerGate

ControllerGate is a provenance-first software repair research harness. It is built around artifact byte custody, candidate provenance, replay discipline, source-only repair safety, registry validation, and explicit claim boundaries.

Current branch: `controllergate-v1.7-alpha-real-trace-pilot`

## Current status

- Current protocol remains `v2.13` / `minimal_forensic_context_lane`.
- Four external non-Ansible native source-only repair episodes are confirmed after the official Batch008 ingest boundary: `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.
- ControllerGate has strong artifact custody, registry validation, claim-boundary enforcement, transport integrity checks, clean-replication scaffolding, artifact hygiene, and real-lead acquisition attempts.
- v2.37 and post-v2.37 work introduced shared core gates, reusable workflow scaffolding, transport integrity, risk regulation, a clean protocol adapter, and native/issue-derived evidence class separation.
- Clean replication batch002 now attempts real external leads, resolves project environments before replay, and produced one additional native repair for `darker_non_ascii_drop_changes` with target validation PASS and duplicate clean replay 3/3.
- The `darker_non_ascii_drop_changes` no-overreach result is target-file bounded only; stronger robustness is not claimed.
- The `darker_stdin_filename` matched-null comparison had equal Arm A and Arm B repair success, so it adds a native repair episode but does not provide memory separation evidence.
- Clean replication batch003 implements a matched-null ensemble challenge protocol and is officially ingested. It found no verified challenge candidate, so the matched-null ensemble did not run; the correct blocker is `clean_replication_batch_003_no_verified_challenge_candidate`.
- Clean replication batch004 implements native-first dual-track challenge acquisition with issue-derived ephemeral reproduction harness fallback as a separate evidence class. It currently blocks because neither track verified a challenge candidate.
- The official Batch005 source-materialized artifact verified byte custody and source materialization, but did not verify the native target-node replay; the corrected Batch005 workflow adds intended target-node selection, source-stack extraction, patchable source subset derivation, and explicit no-patch taxonomy before any repair attempt.
- Batch006 adds bounded fragment patch assembly for the verified native challenge candidate. It records coupled dependency interlock mapping, dual projection consistency checks, passive failure-memory weighting, and a proof-chain lock, but blocks before patch bytes because the observed replay does not yet authorize a source-only fragment.
- Batch007 adds target-intent reachability and precondition resolution for the same verified native challenge candidate. It records formatter/dependency precondition evidence, trace-feedback alignment, iterative dual projection recheck, and an explicit completion decision; the candidate is retired under `target_precondition_unresolved` because the replay remains blocked before the intended import-sorting skip behavior.
- Batch008 corrects declared formatter precondition materialization by using a fresh ephemeral runtime workspace, installing declared formatter extras and declared target-test tooling, rerunning target-intent reachability, and validating one source-only patch for `darker_skip_glob_failing_test` with target validation, duplicate replay, and target-file no-overreach evidence.
- Batch009 patch-quarantined matched-null calibration is retrospective diagnostic work on the already repaired Batch008 candidate. It does not add another repair episode, does not establish prospective memory lift, and keeps successful Batch008 patch artifacts out of both comparison arms.
- Batch009 showed null ensemble failure under patch quarantine, but Arm A still had passive memory markers, no routing delta, and no generated patch; the matched-null score correctly remains `0.0`.
- Batch010 implements active status-code weighting, a High-Pass Source Ranking Filter, a Two-Candidate Selection Policy, and Strict Minimum-Delta Routing for the same already repaired candidate as retrospective calibration. It blocks with `active_memory_routing_delta_not_established` because the decision-time-safe status codes do not change source, context, or generation routing without using quarantined prior patch detail.
- Batch011 prospective memory challenge eligibility retires `darker_skip_glob_failing_test` from further memory-lift attempts, reviews bounded fresh leads from the existing clean replication lead pool, and blocks with `batch011_no_fresh_candidate_verified`; no memory-enabled arm, null ensemble, patch generation, or repair-only fallback is authorized.
- Batch012 targeted prospective seed intake is now the next gate. If `external_seeds_pending/targeted_prospective_seed_batch012.json` is absent or invalid, the lane blocks with `targeted_prospective_seed_missing_or_invalid` before native verification, issue-derived fallback, repair-only fallback, or matched-null comparison.
- Batch013 acquisition locks add source-commit environment locking, target command manifest requirements, fresh workspace purity checks, baseline registry drift precheck, gate-chain binding, tracked seed enforcement, active context filtering records, and frozen routing-score policy. With no tracked seed at `external_seeds_pending/targeted_prospective_seed_batch013.json`, the lane blocks with `targeted_prospective_seed_missing_or_invalid_after_locks_ready` before source checkout, replay, issue-derived fallback, repair-only fallback, or matched-null comparison.
- Batch014 consumes a tracked targeted seed for Darker issue #112 as issue-derived evidence. It requires seed schema harmonization, a redacted issue snapshot firewall, dataset lead firewall, source-commit selection before replay, the Batch013 five-lock stack, and issue-derived evidence separation. Issue-derived success cannot increment native repair counts or support native memory-separation claims.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift on external real bugs is not demonstrated; the prospective memory-lift status remains `not_demonstrated`.
- Self-maintaining software is not demonstrated.
- BugsInPy remains globally blocked except for future byte-identical exception research.
- This repository is currently suitable as a pre-alpha research archive, not a technical validation release.

## What ControllerGate can do now

- Verify manually supplied workflow artifacts before ingesting output evidence.
- Preserve byte-level manifests and detect manifest drift.
- Validate the external candidate registry and repair episode registry.
- Separate native repair evidence, issue-derived evidence, diagnostic evidence, documentation evidence, and infrastructure evidence.
- Run the current protocol audit and dry-run without promoting later lanes to current.
- Run clean replication acquisition over explicit external leads.
- Create isolated candidate workspaces and attempt structured environment resolution before collection and replay.
- Generate bounded source-only repair patches from verified native candidate context only after target-intent reachability and trace-feedback alignment gates pass, then require patch safety, target validation, and duplicate replay before recording a repair success.
- Define deterministic matched-null ensemble policies for future challenge candidates, including memory-enabled and memory-disabled arm separation, fair null perturbations, and explicit score boundaries.
- Record prospective memory-challenge eligibility gates that require a fresh candidate, preregistered arms, legal alternative routes, mappable status features, strict routing delta, and patch artifact quarantine before any memory-lift claim.

## Current limits

ControllerGate does not currently claim autonomous repair, full benchmark scoring, memory-lift evidence, self-maintaining software, or technical validation readiness. Issue-derived harnesses do not count as native external repairs. Historical lanes remain auditable evidence, but new replication work should use the clean replication protocol and reusable workflow where possible.

The next technical objective after Batch014 is to resolve the issue-derived replay boundary honestly or provide a new reviewed tracked seed. The matched-null rules must be registered before any successful patch exists for a future native candidate, native and issue-derived evidence must remain separate, and prior repaired candidates must not be reused for memory-lift claims.

## Current operational gate status

- Implemented active gates: artifact byte custody, workspace transport integrity, external candidate registry validation, semantic failure signatures, target-node admission decisions, target-intent reachability, formatter/dependency precondition resolution, trace-feedback alignment, iterative dual projection recheck, matched-null arm separation, duplicate clean replay, bounded exploration budget, execution environment normalization, context boundary pinning, public claim boundary audit, public release readiness blocking, status-code weighting policy, High-Pass Source Ranking Filter, Curvature-Based Candidate Selection, Two-Winner Source Selection, Strict Minimum-Delta Routing, source-commit environment locking, target command manifest checks, fresh workspace purity checks, baseline registry drift precheck, rollback block ledger, Batch013 gate-chain binding, tracked seed enforcement, routing-score heuristic freeze, five-lock routing cross-gate checks, seed schema harmonization, redacted issue snapshot firewall, dataset lead firewall, and issue-derived evidence-class separation for Batch014.
- Partial gates: structural navigation, active probe routing, dependency projection reuse, interlock invariant mapping reuse, Targeted Prospective Seed Intake, Native Target Test Verification, issue-derived harness handling, issue text temporal guard, matched-null ensemble execution, Active Failure-Memory Routing, Prospective Memory Challenge, prospective memory eligibility, failure-memory weighting, no-overreach validation for non-successful candidates, global-block exception research, evidence-ledger sealing, active context filtering, routing-score feature vectors, basin stability checks, routing memory diagnostics, fragment planning, and null ensemble routing fairness.
- Deferred gates: bounded micro-reversal and v3.0 readiness.
- Current evidence counts: confirmed external native repair episodes `4` after official Batch008 ingest; confirmed issue-derived repair episodes `0`; accepted matched-null comparisons `1` with equal performance; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core -q
python scripts/validate_external_candidate_registry.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

## Manual artifact boundary

Workflow artifacts are ingested only after manual download and local ZIP verification. The repository records local artifact identity and ingests non-archive output files only. Codex must not bless an artifact it fetched for itself.

## Documentation

- Current status: `docs/current_status.md`
- Capability inventory: `docs/capability_inventory.md`
- Evidence model: `docs/evidence_model.md`
- Claim boundaries: `docs/claim_boundaries.md`
- Replication protocol: `docs/replication_protocol.md`
- Public readiness: `docs/public_release_readiness.md`
- Technical validation gap report: `docs/technical_validation_gap_report.md`
- Operational gate matrix: `docs/operational_gate_matrix.md`
