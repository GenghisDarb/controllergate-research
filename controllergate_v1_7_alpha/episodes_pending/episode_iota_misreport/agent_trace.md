# Agent Trace: Iota Misreport Candidate

Known correction event summary:

- Builder reported ControllerGate v1.6-iota as `20 / 20`.
- Critic verification found `16 / 20`.
- Packaged `decision_report.json` agreed with `16 / 20`.
- The corrected interpretation was that precision gates eliminated false-positive transfer but also suppressed useful memory, leaving productive lift, hidden-downstream lift, and corruption reduction at zero.

Evidence status:

- TODO_REQUIRED: original builder trace or transcript containing the `20 / 20` claim.
- TODO_REQUIRED: critic verification output showing `16 / 20`.
- Package evidence present: packaged `decision_report.json` records `16 / 20`.
- Analyzer rerun performed: `16 / 20`.
- SHA256 manifest verification performed: 19 entries checked, 0 mismatches.
- Package ZIP and extracted notebook are present in `controllergate_v1_7_alpha/artifacts_intake/iota/`.

Decision-time claim:

- Builder reportedly claimed v1.6-iota passed `20 / 20`.

Outcome-only correction evidence:

- Packaged decision report records `16 / 20`.
- Local analyzer rerun over packaged outputs records `16 / 20`.
- Failed criteria were hidden downstream lift, corruption reduction, memory helped more than hurt, and productive recommendation precision.

Key lesson:

- Precision gates eliminated false-positive transfer but over-abstained; useful memory transfer disappeared.

Decision-time evidence and future outcome evidence must be separated before this episode can be normalized.
