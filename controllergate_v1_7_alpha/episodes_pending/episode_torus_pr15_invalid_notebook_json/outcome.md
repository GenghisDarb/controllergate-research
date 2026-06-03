# Outcome: TORUS-Theory PR #15 Notebook Force Clean

Candidate classification:

- external real repo candidate
- notebook repair / cleanup
- incomplete evidence bundle

Known outcome:

- PR #15 was merged.
- The PR body says it superseded PRs #9 through #14.
- Sampled workflow metadata for the PR head includes `Execute PairCorr Notebooks` failure.
- Fresh local rerun at the PR #15 head reproduced failure with exit code `1`.
- Fresh local rerun failure: `nbformat.reader.NotJSONError: Notebook does not appear to be JSON`.

Important caveat:

- Full historical job logs are unavailable through the GitHub job-log endpoint, which returned HTTP 410.
- The original GitHub CI failure text is unavailable; the local rerun failure text is captured in `local_rerun_stderr.txt`.

Current status: pending external candidate, not normalized. No v1.7-alpha scoring is allowed from this evidence summary.
