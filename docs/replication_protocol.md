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
- source-only repair attempt records,
- duplicate clean replay requirements for any future scoreable repair,
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
12. admission or rejection decision.

Issue-derived evidence remains separate and never increments native repair counts.
