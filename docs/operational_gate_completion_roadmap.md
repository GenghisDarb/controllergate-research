# Operational gate completion roadmap

This roadmap translates remaining internal design intent into neutral engineering gates.

| Gate | Status | Repo module | Output files | Blocker | Audit assertion | Do-not-overclaim note |
| --- | --- | --- | --- | --- | --- | --- |
| Workspace Transport Integrity Gate | implemented | `controllergate/core/transport.py` | `workspace_transport_integrity_log.json` | `transport_integrity_breach` | every transfer records source and destination hashes | transport integrity is not repair success |
| Bounded Exploration Budget | implemented | `controllergate/core/budget.py` | `bounded_exploration_budget_trace.json` | `exploration_budget_exhausted` | budget decrements for probes and repair forks | budget routing is not intelligence |
| Context Boundary Pinching | implemented | `controllergate/core/context_boundary.py` | `context_boundary_map.json` | `no_candidate_source_interlock_invariant` | patch context excludes tests and unrelated files | context selection is not proof of correctness |
| Execution Environment Normalization | implemented | `controllergate/core/normalization.py` | `environment_normalization_log.json` | `environment_normalization_unsafe` | forbidden normalization blocks | environment setup is not a patch |
| Issue-Derived Ephemeral Reproduction Harness | partial | `controllergate/core/evidence_classes.py` | `issue_derived_evidence_class_policy.json` | `issue_derived_harness_context_firewall_failed` | issue-derived class remains separate | issue-derived results are not native-test replication |
| Bounded Micro-Reversal | planned | future shared repair helper | future reversal trace | `micro_reversal_budget_exhausted` | failed local edits must be reversible | reversal support is not broad autonomy |
| Homeostasis Risk Regulator | implemented | `controllergate/core/homeostasis.py` | `homeostasis_risk_state.json` | channel-specific blockers | pressure channels route or block work | risk routing is not a capability claim |
| Failure Memory Weighting | partial | existing failure-memory ledger | existing failure-memory outputs | `failure_memory_context_missing` | weights must be evidence-derived | memory weighting is not memory lift |
| Multi-File Patch Fragment Proposer | planned | future patch helper | future fragment proposal trace | `patch_fragment_scope_overflow` | fragments must stay source-only | fragment support is not general repair |
| Cryptographic Evidence Ledger Sealing | partial | manifests and proof ledgers | `SHA256SUMS.txt` and ledger files | `evidence_ledger_hash_mismatch` | manifests and ledgers match bytes | hashes preserve evidence; they do not prove claims |
