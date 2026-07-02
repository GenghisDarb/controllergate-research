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

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core tests/runtime -q
python scripts/validate_external_candidate_registry.py
python scripts/audit_post_v2_37_hardening_and_batch002.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```
