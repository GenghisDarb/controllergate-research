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


## v2.31 consolidation status


v2.31 records the first scoreable external repair episode as a consolidated engineering artifact. The active repair-control mechanisms remain bounded and diagnostic: semantic failure signature, source-only patch safety, target validation, duplicate clean replay, and proof-ledger custody.

No v2.31 repair, target-test execution, patch generation, or new candidate selection is authorized. The next safe expansion is more reviewed registry candidates or a prospective second repair lane.
