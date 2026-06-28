# ControllerGate

ControllerGate is a provenance-first software repair research harness. It focuses on byte custody, artifact verification, candidate provenance, replay discipline, source-only patch safety, and explicit claim boundaries.

Current branch: `controllergate-v1.7-alpha-real-trace-pilot`

## Current protocol

The current protocol remains `v2.13` / `minimal_forensic_context_lane`.

- Current config: `configs/controllergate_current.yaml`
- Current summary: `outputs/current/current_protocol_summary.json`
- Current protocol docs: `docs/current_protocol.md`

Historical versioned lanes are preserved as evidence history. They are not the current interface for new work.

## Current evidence boundary

- One confirmed external non-Ansible repair episode is recorded so far.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift is not demonstrated on external real bugs.
- Self-maintaining software is not demonstrated.
- Public technical-validation readiness is not claimed.

## v2.37 transition

v2.37 introduces a maintained framework layer:

- shared core gate helpers under `controllergate/core/`,
- unit tests under `tests/core/`,
- a reusable workflow at `.github/workflows/controllergate_reusable_lane.yml`,
- a clean replication protocol adapter,
- a consolidated state-file format,
- public documentation for architecture, claims, replication, and readiness.

The clean replication batch target is to support future attempts at 2–4 additional external repair episodes without creating a new one-purpose lane for every blocker. If no manually reviewed seed drafts are present, the batch blocks honestly instead of fabricating candidates.

## v2.36 resolved-commit replay and candidate admission status

v2.36 is officially ingested as a blocked candidate-admission lane. It verified the prior artifact boundary, preserved the current protocol at v2.13, attempted the allowed candidate-admission path, and blocked with `blocked_no_native_or_issue_derived_candidate2_seed_acquired`.

## v2.35 automated candidate #2 acquisition status

v2.35 is preserved as historical acquisition evidence. It did not acquire a verified second candidate, did not run full scoring, did not demonstrate memory lift, and did not change the current protocol.

## Basic local checks

```bash
python scripts/byte_custody_preflight.py
python -m pytest tests/core -q
python scripts/validate_external_candidate_registry.py
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

## Manual artifact boundary

Workflow artifacts are ingested only after manual download and local ZIP verification. The repository records local artifact identity and ingests non-archive outputs only. Codex must not bless an artifact it fetched for itself.

## Documentation

- Architecture: `docs/architecture.md`
- Getting started: `docs/getting_started.md`
- Claim boundaries: `docs/claim_boundaries.md`
- Clean replication protocol: `docs/replication_protocol.md`
- Consolidated state format: `docs/consolidated_state_format.md`
- Public readiness: `docs/public_release_readiness.md`
