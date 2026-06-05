# v2.6 BugsInPy Real-Bug Limited Replay Execution

Result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.

## Candidate Source Integrity

- `black:2`: blocked after target-failure guard; log showed dependency/import failure rather than accepted target BugsInPy failure.
- `youtube-dl:1`: promoted after target-failure guard; log matched `BUGSINPY_REPRODUCED_FAILURE: youtube-dl:1`.
- `black:8`: blocked after target-failure guard; log showed dependency/import failure rather than accepted target BugsInPy failure.

## Execution

No limited replay scoring episodes were executed. The three-episode BugsInPy memory-lift gate cannot be entered with only one target-matched candidate.

Gold/fixed patches are outcome-only and excluded from decision-time inputs. Full scoring remains disallowed. Self-maintaining software remains undemonstrated. BugsInPy success or blockage does not prove arbitrary public repo maintenance.

Blocked runtime or target-failure mismatch is not negative capability evidence.
