# Outcome: TORUS-Theory PR #19 PairCorr Kernelspec

Candidate classification:

- external real repo candidate
- notebook repair attempt
- incomplete evidence bundle

Known outcome:

- PR #19 was merged.
- PR #19 changed `notebooks/validation/synthetic/PairCorr_SideBand_Benchmark.ipynb`.
- Sampled workflow metadata includes `Execute PairCorr Notebooks` failure.
- Fresh local rerun at the PR #19 head reproduced failure with exit code `1`.
- Fresh local rerun failure: `AssertionError: Pin NumPy <2.3 until SciPy wheels catch up`.

Important caveat:

- Full historical job logs are unavailable through the GitHub job-log endpoint, which returned HTTP 410.
- The original GitHub CI failure text is unavailable; the local rerun failure text is captured in `local_rerun_stderr.txt`.

Current status: pending external candidate, not normalized. No v1.7-alpha scoring is allowed from this evidence summary.
