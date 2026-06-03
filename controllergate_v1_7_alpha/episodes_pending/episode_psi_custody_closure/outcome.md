# Outcome: Psi Custody Closure

Classification:

- real ControllerGate v1.6 ladder verification episode
- package-backed evidence bundle
- normalized as controlled_benchmark_evidence, not scored for v1.7-alpha

Known verified outcome:

- Corrected ladder result: `51 / 51`.
- Packaged `decision_report.json`: `51 / 51`.
- Local package runner plus analyzer rerun: `51 / 51`.
- Package SHA manifest verification: 8 entries checked, 0 mismatches.

Role:

- separated benchmark code custody from external fixture artifact custody

Key metrics / notes:

- separate fixture artifact required true; bundled with code false; supplied at runtime true; missing/tampered fixture rejected true; verified fixture set only scored true; provenance failures blocked 2

Lesson:

- Psi closed v1.6 custody by requiring a separately supplied verified external fixture artifact.

Current status: normalized as controlled_benchmark_evidence. No v1.7-alpha real repo scoring is allowed from this evidence summary.
