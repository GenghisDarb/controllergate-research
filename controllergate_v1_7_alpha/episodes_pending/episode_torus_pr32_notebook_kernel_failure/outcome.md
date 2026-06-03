# Outcome: TORUS-Theory PR #32 Notebook Kernel Failure

Candidate classification:

- external real repo pending evidence
- notebook execution failure
- dependency/config/kernel metadata issue

Known outcome:

- PR #32 was merged.
- CI Full run `16085973917` failed.
- Job `test (3.11)` failed.
- Fresh bounded local rerun at PR #32 head failed with exit code `1`.
- Local failure: `ValueError: No kernel name found in notebook and no override provided.`

Important caveat:

- Full historical GitHub Actions job logs are unavailable through the GitHub job-log endpoint, which returned HTTP 410.
- This is pending evidence only and is not normalized or scoring-eligible.

Current status: pending external real repo evidence. No v1.7-alpha scoring is allowed from this bundle.
