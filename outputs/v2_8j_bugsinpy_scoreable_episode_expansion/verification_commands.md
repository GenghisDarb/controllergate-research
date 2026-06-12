# v2.8j Verification

- Run GitHub Actions workflow `v2_8j_bugsinpy_scoreable_episode_expansion`.
- Download artifact `v2_8j_bugsinpy_scoreable_episode_expansion_artifacts`.
- Verify `SHA256SUMS.txt` inside the artifact.
- Confirm `decision_report.json` and `aggregate_report.json` reproduce campaign summary counts.
- Confirm source-only repair patches are separate from replay/materialization artifacts.
