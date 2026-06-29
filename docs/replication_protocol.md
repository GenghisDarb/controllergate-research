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

## Current official repair episodes

As of the post-v2.37 batch002 matched-null official ingest, the confirmed external non-Ansible native repair episodes are `py_bugger_issue_65`, `darker_non_ascii_drop_changes`, and `darker_stdin_filename`. Full scoring remains `NOT_RUN/disallowed`, matched-null memory status is `undemonstrated_equal_performance`, and self-maintaining software remains `false/not_demonstrated`.
