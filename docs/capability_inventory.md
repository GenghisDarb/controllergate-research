# Capability inventory

Capabilities are tiered in `configs/controllergate_capability_catalog.json`. Runtime-wrapper entries introduced in Batch015 are scaffold-level unless deterministic fixture evidence is recorded.

- Artifact custody, registry-first provenance, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift prechecks, and rollback ledger controls have reproduced repository evidence.
- Runtime incident capture, execution boundary gateway, isolated repair sandbox, dependency drift chaperone, active AST excision probe, syntax micro-rollback, predictive degradation telemetry, compute budget safe-stop, simulated blue/green deployment, proof-to-action compiler, and lock-sequence registry are Batch015 scaffold capabilities.
- Target intent signature alignment and dependency-era chaperone checks are Batch016 diagnostic capabilities; they block patch admission when observed failure does not match issue intent.
- Dependency-Era Resolution, Thin Artifact Packaging, and Evidence Carry-Forward Manifest records are Batch017 diagnostic/custody capabilities.
- Structure-first compiler and future agentic admissibility compiler work remain roadmap-only.

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
