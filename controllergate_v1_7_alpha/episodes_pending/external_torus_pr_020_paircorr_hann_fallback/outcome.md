# Outcome: TORUS-Theory PR #20 PairCorr Hann Fallback

Candidate classification:

- external real repo candidate
- notebook repair attempt
- incomplete evidence bundle

Known outcome:

- PR #20 was closed unmerged.
- PR #20 changed `notebooks/validation/synthetic/PairCorr_SideBand_Benchmark.ipynb`.
- Fresh local rerun at the PR #20 head reproduced failure with exit code `1`.
- Fresh local rerun failure: `AssertionError: Pin NumPy <2.3 until SciPy wheels catch up`.

Important caveat:

- Full historical job logs are unavailable through the GitHub job-log endpoint, which returned HTTP 410.
- The PR was not merged, so this should not be counted as a successful repair.
- The original GitHub CI failure text is unavailable; the local rerun failure text is captured in `local_rerun_stderr.txt`.

Current status: pending external candidate, not normalized. No v1.7-alpha scoring is allowed from this evidence summary.
