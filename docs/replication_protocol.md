# Replication protocol

Replication requires manual artifact custody, registry validation, source-commit environment locks, target command manifests, fresh workspace purity, baseline registry drift checks, rollback records, replay, validation, duplicate replay, and claim-boundary review.

Batch018 adds issue timestamp reconciliation and canonical manual dependency lock intake before dependency-era target-intent retry.

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
