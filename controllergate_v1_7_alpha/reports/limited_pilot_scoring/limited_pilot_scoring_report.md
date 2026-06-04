# v1.7-alpha Limited Real Repo Pilot Scoring

ControllerGate v1.7-alpha limited pilot scoring was run on 10 normalized TORUS-Theory external real repo episodes. This is exploratory pilot evidence only, not proof of self-maintaining software.

## Scope

Scoring mode: `limited_pilot_only`

Full scoring allowed: `false`

Only `external_real_repo_episode` entries were included. Correction-review episodes and controlled benchmark evidence episodes were excluded from real repo scoring.

## Counts

| Metric | Count |
| --- | --- |
| eligible external episodes | 10 |
| passed | 2 |
| failed | 5 |
| warning_only | 1 |
| review_required | 2 |
| closed_unmerged | 1 |
| deterministic pass/fail | 7 |
| warning or review_required | 3 |

## Exclusions

| Excluded category | Count |
| --- | --- |
| controlled_benchmark_evidence | 8 |
| correction_review_episode | 2 |

## Episode-Level Decision Table

| Episode | PR | Outcome type | Verified result | Runner | Dependency/config drift | Generated artifact mismatch |
| --- | --- | --- | --- | --- | --- | --- |
| episode_011 | 15 | malformed_artifact_failure | failed | true | false | true |
| episode_012 | 16 | successful_rerun_positive_signal | passed | true | false | false |
| episode_013 | 19 | dependency_version_assertion_failure | failed | true | true | false |
| episode_014 | 20 | dependency_version_assertion_failure_closed_unmerged | failed | true | true | false |
| episode_015 | 32 | notebook_kernel_failure | failed | true | true | false |
| episode_016 | 32 | validation_workflow_failure | review_required | false | UNAVAILABLE | false |
| episode_017 | 33 | notebook_selector_repair | passed | true | true | false |
| episode_018 | 33 | readme_guard_warning_only | warning_only | true | false | false |
| episode_019 | 17 | latex_workflow_repair | review_required | true | true | false |
| episode_020 | 34 | readme_guard_failure | failed | true | true | false |

## Memory Baselines

| Baseline | Result | Reason |
| --- | --- | --- |
| discovered-memory result | UNAVAILABLE | The TORUS-Theory external rerun episodes do not contain ControllerGate discovered-memory condition outputs. |
| no-memory baseline | UNAVAILABLE | No no-memory baseline was available in the normalized TORUS external evidence. |
| predefined-memory baseline | UNAVAILABLE | No predefined-memory baseline was available in the normalized TORUS external evidence. |
| poisoned-memory baseline | UNAVAILABLE | No poisoned-memory baseline was available in the normalized TORUS external evidence. |

## Detection Results

| Detection area | Result |
| --- | --- |
| false-success detection | 0 explicit external false-success episodes; iota/pi false-success correction episodes were excluded from real repo scoring. |
| stale-read or false-completion detection | true=0, false=10, null=0 |
| dependency/config drift detection | true=6, false=3, null=1 |
| generated artifact mismatch detection | true=1, false=9, null=0 |
| future leakage check | decision-time/outcome-only overlap episodes=0; review-required caveats preserved |

## Limitations

- Historical GitHub Actions log text is unavailable for multiple episodes because the job-log endpoint returned HTTP 410.
- Original agent/tool transcripts are unavailable for the TORUS external episodes.
- Several reruns are bounded local command reruns rather than full GitHub Actions job replays.
- No ControllerGate memory-condition baselines are available for the TORUS external evidence.
- Review-required, warning-only, failed, and closed-unmerged episodes remain included.

## Non-Claims

- This is not proof of self-maintaining software.
- This is not full v1.7-alpha scoring.
- This is not broad external generalization across repositories.
- This does not convert controlled benchmark evidence or correction-review episodes into real repo scoring evidence.

## Result

Overall limited pilot result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`
