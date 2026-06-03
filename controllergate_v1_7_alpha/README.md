# ControllerGate v1.7-alpha

Purpose: real repository / real agent trace pilot.

v1.7-alpha should test whether ControllerGate's discovered causal trace memory improves maintenance decisions on real repository and real agent traces without relying on synthetic issue generation.

This folder contains the v1.7-alpha scaffold, normalized evidence ledger, and review classification layer. It does not claim ControllerGate v1.7-alpha works yet, and real repo scoring remains blocked until external real repo episodes are supplied.

## Required Directory Shape

```text
controllergate_v1_7_alpha/
  traces/
    raw/
    normalized/
    audits/
  schemas/
  reports/
  controllergate_memory/
```

## First Pilot Source Recommendation

Use the ControllerGate chain itself for `v1.7-alpha-internal`, then use a separate repo for `v1.7-beta-external`.

The supplied v1.6-psi artifacts are valuable custody evidence, but they are controlled benchmark artifacts. They should be recorded as prior evidence and release material, not counted as real maintenance episodes.

## Initial Pass Gates

1. SHA/custody verification passes for all input artifacts.
2. Future-leakage audit passes.
3. Policy blindness passes.
4. Discovered memory hidden/downstream pass is greater than no-memory.
5. Discovered memory corruption is lower than no-memory.
6. Discovered memory human-required rate is lower than no-memory.
7. Discovered memory false-positive transfer is less than or equal to `0.20`.
8. Productive recommendation precision is at least `0.70`.
9. Avoidance transfer precision is at least `0.70`.
10. Discovered memory beats predefined memory on at least one repeated real failure family.
11. Discovered memory does not over-transfer on near-match real failures.
12. Stale-read or false-completion detection succeeds in at least one real case.
13. Generated artifact mismatch detection succeeds in at least one real case.
14. Proof ledger completeness is `100%`.
15. All failed criteria are preserved and reported.
