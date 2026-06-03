# Outcome: Lambda Noisy Drift

Classification:

- real ControllerGate v1.6 ladder verification episode
- package-backed evidence bundle
- normalized as controlled_benchmark_evidence, not scored for v1.7-alpha

Known verified outcome:

- Corrected ladder result: `20 / 20`.
- Packaged `decision_report.json`: `20 / 20`.
- Local package runner plus analyzer rerun: `20 / 20`.
- Package SHA manifest verification: 20 entries checked, 0 mismatches.

Role:

- noisy heldout family drift preserved memory lift

Key metrics / notes:

- productive lift +0.119; hidden downstream lift +0.497; corruption reduction +0.499; false-positive transfer 0.012

Lesson:

- Memory remained useful under noisy heldout family drift.

Current status: normalized as controlled_benchmark_evidence. No v1.7-alpha real repo scoring is allowed from this evidence summary.
