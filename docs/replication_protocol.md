# Clean replication protocol

The clean replication protocol is the maintained path for future external repair replication.

It supports:

- explicit lead pools,
- curated seed intake,
- metadata probes over native-capable leads,
- issue-derived leads as a separate evidence class,
- isolated runtime workspaces,
- structured environment resolution,
- collection and replay probes,
- bounded source-only repair generation for verified native candidates,
- patch safety, target validation, and duplicate clean replay requirements for any new repair success,
- full scoring disabled by default.

## Batch002 sequence

For every real metadata lead, batch002 must attempt:

1. clone,
2. commit resolution,
3. checkout,
4. target test path check,
5. environment file check,
6. isolated venv creation,
7. declared environment resolution,
8. import probes,
9. collection,
10. failure replay,
11. semantic failure signature when a command runs,
12. admission or rejection decision,
13. repair queue construction for verified native candidates,
14. structural repair routing and context-state locking,
15. source-only patch generation if a safe patch is available,
16. patch safety,
17. target validation with exit status 0,
18. duplicate clean replay 3/3 before a repair success is recorded.

Issue-derived evidence remains separate and never increments native repair counts.

## Batch003 memory-challenge sequence

Batch003 extends the clean replication protocol with deterministic matched-null ensemble calibration:

1. exclude already confirmed repair episodes from new candidate selection,
2. score unrepaired leads with a challenge-candidate difficulty band,
3. admit only native candidates with a verified commit, target test, environment file, collection, and pre-repair failure replay,
4. reject candidates that are too trivial, too broad, environment-only, network-dependent, or not localized to candidate source,
5. run one memory-enabled repair and five memory-disabled null runs only after admission,
6. compute a separation score only when all arms are comparable,
7. keep issue-derived candidates separate from native repair counts,
8. keep full scoring disabled by default.

Batch003 official ingest outcome: 3 challenge candidates were attempted, 0 verified, the matched-null ensemble did not run, and the blocker is `clean_replication_batch_003_no_verified_challenge_candidate`.

## Batch004 dual-track challenge acquisition

Batch004 keeps native evidence preferred while allowing issue-derived ephemeral reproduction harnesses only as a separate evidence class:

1. attempt native challenge acquisition first,
2. retry `darker_skip_glob_failing_test` with improved collection and test-node discovery before classifying `command_cannot_collect_target`,
3. use issue-derived fallback only after native acquisition fails,
4. hash issue text, source context, generated harness, and prompt/context records if issue-derived fallback is used,
5. never increment native repair counts from issue-derived evidence,
6. run matched-null ensemble repair only after a native challenge candidate verifies.

Batch004 current outcome: 1 native carry-forward lead was attempted, 0 native challenge candidates verified, 0 issue-derived candidates verified, no repair ran, and the blocker is `batch004_no_native_or_issue_derived_challenge_candidate_verified`.

## Batch005 source-materialized challenge retry

Batch005 corrects Batch004 by requiring the native retry to clone and checkout the exact source commit in an ephemeral workspace before AST node discovery, collection, and node-level replay. The corrected Batch005 workflow selects the intended `test_isort_respects_skip_glob` node by semantic intent, classifies non-intent setup failures separately, extracts source-stack/import/AST context, derives a source-only patchable subset, and distinguishes empty-subset, generator-not-implemented, no-safe-patch, safety-failure, validation-failure, and success outcomes. If the native retry fails before target verification, Batch005 checks targeted issue-derived seed intake before bounded issue discovery fallback. Issue-derived candidates remain a separate evidence class and never increment native repair counts.

## Batch006 bounded fragment patch assembly

Batch006 continues from the verified Batch005 native challenge candidate. It builds a bounded fragment patch policy, coupled dependency interlock map, dual projection consistency check, pre-generation context lock, passive failure-memory weighting trace, fragment assembly seal, and proof-chain lock. It may assemble at most one source-only patch from at most three fragments, but only after both target-facing and source-facing projections authorize patch bytes. The current Batch006 result blocks before patch bytes with `fragment_patch_plan_not_generated`.

## Batch007 target-intent reachability and precondition resolution

Batch007 continues from Batch006 and verifies whether the observed replay reaches the intended import-sorting skip behavior before any fragment patch can be generated. It records formatter/dependency precondition evidence, declared metadata scans, install strategy decisions, trace-feedback alignment, iterative dual projection recheck, and an explicit completion decision ladder. The current Batch007 result retires `darker_skip_glob_failing_test` with `target_precondition_unresolved`; no patch, validation, duplicate replay, no-overreach, or matched-null ensemble is authorized.

## Batch008 declared precondition materialization

