# Capability inventory

Capabilities are tiered in `configs/controllergate_capability_catalog.json`.

- Manual Dependency Lock Intake is present as a Batch018 gate and is blocked until the canonical JSON lock is supplied.
- Issue Timestamp Reconciliation is recorded for Darker issue #112 before dependency cutoff logic.
- Dependency-Era Resolution remains blocked because authoritative manual lock evidence is absent.
- Thin Artifact Packaging and Evidence Carry-Forward Manifest remain active custody capabilities.

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
