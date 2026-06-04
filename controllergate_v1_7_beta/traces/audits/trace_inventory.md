# ControllerGate v1.7-beta Trace Inventory

Status: second-repo TatMapper evidence has been review-normalized. ControllerGate scoring remains NOT RUN.

## Inventory

| Area | Status |
| --- | --- |
| Pending evidence bundles | 6 TatMapper bundles present |
| Normalized beta ledger | 6 episodes in `traces/normalized/episodes.jsonl` |
| Episode review classification | Present in `traces/audits/beta_episode_review_classification.json` |
| Second-repo eligibility review | Present; scoring blocked for insufficient second-repo evidence |
| Beta scoring | NOT RUN |
| Full scoring | DISALLOWED |
| Alpha reports/audits | Preserved unchanged |

## Normalized TatMapper Episodes

- `beta_episode_001`: PR #93, Flutter availability/environment gap plus calibration guard repair.
- `beta_episode_002`: PR #92, NDK/tooling review and configuration drift warning.
- `beta_episode_003`: commit `7eb2e48`, invalid Windows checkout filename repair.
- `beta_episode_004`: commit `5019f6f`, Android scaffold and NDK/CMake setup repair.
- `beta_episode_005`: commit `a63a5ea`, Android v2 embedding and SDK alignment repair.
- `beta_episode_006`: commit `d9a6bbe`, pubspec conflict-marker/generated-artifact risk.

## Gate State

All six normalized beta episodes are `external_real_repo_episode`, but all remain `review_required`. The v1.7-beta second-repo eligibility review keeps scoring blocked because the set has only six episodes and lacks full CI logs or fresh local Flutter/Android reruns.
