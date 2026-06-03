# Agent Trace: Psi Custody Closure

Decision-time claim summary:

- Claim: v1.6-psi verified separate fixture artifact custody closure.
- Role: separated benchmark code custody from external fixture artifact custody.
- Expected result from corrected ladder chronology: 51 / 51.

Decision-time evidence available to a future v1.7 policy must be limited to package contents, commands, logs, and artifacts available before the outcome check. The verified pass/fail result below is outcome evidence and must not be used as decision-time policy input.

Outcome-only verification evidence:

- Packaged decision report: `51 / 51`.
- Rerun analyzer result: `51 / 51`.
- Package SHA manifest: 8 entries checked, 0 mismatches.
- Rerun status: completed.

Key lesson:

- Psi closed v1.6 custody by requiring a separately supplied verified external fixture artifact.

Key metrics / notes:

- separate fixture artifact required true; bundled with code false; supplied at runtime true; missing/tampered fixture rejected true; verified fixture set only scored true; provenance failures blocked 2

TODO_REQUIRED: original builder/critic transcript custody if this episode is later promoted from pending evidence into the normalized real-trace ledger.
