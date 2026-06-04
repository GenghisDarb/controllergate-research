# ControllerGate v1.7-beta Second-Repo Eligibility Review

Status: blocked for scoring. No ControllerGate scoring was run.

## Decision

`scoring_allowed: false`

Reason: v1.7-beta has six normalized TatMapper external real repo episodes, but all six remain `review_required`. The set is below the 10-episode minimum used for the v1.7-alpha limited pilot and lacks full CI logs or fresh local Flutter/Android reruns. The evidence is useful for second-repo readiness, but not yet sufficient for a limited beta scoring run.

## Counts

| Field | Value |
| --- | --- |
| Beta normalized episodes | 6 |
| Beta external real repo episodes | 6 |
| Eligible beta scoring episodes | 0 |
| Scoring mode | `blocked_insufficient_second_repo_evidence` |
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

## Diversity Check

The TatMapper cluster covers the right kinds of second-repo maintenance evidence:

- Flutter availability or environment gap: covered by `beta_episode_001`
- NDK/tooling review: covered by `beta_episode_002`
- Windows checkout breakage: covered by `beta_episode_003`
- Android scaffold / NDK / CMake setup: covered by `beta_episode_004`
- SDK/v2 embedding alignment: covered by `beta_episode_005`
- pubspec conflict-marker risk: covered by `beta_episode_006`
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

Before a limited v1.7-beta scoring pass, collect at least four more eligible TatMapper episodes to reach 10, and strengthen the current cluster with fresh local reruns or full CI logs where possible. Highest-value additions are Flutter analyze/test/build outputs, Android/Gradle build logs, Windows checkout reproduction, and a deterministic Flutter tooling check for the pubspec conflict-marker risk.
