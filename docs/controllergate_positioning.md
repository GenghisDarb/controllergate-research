# ControllerGate positioning

Preferred precise claim: ControllerGate turns proposed fixes into auditable, sandboxed, rollback-safe software-change candidates and blocks unverified changes before accepted state is contaminated.

Batch018 preserves that boundary by refusing to retry target-intent alignment without a decision-time dependency lock.

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
