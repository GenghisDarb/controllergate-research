# Technical validation gap report

ControllerGate has made meaningful progress as a research harness, but the evidence does not yet support a technical validation release.

## Confirmed progress

- Three external non-Ansible native repair episodes are confirmed after official ingest: `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, and `darker_stdin_filename`.
- Artifact custody, registry validation, and claim-boundary checks are active.
- Clean replication batch002 uses explicit real leads instead of placeholders.
- Environment resolution is attempted before collection and failure replay.
- Clean replication batch002 generated and validated one additional native source-only repair with target validation PASS and duplicate clean replay 3/3.
- The `darker_non_ascii_drop_changes` no-overreach result is target-file bounded only; stronger robustness is not claimed.
- The `darker_stdin_filename` matched-null comparison produced equal success across the memory-enabled and memory-disabled arms, so preliminary memory separation evidence remains false.
- Batch003 adds matched-null ensemble calibration and challenge-candidate difficulty-band admission, but it still requires a verified moderate-complexity candidate before a memory-challenge repair experiment can run.

## Remaining gaps

- Additional external repair successes across more repositories are still useful for broader replication.
- Clean repair generation needs broader coverage beyond the currently validated darker repair case.
- Matched-null memory separation evidence is not accepted yet.
- A matched-null ensemble on a verified challenge candidate has not produced accepted separation evidence.
- Full scoring remains disallowed.
- Public claims must remain conservative.

## Current blocker

Batch002 has demonstrated two additional source-only repairs after environment resolution. The remaining blocker is accepted matched-null ensemble separation evidence on a safe challenge candidate and broader robustness evidence, not artifact custody or environment setup for this batch.
