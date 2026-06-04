# ControllerGate v1.7-beta Trace Inventory

Status: second-repo TatMapper evidence has been strengthened. Six TatMapper episodes remain review-normalized, five more are pending, and ControllerGate scoring remains NOT RUN.

## Inventory

| Area | Status |
| --- | --- |
| Pending evidence bundles | 11 TatMapper bundles present |
| Normalized beta ledger | 6 episodes in `traces/normalized/episodes.jsonl` |
| Episode review classification | Present in `traces/audits/beta_episode_review_classification.json` |
| Second-repo eligibility review | Present; scoring blocked for insufficient second-repo evidence |
| Beta scoring | NOT RUN |
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

## Gate State

All six normalized beta episodes are `external_real_repo_episode`, but all remain `review_required`. Five additional TatMapper bundles are pending and not normalized. The v1.7-beta second-repo eligibility review keeps scoring blocked until the new pending bundles are reviewed, normalized if eligible, and the eligibility review is rerun.

## Newly Pending TatMapper Episodes

- `episode_tatmapper_pr98_export_opencv_helper_repair`
- `episode_tatmapper_pr97_closed_unmerged_gradle_entrypoint_regression`
- `episode_tatmapper_pr96_gradle_config_not_run`
- `episode_tatmapper_pr94_manual_override_precedence_review`
- `episode_tatmapper_pr90_codecov_patch_coverage_warning`

## Strengthening Summary

Current-head local rerun logs are preserved as outcome-only evidence. Guard calibration passed, OpenCV helper failed due missing `OpenCVConfig.cmake`, Flutter commands timed out, and Android Gradle wrapper verification remained blocked by missing Java/JAVA_HOME.
