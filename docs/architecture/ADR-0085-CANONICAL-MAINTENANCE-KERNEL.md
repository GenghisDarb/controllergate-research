# ADR-0085: Canonical maintenance kernel

Status: accepted for Batch085 convergence.

ControllerGate has one production maintenance path: `controllergate.cli` invokes
`controllergate.engine`, which coordinates typed reactions through the canonical
dispatcher and records state in the SQLite controller-state store. External
processes cross `controllergate.execution.execution_broker`. Proof records, not
reports or configuration, are the only inputs to repair-count decisions.

Batch-specific orchestrators are migration and reporting tools. Product Alpha is
a controlled fixture. Historical implementations remain readable only through
declared compatibility harnesses and cannot be selected for fresh maintenance.

The state database, proof store, routing-memory store, sealed truth store, and
patch store are separate authorities. Routing decisions cannot read truth or
patch evidence. Public state views are generated from the database and proof
records rather than edited independently.

This decision does not promote protocol v2.19, authorize public writes, establish
prospective AMDS effectiveness, or claim production readiness.
