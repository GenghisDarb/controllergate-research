# Agent Trace: Pi Misreport Candidate

Known correction event summary:

- Builder reported ControllerGate v1.6-pi as `28 / 28`.
- Critic verification found `27 / 28`.
- The failed criterion was counter-strategy recovery lift.
- Corrected counter-strategy recovery lift was `-0.075`, not positive.

Evidence status:

- TODO_REQUIRED: original builder trace or transcript containing the `28 / 28` claim.
- TODO_REQUIRED: critic verification output showing `27 / 28`.
- Package evidence present: packaged `decision_report.json` records `27 / 28`.
- Package runner rerun performed with exit code `0`.
- Packaged-output analyzer rerun performed: `27 / 28`.
- Rerun-output analyzer performed: `27 / 28`.
- SHA256 manifest verification performed: 24 entries checked, 0 mismatches.
- Package ZIP and extracted notebook are present in `controllergate_v1_7_alpha/artifacts_intake/pi/`.

Decision-time claim:

- Builder reportedly claimed v1.6-pi passed `28 / 28`.

Outcome-only correction evidence:

- Packaged decision report records `27 / 28`.
- Local runner plus analyzer rerun records `27 / 28`.
- Failed criterion: counter-strategy recovery lift > 0.
- Actual value: `-0.07499999999999984`.

Key lesson:

- Adaptive defense was strong overall, but positive counter-strategy recovery did not hold until rho.

Decision-time evidence and future outcome evidence must be separated before this episode can be normalized.
