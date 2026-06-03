# Agent Trace: Pi Misreport Candidate

Known correction event summary:

- Builder reported ControllerGate v1.6-pi as `28 / 28`.
- Critic verification found `27 / 28`.
- The failed criterion was counter-strategy recovery lift.
- Corrected counter-strategy recovery lift was `-0.075`, not positive.

Evidence status:

- TODO_REQUIRED: original builder trace or transcript containing the `28 / 28` claim.
- TODO_REQUIRED: critic verification output showing `27 / 28`.
- TODO_REQUIRED: packaged `decision_report.json` path and SHA256.
- TODO_REQUIRED: rerun analyzer output.
- TODO_REQUIRED: `SHA256SUMS.txt` verification output.
- TODO_REQUIRED: pi package ZIP and notebook are missing from `controllergate_v1_7_alpha/artifacts_intake/pi/`.

Decision-time evidence and future outcome evidence must be separated before this episode can be normalized.
