# Technical validation gap report

ControllerGate has made meaningful progress as a research harness, but the evidence does not yet support a technical validation release.

## Confirmed progress

- Two confirmed external non-Ansible repair episodes are recorded.
- Artifact custody, registry validation, and claim-boundary checks are active.
- Clean replication batch002 uses explicit real leads instead of placeholders.
- Environment resolution is attempted before collection and failure replay.
- Clean replication batch002 generated and validated one additional native source-only repair with duplicate clean replay 3/3.

## Remaining gaps

- Additional external repair successes across more repositories are required.
- Clean repair generation needs broader coverage beyond the currently validated darker repair case.
- Matched-null comparison evidence is not accepted yet.
- Full scoring remains disallowed.
- Public claims must remain conservative.

## Current blocker

Batch002 has demonstrated one additional source-only repair after environment resolution. The remaining blocker is broader replicated repair coverage and matched comparison evidence, not artifact custody or environment setup for this batch.
