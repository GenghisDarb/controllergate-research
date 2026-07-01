# Technical validation gap report

ControllerGate has made meaningful progress as a research harness, but the evidence does not yet support a technical validation release.

## Confirmed progress

- Four external non-Ansible native repair endpoints are confirmed after official Batch008 ingest: `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`.
- Artifact custody, registry validation, and claim-boundary checks are active.
- Clean replication batch002 uses explicit real leads instead of placeholders.
- Environment resolution is attempted before collection and failure replay.
- Clean replication batch002 generated and validated one additional native source-only repair with target validation PASS and duplicate clean replay 3/3.
- The `darker_non_ascii_drop_changes` no-overreach result is target-file bounded only; stronger robustness is not claimed.
- The `darker_stdin_filename` matched-null comparison produced equal success across the memory-enabled and memory-disabled arms, so preliminary memory separation evidence remains false.
- Batch003 officially records matched-null ensemble calibration and challenge-candidate difficulty-band admission, but found 0 verified challenge candidates; the matched-null ensemble did not run.
- Batch004 records native-first dual-track challenge acquisition with issue-derived ephemeral reproduction harness fallback as a separate evidence class. It verified 0 native challenge candidates and 0 issue-derived candidates.
- The official Batch005 source-materialized artifact verified byte custody and source materialization. The corrected Batch005 workflow adds intended target-node selection, source-stack extraction, patchable source subset derivation, and explicit no-patch taxonomy before any repair attempt.
- Batch006 adds bounded fragment patch assembly, coupled dependency interlock mapping, dual projection consistency checks, passive failure-memory weighting records, and proof-chain custody for the verified native challenge candidate. It blocks before patch bytes with `fragment_patch_plan_not_generated`.
- Batch007 adds target-intent reachability, formatter/dependency precondition resolution, trace-feedback alignment, iterative dual projection recheck, and candidate retirement for the same challenge candidate.
- Batch008 corrects declared formatter precondition materialization, reaches the intended target behavior after declared extras, and validates one bounded source-only patch with target validation PASS, duplicate replay 3/3, and target-file no-overreach PASS. No additional matched-null memory evidence is counted.
- Batch009 is retrospective patch-quarantined matched-null calibration on the already repaired Batch008 candidate. It does not add another repair episode and does not satisfy prospective memory-lift requirements.

## Remaining gaps

- Additional external repair successes across more repositories are still useful for broader replication.
- Clean repair generation needs broader coverage beyond the currently validated darker repair case.
- Matched-null memory separation evidence is not accepted yet.
- A matched-null ensemble on a verified challenge candidate has not run or produced accepted separation evidence.
- Full scoring remains disallowed.
- Public claims must remain conservative.

## Current blocker

Batch002 has demonstrated two additional source-only repairs after environment resolution. Batch003 and batch004 show that challenge-candidate acquisition remains difficult. Batch005 addresses source materialization and target-node/source-subset derivation. Batch006 adds fragment assembly gates, Batch007 adds target-intent/precondition gates, and Batch008 demonstrates one bounded repair after declared precondition materialization. The remaining blocker is not a single-target repair endpoint; it is the lack of broader audited replication and accepted matched-null memory separation evidence.

## Current operational gate status

- Implemented active gates: artifact byte custody, workspace transport integrity, registry validation, semantic failure signatures, candidate admission decisions, target-intent reachability, formatter/dependency precondition resolution, trace-feedback alignment, iterative dual projection recheck, matched-null arm separation, duplicate clean replay, bounded exploration budget, environment normalization, context boundary pinning, public claim boundary audit, and release-readiness blocking.
- Partial gates: baseline registry snapshot standardization, structural navigation, active probe routing, issue-derived harness execution, issue text temporal guard, matched-null ensemble execution, failure-memory weighting, post-patch revalidation for blocked candidates, global-block exception research, and broader evidence-ledger standardization.
- Deferred gates: bounded micro-reversal and v3.0 readiness.
- Current evidence counts: confirmed external native repair episodes `4` after official Batch008 ingest; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.
