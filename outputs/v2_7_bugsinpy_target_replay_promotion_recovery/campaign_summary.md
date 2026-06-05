# v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign

Result: `insufficient_target_matched_bugsinpy_candidates_for_v2_8`.

## Artifact Ingestion

The v2.7 GitHub Actions recovery artifact was ingested from:

`C:\Users\thisb\OneDrive\Documents\ControllerGate\outputs\v2_7_bugsinpy_target_replay_promotion_recovery\artifact_intake\v2_7_bugsinpy_target_replay_recovery_artifacts`

## Phase A

- `black:2`: `blocked_runtime_environment_failure`; target matched: `false`; reason: dependency/import/runtime failure marker was present
- `black:8`: `blocked_runtime_environment_failure`; target matched: `false`; reason: dependency/import/runtime failure marker was present

## Phase B

Additional BugsInPy candidates attempted by the runner: 8.
New target-matched candidates from expansion: 0.

## Phase C

Final target-matched BugsInPy candidate count: 1.

## Phase D

v2.8 limited replay execution did not run.
v2.8 executed: false.
Repair scoring remains NOT RUN. Full scoring remains disallowed. Memory lift is not demonstrated. Self-maintaining software is not demonstrated.

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import/runtime failures do not count as target bug replay.
