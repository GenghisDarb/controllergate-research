# Agent Trace: Iota Misreport Candidate

Known correction event summary:

- Builder reported ControllerGate v1.6-iota as `20 / 20`.
- Critic verification found `16 / 20`.
- Packaged `decision_report.json` agreed with `16 / 20`.
- The corrected interpretation was that precision gates eliminated false-positive transfer but also suppressed useful memory, leaving productive lift, hidden-downstream lift, and corruption reduction at zero.

Evidence status:

- TODO_REQUIRED: original builder trace or transcript containing the `20 / 20` claim.
- TODO_REQUIRED: critic verification output showing `16 / 20`.
- TODO_REQUIRED: packaged `decision_report.json` path and SHA256.
- TODO_REQUIRED: rerun analyzer output.
- TODO_REQUIRED: `SHA256SUMS.txt` verification output.
- TODO_REQUIRED: iota package ZIP and notebook are missing from `controllergate_v1_7_alpha/artifacts_intake/iota/`.

Decision-time evidence and future outcome evidence must be separated before this episode can be normalized.
