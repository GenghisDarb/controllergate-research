# Structural Repair Capability Plan

This plan records neutral engineering controls used by the v2.29 and v2.30
bounded repair lanes.

## Active mechanisms

- AST Dependency Closure: restrict patchable source files using executed-scope
  and buggy-tree AST evidence.
- Context Pinching Filter: build a compact hash-anchored repair capsule from
  approved decision-time evidence only.
- Failure Memory Weight Ledger: record diagnostic loci and outcomes for the
  exact candidate/failure signature without claiming aggregate lift.
- Fragmented Patch Assembly Gate: permit at most three audited source-only
  fragments assembled into one final patch.
- Pre/Post Handoff Consistency Gate: keep the candidate, commit, target
  command, semantic failure signature, context hash, patch bytes, and
  validation result aligned.
- Failure Signature Canonicalization: preserve historical text hashes while
  gating repair on three clean matching semantic captures.

Full scoring is not run. Current protocol remains v2.13.
