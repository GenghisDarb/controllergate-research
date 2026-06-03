# Outcome: Mu Discovery vs Predefinition

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

- discovered memory separated from predefined memory through online learning

Key metrics / notes:

- discovered hidden pass 0.992; predefined hidden pass 0.728; novel discovered-vs-predefined gap +0.967

Lesson:

- Discovered memory separated from frozen predefined memory under novel heldout-only recurrence.

Current status: normalized as controlled_benchmark_evidence. No v1.7-alpha real repo scoring is allowed from this evidence summary.
