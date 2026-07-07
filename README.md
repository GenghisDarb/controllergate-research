# ControllerGate

ControllerGate is a proof-gated runtime and compiler layer for safe AI software repair.

It remains a provenance-first software repair research harness with a conservative pre-alpha research archive boundary.

It turns AI-generated fixes into auditable, sandboxed, rollback-safe software-change candidates, blocking unverified patches before they can contaminate accepted software state.

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

Batch014 remains the latest validation-path boundary: the Darker issue #112 seed was admitted only as issue-derived evidence, the redacted issue snapshot and acquisition locks passed, and the issue-derived harness blocked with `issue_derived_harness_intent_mismatch`. Native repair count remains `4`; issue-derived repair count remains `0`.

Confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.

Clean replication batch002 now attempts real external leads and preserves environment-resolution evidence before replay.

Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.

Batch015 adds scaffolded runtime controls and claim documentation. It does not add a repair episode.

Batch016 addresses target-intent alignment for Darker issue #112. The previous issue-derived harness failed because the observed config-loading TypeError did not match the issue intent. ControllerGate correctly blocked instead of accepting an unrelated failure.

Batch017 attempts decision-time-safe dependency-era resolution for that pre-target failure. If the historical environment cannot be reconstructed from admissible evidence, ControllerGate blocks rather than patching. Batch017 also starts thin artifact packaging: prior evidence is preserved by artifact SHA, ingest commit, manifest hash, and lineage index instead of recursively repackaging every prior batch.

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

- Current protocol remains `v2.13`.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Batch015 adds a runtime-wrapper scaffold, lock-sequence registry, claim tiers, and product-positioning boundaries without live deployment.
- Batch016 addresses target-intent alignment for the issue-derived Darker seed and safe-stops before repair because the observed failure is pre-target/precondition.
- Batch017 attempts decision-time dependency-era resolution and starts thin artifact packaging; it safe-stops if no decision-time dependency lock can be proven.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core tests/runtime -q
python scripts/validate_external_candidate_registry.py
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
