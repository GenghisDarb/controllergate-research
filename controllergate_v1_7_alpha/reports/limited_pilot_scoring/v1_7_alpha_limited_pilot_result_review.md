# v1.7-alpha Limited Pilot Result Review

Status: limited exploratory real-repo pilot completed with review-required caveats.

ControllerGate v1.7-alpha limited pilot scoring was run on 10 normalized TORUS-Theory external real repo episodes. This is exploratory pilot evidence only, not proof of self-maintaining software.

## Review Decision

The limited pilot result is accepted as an honest first real-repo scoring run, not as a pass/fail validation of self-maintaining behavior.

Result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`

Recommended next milestone: start v1.7-beta second-repo evidence collection, preferably TatMapper or another non-TORUS repository with real CI/build/test failures.

Reason: more TORUS episodes would add depth, but a second repo is the next credibility jump because the current evidence is one repo family with bounded reruns and unavailable historical GitHub Actions logs.

## What Scoring Found

| Metric | Result |
| --- | --- |
| Eligible external episodes scored | 10 |
| Passed | 2 |
| Failed | 5 |
| Warning-only | 1 |
| Review-required | 2 |
| Closed-unmerged | 1 |
| Deterministic pass/fail outcomes | 7 |
| Warning or review-required outcomes | 3 |
| Controlled benchmark episodes excluded | 8 |
| Correction-review episodes excluded | 2 |

Episode outcome review:

| Episode | PR | Outcome type | Result | Review note |
| --- | ---: | --- | --- | --- |
| episode_011 | 15 | malformed_artifact_failure | failed | Invalid notebook JSON was reproduced by fresh local rerun; generated artifact mismatch signal present. |
| episode_012 | 16 | successful_rerun_positive_signal | passed | Fresh local rerun passed and found the TORUS-POSITIVE signal. |
| episode_013 | 19 | dependency_version_assertion_failure | failed | NumPy version assertion reproduced in current environment. |
| episode_014 | 20 | dependency_version_assertion_failure_closed_unmerged | failed | NumPy version assertion reproduced; PR was closed unmerged and must stay in the pilot. |
| episode_015 | 32 | notebook_kernel_failure | failed | Bounded papermill rerun reproduced missing notebook kernel metadata. |
| episode_016 | 32 | validation_workflow_failure | review_required | Workflow failure metadata exists, but exact historical logs and local rerun output are unavailable. |
| episode_017 | 33 | notebook_selector_repair | passed | Bounded selector rerun passed; full notebook execution loop was not replayed. |
| episode_018 | 33 | readme_guard_warning_only | warning_only | Local README guard printed warnings while exiting 0; not equivalent to historical shell check. |
| episode_019 | 17 | latex_workflow_repair | review_required | Full LaTeX workflow replay unavailable; bounded check failed due local TeX permission issue. |
| episode_020 | 34 | readme_guard_failure | failed | Bounded README guard rerun failed with missing README entries. |

## Passed Review Checks

| Check | Result | Reason |
| --- | --- | --- |
| Scope gate | PASS | Only `external_real_repo_episode` entries were scored. |
| Exclusion gate | PASS | The 8 controlled benchmark episodes and 2 correction-review episodes were excluded. |
| Caveat preservation | PASS | Failed, warning-only, ambiguous, and closed-unmerged episodes remain included. |
| Decision/outcome separation | PASS | Decision-time and outcome-only fields have 0 overlap in the scoring audit. |
| Future-leakage guard | PASS_WITH_REVIEW_REQUIRED_CAVEATS | Review-required future-leakage status was preserved instead of converted into a pass. |
| Non-claim boundary | PASS | The report explicitly rejects self-maintaining, full-scoring, and broad generalization claims. |
| Limited scoring audit | PASS | `audit_limited_pilot_scoring.py` accepts the scoring output. |

## Detection Review

| Detection area | Result | Interpretation |
| --- | --- | --- |
| False-success detection | 0 explicit external false-success episodes | iota/pi false-success correction episodes were excluded from real-repo scoring, as required. |
| Stale-read or false-completion detection | true=0, false=10, null=0 | No stale-read or false-completion signal is present in these external episodes. |
| Dependency/config drift detection | true=6, false=3, null=1 | Dependency/config drift is a major theme in the TORUS pilot set. |
| Generated artifact mismatch detection | true=1, false=9, null=0 | The PR #15 malformed notebook case is the one generated-artifact mismatch signal. |
| Correction-required signal | true=6, false=4, null=0 | Most failed external outcomes still require correction or review handling. |

## Memory Baseline Review

The pilot cannot measure ControllerGate memory lift.

| Baseline | Status | Reason |
| --- | --- | --- |
| Discovered memory | UNAVAILABLE | TORUS external rerun episodes do not contain ControllerGate discovered-memory condition outputs. |
| No-memory baseline | UNAVAILABLE | No no-memory baseline was present in the normalized TORUS evidence. |
| Predefined-memory baseline | UNAVAILABLE | No predefined-memory baseline was present in the normalized TORUS evidence. |
| Poisoned-memory baseline | UNAVAILABLE | No poisoned-memory baseline was present in the normalized TORUS evidence. |

This means the v1.7-alpha pilot validates the evidence/scoring harness against real repo episodes, but it does not yet demonstrate real-repo memory improvement.

## Remaining Caveats

- Historical GitHub Actions log text is unavailable for multiple TORUS episodes because the job-log endpoint returned HTTP 410.
- Original agent/tool transcripts are unavailable for the TORUS external episodes.
- Several reruns are bounded local command reruns rather than full GitHub Actions job replays.
- No ControllerGate memory-condition baselines are available for the TORUS external evidence.
- Two episodes remain `review_required`, and one is warning-only.
- The external source is one repository family, so cross-repo generalization is not established.

## Non-Claims

- Do not claim that v1.7-alpha passes full real-repo scoring.
- Do not claim proof of self-maintaining software.
- Do not claim broad external generalization.
- Do not claim ControllerGate improved real-repo repair outcomes through memory on this pilot.
- Do not convert TORUS bounded rerun evidence into original GitHub Actions log proof.

## Recommendation

Move next to v1.7-beta second-repo external evidence collection.

Priority order:

1. Collect at least 10 external episodes from TatMapper or another non-TORUS repo.
2. Preserve the same pending bundle, normalization, classification, eligibility, and limited scoring gates.
3. Run a multi-repo limited scoring pass only after the second repo cluster is normalized and reviewed.
4. Compare TORUS and non-TORUS behavior without claiming self-maintaining software.

Additional TORUS collection is useful for depth, but it should not substitute for the second-repo credibility jump.
