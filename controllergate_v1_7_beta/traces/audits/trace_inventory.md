# ControllerGate v1.7-beta Trace Inventory

Status: second-repo TatMapper evidence has been strengthened, review-normalized, and run through the approved limited beta pilot scoring pass. Eleven TatMapper episodes are normalized as review-required evidence, limited beta pilot scoring completed with review-required caveats, and ControllerGate full scoring remains NOT RUN.

## Inventory

| Area | Status |
| --- | --- |
| Pending evidence bundles | 11 TatMapper bundles present |
| Normalized beta ledger | 11 episodes in `traces/normalized/episodes.jsonl` |
| Episode review classification | Present in `traces/audits/beta_episode_review_classification.json` |
| Second-repo eligibility review | Present; limited pilot eligibility approved |
| Beta scoring | LIMITED_PILOT_RUN |
| Beta scoring result | COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS |
| Beta critic review package | Present |
| Deterministic replay readiness audit | Present; deterministic replay-ready count 0 |
| Replay eligibility pathway | Present; 0 of 11 deterministic replay-ready |
| Full scoring | DISALLOWED |
| Alpha reports/audits | Preserved unchanged |
| Strengthening logs | Present in `evidence_strengthening/tatmapper_current_head/` |

## Normalized TatMapper Episodes

- `beta_episode_001`: PR #93, Flutter availability/environment gap plus calibration guard repair.
- `beta_episode_002`: PR #92, NDK/tooling review and configuration drift warning.
- `beta_episode_003`: commit `7eb2e48`, invalid Windows checkout filename repair.
- `beta_episode_004`: commit `5019f6f`, Android scaffold and NDK/CMake setup repair.
- `beta_episode_005`: commit `a63a5ea`, Android v2 embedding and SDK alignment repair.
- `beta_episode_006`: commit `d9a6bbe`, pubspec conflict-marker/generated-artifact risk.
- `beta_episode_007`: PR #98, OpenCV CI helper repair and current-head OpenCV discovery failure.
- `beta_episode_008`: PR #97, closed-unmerged Gradle entrypoint repair with compile-risk review findings.
- `beta_episode_009`: PR #96, Android Gradle configuration repair with testing-not-run caveat.
- `beta_episode_010`: PR #94, calibration guard repair with manual override precedence review caveat.
- `beta_episode_011`: PR #90, Codecov patch coverage warning-only guardrail evidence.

## Gate State

All eleven normalized beta episodes are `external_real_repo_episode`, and all remain `review_required`. The renewed v1.7-beta second-repo eligibility review allowed a tiny exploratory `limited_pilot_only` scoring run, and that limited run completed with review-required caveats. Full scoring remains disallowed.

## Newly Normalized TatMapper Episodes

- `episode_tatmapper_pr98_export_opencv_helper_repair`
- `episode_tatmapper_pr97_closed_unmerged_gradle_entrypoint_regression`
- `episode_tatmapper_pr96_gradle_config_not_run`
- `episode_tatmapper_pr94_manual_override_precedence_review`
- `episode_tatmapper_pr90_codecov_patch_coverage_warning`

## Strengthening Summary

Current-head local rerun logs are preserved as outcome-only evidence. Guard calibration passed, OpenCV helper failed due missing `OpenCVConfig.cmake`, Flutter commands timed out, and Android Gradle wrapper verification remained blocked by missing Java/JAVA_HOME.
