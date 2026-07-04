# Artifact packaging policy

The primary post-v2.37 artifact remains thin and delta-oriented. Batch024 carries prior evidence by artifact identity and lineage records.

## Current operational gate status

- Batch023 verified Docker provider activation, Python 3.7 preflight, provider output transport, and manual dependency-lock installation in the official artifact.
- Batch023 blocked at source workspace materialization pending an approved Provider Workspace Bridge.
- Batch024 adds the Provider Workspace Bridge, Provider Input Bundle, Provider Output Bundle, Provider Workspace Transport, and Provider Source Materialization records.
- The runtime must conform to the reviewed lock; the lock is not loosened to fit the runtime.
- Provider labels are insufficient; actual Python and pip versions must be recorded inside the provider.
- External source execution must not receive write credentials or secrets.
- Structured Fragility Diagnostic is diagnostic and cannot replace empirical gates.
- Repair cannot activate before bounded materialization and Target-Intent Alignment.
- Active Search-Space Geometry may prioritize probes but cannot replace empirical evidence.
- Single-system navigation and coupled-interlock extension remain separate.
- Coupled-interlock extension remains blocked until interlock invariants are computed.
- Confirmed external native repair episodes remain `4`.
- Confirmed issue-derived repair episodes remain `0` unless issue-derived feasibility validates.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Hallucination elimination, absolute uncrashability, and production runtime readiness are not claimed.
