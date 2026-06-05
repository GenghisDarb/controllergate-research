# v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign

Result: `insufficient_target_matched_bugsinpy_candidates_for_v2_8`.

## Phase A

`black:2` and `black:8` now have dependency-recovery rerun plans and a Linux GitHub Actions workflow path. They are not promoted locally because no fresh recovery artifact exists yet.

## Phase B

Additional BugsInPy expansion did not run locally because the workspace lacks the required BugsInPy Linux runtime. The v2.7 workflow can perform bounded expansion on Ubuntu after Phase A.

## Phase C

Final target-matched BugsInPy candidate count remains 1. The only promoted candidate is the corrected v2.5 `youtube-dl:1` target assertion replay.

## Phase D

v2.8 limited replay execution did not run. Repair scoring remains NOT RUN. Full scoring remains disallowed. Memory lift is not demonstrated. Self-maintaining software is not demonstrated.

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import failures do not count as target bug replay.
