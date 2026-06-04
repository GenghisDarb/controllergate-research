# ControllerGate v1.7-beta Second-Repo Eligibility Review

Status: blocked for scoring. No ControllerGate scoring was run.

## Decision

`scoring_allowed: false`

Reason: v1.7-beta now has eleven normalized TatMapper external real repo episodes, but all eleven remain `review_required`. The count threshold is met, but this update is a normalization pass, not a renewed pilot eligibility approval. Scoring remains blocked until a renewed v1.7-beta eligibility review explicitly decides whether `limited_pilot_only` is allowed.

## Post-Review Strengthening And Collection

After the first eligibility decision, a strengthening pass added current-head TatMapper rerun logs under `controllergate_v1_7_beta/evidence_strengthening/tatmapper_current_head/` and collected five additional bundles:

- `episode_tatmapper_pr98_export_opencv_helper_repair`
- `episode_tatmapper_pr97_closed_unmerged_gradle_entrypoint_regression`
- `episode_tatmapper_pr96_gradle_config_not_run`
- `episode_tatmapper_pr94_manual_override_precedence_review`
- `episode_tatmapper_pr90_codecov_patch_coverage_warning`

The current-head guard script passed, the OpenCV helper failed because `OpenCVConfig.cmake` was unavailable, Flutter version/analyze/test attempts timed out, and Android Gradle wrapper verification remained blocked by missing Java/JAVA_HOME. These strengthening logs are outcome-only observations. The five new bundles are now normalized as review-required evidence, but they do not authorize scoring.

## Counts

| Field | Value |
| --- | --- |
| Beta normalized episodes | 11 |
| Beta external real repo episodes | 11 |
| Eligible beta scoring episodes | 0 |
| Scoring mode | `blocked_pending_renewed_eligibility_review` |
| Full scoring allowed | false |
| ControllerGate scoring | NOT RUN |

## Episode Review

| Episode | Source | Reference | Outcome type | Verified result | Evidence status | Decision/outcome evidence separated | Eligibility |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `beta_episode_001` | TatMapper | PR #93 / `36189ae` | `flutter_availability_failure_or_environment_gap` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_002` | TatMapper | PR #92 / `41c483f` | `ndk_tooling_review` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_003` | TatMapper | commit `7eb2e48` | `windows_checkout_breakage` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_004` | TatMapper | commit `5019f6f` | `android_scaffold_ndk_cmake_setup` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_005` | TatMapper | commit `a63a5ea` | `sdk_v2_embedding_alignment` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_006` | TatMapper | commit `d9a6bbe` | `pubspec_conflict_marker_risk` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_007` | TatMapper | PR #98 / `bc2fff0` | `export_opencv_helper_repair` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_008` | TatMapper | PR #97 / `7e401a0` | `closed_unmerged_gradle_entrypoint_regression` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_009` | TatMapper | PR #96 / `9753a1d` | `gradle_config_not_run` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_010` | TatMapper | PR #94 / `e64ecfc` | `manual_override_precedence_review` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |
| `beta_episode_011` | TatMapper | PR #90 / `ccc9a44` | `codecov_patch_coverage_warning` | `review_required` | pending evidence bundle reviewed and normalized | yes | not eligible |

## Diversity Check

The TatMapper cluster covers the right kinds of second-repo maintenance evidence:

- Flutter availability or environment gap: covered by `beta_episode_001`
- NDK/tooling review: covered by `beta_episode_002`
- Windows checkout breakage: covered by `beta_episode_003`
- Android scaffold / NDK / CMake setup: covered by `beta_episode_004`
- SDK/v2 embedding alignment: covered by `beta_episode_005`
- pubspec conflict-marker risk: covered by `beta_episode_006`
- CI helper / OpenCV config repair: covered by `beta_episode_007`
- closed unmerged repair attempt: covered by `beta_episode_008`
- Gradle config verification gap: covered by `beta_episode_009`
- manual override review caveat: covered by `beta_episode_010`
- Codecov patch coverage warning: covered by `beta_episode_011`
- dependency/config drift: covered by multiple episodes
- build scaffold repair: covered by `beta_episode_004` and `beta_episode_005`
- warning or guardrail case: covered by `beta_episode_002`

The diversity is promising, but the coverage strength is review-required rather than scoring-clean.

## Weak Evidence

Missing or weak evidence is concentrated in five areas:

- Full GitHub Actions logs were unavailable for the selected PRs/commits.
- No fresh local Flutter, Android, Gradle, or Windows checkout reruns were performed.
- Some failing commands are inferred from PR/commit metadata rather than preserved output.
- Original external agent/tool traces are unavailable.
- Codecov patch status exists for two commits, but it is not full app build verification.

## Protected Constraints

- Use only v1.7-beta TatMapper `external_real_repo_episode` entries if beta scoring is later approved.
- Exclude v1.7-alpha TORUS episodes from beta scoring.
- Exclude v1.6 controlled benchmark evidence.
- Do not claim self-maintaining software.
- Do not claim broad cross-repo generalization.
- Keep all weak and ambiguous episodes visible.
- Full scoring remains disallowed.

## Additional Evidence Needed

Before a limited v1.7-beta scoring pass, run a renewed eligibility review over all eleven normalized TatMapper episodes and continue strengthening the cluster with full CI logs or more reliable local reruns where possible. Highest-value additions are Flutter analyze/test/build outputs, Android/Gradle build logs with Java available, Windows checkout reproduction, and a deterministic Flutter tooling check for the pubspec conflict-marker risk.