Batch008 corrects declared formatter precondition materialization for `darker_skip_glob_failing_test`. It creates a fresh ephemeral runtime workspace, checks out the exact candidate commit, installs only declared formatter extras and declared target-test tooling, reruns the exact target command, and authorizes bounded source-only repair only after the target behavior is reached and failing. The Batch008 implementation records one source-only patch, target validation PASS, duplicate replay 3/3, and target-file no-overreach PASS. It does not run full scoring, does not claim memory lift, and does not claim self-maintaining software.

## Batch009 patch-quarantined matched-null calibration

Batch009 runs retrospective matched-null calibration on the already repaired Batch008 candidate. Both the memory-enabled arm and memory-disabled null ensemble are denied access to Batch008 patch bytes, fragment records, patch rationale, and successful repair details. This diagnostic does not add another native repair episode and cannot establish prospective memory lift because the successful Batch008 patch already exists.

Batch009 outcome: patch quarantine passes and the null ensemble fails 5/5, but Arm A does not generate a patch and its routing delta is false because the available failure-memory markers are passive. The matched-null score remains `0.0`.

## Batch010 active status-code weighting calibration

Batch010 converts prior decision-time-safe status codes into deterministic weighting records and applies a High-Pass Source Ranking Filter, Two-Candidate Selection Policy, and Strict Minimum-Delta Routing audit before any memory-enabled patch generation can be labeled active. It uses the same already repaired Batch008 candidate only as retrospective calibration, keeps Batch008 patch bytes and rationale quarantined, and does not increment the repair episode count.

Batch010 outcome: the safe status-code evidence does not establish a source, context, or generation routing delta. Patch generation, target validation, duplicate replay, and null ensemble rerun remain `NOT_RUN` or blocked, with exact blocker `active_memory_routing_delta_not_established`.

## Batch011 prospective memory challenge eligibility

Batch011 starts the prospective memory challenge eligibility gate without creating a new versioned lane. It retires `darker_skip_glob_failing_test` from further memory-lift attempts, excludes all previously repaired candidates from new candidate selection, reviews the bounded fresh pytest-rerunfailures leads already present in the clean replication lead pool, and records Curvature-Based Candidate Selection, Two-Winner Source Selection, Strict Minimum-Delta Routing, preregistration, and patch artifact quarantine policies.

Batch011 outcome: no fresh candidate verifies a pre-repair failure under the ingested decision-time-safe evidence, so the memory-enabled arm, null ensemble, patch generation, repair-only fallback, and matched-null score all remain `NOT_RUN` or uncomputed. The exact blocker is `batch011_no_fresh_candidate_verified`.

## Batch012 targeted prospective seed intake

Batch012 continues the same post-v2.37 clean replication workflow without creating a new versioned lane. It requires a reviewed seed at `external_seeds_pending/targeted_prospective_seed_batch012.json` before any new source checkout, native target test verification, issue-derived fallback, prospective memory eligibility, repair-only fallback, or matched-null comparison can run.

Batch012 outcome with no seed: the lane blocks with `targeted_prospective_seed_missing_or_invalid`. No automated fresh-candidate search is repeated, no native or issue-derived candidate is admitted, and native and issue-derived counts remain separate.

## Current official repair episodes

As of the Batch012 targeted seed boundary, the confirmed external non-Ansible native repair endpoints remain `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, `darker_stdin_filename`, and `darker_skip_glob_failing_test`. Full scoring remains `NOT_RUN/disallowed`, matched-null memory status is `not_demonstrated`, and self-maintaining software remains `false/not_demonstrated`.

## Current operational gate status

- Implemented active gates: artifact byte custody, workspace transport integrity, registry validation, semantic failure signatures, candidate admission decisions, target-intent reachability, formatter/dependency precondition resolution, trace-feedback alignment, iterative dual projection recheck, matched-null arm separation, duplicate clean replay, bounded exploration budget, environment normalization, context boundary pinning, public claim boundary audit, status-code weighting policy, High-Pass Source Ranking Filter, Curvature-Based Candidate Selection, Two-Winner Source Selection, and Strict Minimum-Delta Routing.
- Partial gates: structural navigation, active probe routing, dependency projection, interlock invariant mapping, Targeted Prospective Seed Intake, Native Target Test Verification, issue-derived harness execution, matched-null ensemble execution, Active Failure-Memory Routing, Prospective Memory Challenge, prospective memory eligibility, failure-memory weighting, and no-overreach validation for blocked candidates.
- Deferred gates: bounded micro-reversal and v3.0 readiness.
- Current evidence counts: confirmed external native repair episodes `4` after official Batch008 ingest; confirmed issue-derived repair episodes `0`; matched-null comparisons `1`; memory separation evidence `false`; full scoring `NOT_RUN/disallowed`; self-maintaining software `false/not_demonstrated`.
