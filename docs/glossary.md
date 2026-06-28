# Glossary

ControllerGate: a provenance-first software repair research harness.

Current protocol: the maintained protocol pointer used by `scripts/controllergate_audit.py --protocol current`.

Historical lane: a preserved versioned experiment with its own outputs, audit script, and workflow.

Clean replication protocol: the v2.37 maintained interface for future external repair batches.

Consolidated state: a primary JSON record that separates status, blocker, raw evidence, diagnostics, and next actions.

Native candidate: a candidate whose target test physically exists in the selected buggy commit tree.

Issue-derived candidate: a candidate whose reproduction harness is derived from decision-time-safe issue text and kept separate from native-test evidence.

Matched-null comparison: a paired experiment comparing a memory-enabled arm and a memory-disabled arm under the same candidate, command, commit, and environment.
