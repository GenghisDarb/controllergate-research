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

## Current official repair episodes

As of the post-v2.37 batch003 official ingest and batch004 continuation, the confirmed external non-Ansible native repair episodes are `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, and `darker_stdin_filename`. Full scoring remains `NOT_RUN/disallowed`, matched-null memory status is `undemonstrated_equal_performance`, and self-maintaining software remains `false/not_demonstrated`.
