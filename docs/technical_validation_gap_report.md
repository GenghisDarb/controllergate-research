# Technical validation gap report

ControllerGate is not a technical validation release. Batch018 records a precise input gap: the Darker issue #112 issue-derived path needs a decision-time dependency lock before target-intent retry.

The system correctly blocks instead of accepting an unrelated precondition failure or unrestricted latest dependency resolution.

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
