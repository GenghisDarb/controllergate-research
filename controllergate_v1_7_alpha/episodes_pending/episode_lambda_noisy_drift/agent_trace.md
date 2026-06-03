# Agent Trace: Lambda Noisy Drift

Decision-time claim summary:

- Claim: v1.6-lambda verified noisy heldout drift behavior.
- Role: noisy heldout family drift preserved memory lift.
- Expected result from corrected ladder chronology: 20 / 20.

Decision-time evidence available to a future v1.7 policy must be limited to package contents, commands, logs, and artifacts available before the outcome check. The verified pass/fail result below is outcome evidence and must not be used as decision-time policy input.

Outcome-only verification evidence:

- Packaged decision report: `20 / 20`.
- Rerun analyzer result: `20 / 20`.
- Package SHA manifest: 20 entries checked, 0 mismatches.
- Rerun status: completed.

Key lesson:

- Memory remained useful under noisy heldout family drift.

Key metrics / notes:

- productive lift +0.119; hidden downstream lift +0.497; corruption reduction +0.499; false-positive transfer 0.012

TODO_REQUIRED: original builder/critic transcript custody if this episode is later promoted from pending evidence into the normalized real-trace ledger.
