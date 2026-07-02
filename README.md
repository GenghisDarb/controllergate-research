# ControllerGate

ControllerGate is a provenance-first software repair research harness and evidence-bound repair validation kernel for audited software-change candidates. Current protocol remains `v2.13`.

ControllerGate remains a pre-alpha research archive. Clean replication batch002 now attempts real external leads, and confirmed external native repair episodes include `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.

Batch018 is the latest boundary. It officially preserves the Batch017 thin artifact, reconciles Darker issue #112 timestamp evidence, and stops at `manual_dependency_lock_absent` because no canonical decision-time dependency lock JSON is present.

Memory lift on external real bugs is not demonstrated. Self-maintaining software is not demonstrated.

## What ControllerGate is

ControllerGate is an evidence-bound repair validation kernel for software-change candidates. It is designed to verify provenance, replay, patch safety, rollback readiness, and claim boundaries before accepting repair evidence.

## What ControllerGate is not

ControllerGate is not production-ready, not a full scoring result, not a full memory-lift result, not fully self-maintaining software, and not an absolute reliability guarantee.

## Current operational gate status

- Batch017 blocked because no decision-time dependency lock was available.
- Batch018 reconciles the Darker issue #112 timestamp and requires the canonical manual dependency lock JSON before retrying target intent.
- A plain requirements.txt is support evidence only; it is not authoritative unless normalized into the canonical JSON evidence schema.
- If historical environment reconstruction cannot be proven safely, ControllerGate blocks rather than patches.
- Thin artifact packaging remains active to keep manually handled artifacts small.
- Confirmed native repair episode count remains `4`.
- Confirmed issue-derived repair episode count remains `0`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Hallucination elimination is not claimed.
- Absolute uncrashability is not claimed.
- Production runtime readiness is not claimed.

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

## Forbidden claims

- Hallucination elimination.
- Absolute uncrashability.
- Fully self-maintaining software.
- Production-ready runtime wrapper.
- Full scoring.
- Full memory lift.
- Universal bug repair.
- Sector deployment readiness.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core tests/runtime -q
python scripts/validate_external_candidate_registry.py
python scripts/audit_post_v2_37_hardening_and_batch002.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```
