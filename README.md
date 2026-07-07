# ControllerGate

ControllerGate is a provenance-first software repair research harness and evidence-bound repair validation kernel for audited software-change candidates. Current protocol remains `v2.13`.

ControllerGate remains a pre-alpha research archive. Clean replication batch002 now attempts real external leads, and confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.

Batch019 is the latest boundary. Status: `PASS_WITH_BATCH019_ACTIVE_SEARCH_GEOMETRY`; exact blocker: `manual_dependency_lock_available_for_batch020_or_later`.

Full scoring remains `NOT_RUN/disallowed`.

Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.

## Current operational gate status

- Batch018 official artifact evidence remains blocked at `manual_dependency_lock_absent`.
- Batch019 adds Active Search-Space Geometry as a neutral probe-selection scaffold.
- Active Search-Space Geometry can prioritize probes and candidates, but it cannot validate repairs.
- Geometry maps are not substitutes for commit verification, environment locks, replay, validation, null comparison, duplicate replay, no-overreach validation, or SHA custody.
- Single-system search geometry and coupled-interlock extension remain separate.
- Coupled-interlock extension is diagnostic until interlock invariants are computed.
- Darker issue #112 repair execution remains blocked in Batch019; the post-Batch018 manual lock is watch-only for Batch020 or later.
- Native repair episode count remains `4`.
- Issue-derived repair episode count remains `0`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Hallucination elimination is not claimed.
- Absolute uncrashability is not claimed.
- Production runtime readiness is not claimed.

## What ControllerGate is

ControllerGate is an evidence-bound repair validation kernel for software-change candidates. It verifies provenance, replay, patch safety, rollback readiness, and claim boundaries before accepting repair evidence.

## What ControllerGate is not

ControllerGate is not production-ready, not a full scoring result, not a full memory-lift result, not fully self-maintaining software, and not an absolute reliability guarantee.

## Claim Tier System

ControllerGate uses explicit claim tiers so public claims remain tied to repository evidence.

## Capability Catalog

The capability catalog is stored in `configs/controllergate_capability_catalog.json` and summarized in `docs/capability_inventory.md`.

## Skeptic's Acceptance Checklist

The checklist in `docs/skeptics_acceptance_checklist.md` requires registry-first provenance, decision-time separation, SHA256 custody, fresh workspace purity, validation, duplicate replay, no-overreach validation, rollback records, and claim tiers.

## Runtime-wrapper roadmap

Batch015 introduced scaffold modules for audited runtime control. These remain scaffold evidence only unless deterministic fixture evidence is recorded.

## Safe public claims

- Evidence-bound repair validation kernel.
- Proof-gated patch admission and quarantine.
- Runtime-wrapper scaffold for audited local fixtures.
- Claim-tiered capability catalog.
- Active probe-selection scaffold.

## Forbidden claims

- Hallucination elimination.
- Absolute uncrashability.
- Fully self-maintaining software.
- Production-ready runtime wrapper.
- Full scoring.
- Full memory lift.
- Universal bug repair.
- Sector deployment readiness.
- Geometry-proves-repair.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core tests/runtime -q
python scripts/validate_external_candidate_registry.py
python scripts/audit_post_v2_37_hardening_and_batch002.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

### Batch047 bounded environment probe execution

- Batch047 status: `PASS_WITH_BATCH047_TOT_BULB_PROBE_EXECUTION_RECORDED`.
- Batch046 locator authorization is preserved and a source registry now gates future probe execution.
- Bounded non-mutating probe records: executed `34`, blocked `0`, not run `22`.
- Candidate inventory remains `0`; repair generation, target replay, duplicate replay, and protocol promotion remain separate future steps.
- Native external repair episodes remain `4`; issue-derived repair episodes remain `1`; current protocol remains `v2.13`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift, production readiness, and self-maintaining software remain not demonstrated.
