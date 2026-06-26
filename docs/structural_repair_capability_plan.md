# Structural Repair Capability Plan

This plan records the neutral engineering controls used by v2.29 before a
bounded source-only repair attempt.

## Active mechanisms

- AST Dependency Closure: parse the buggy tree and identify source files,
  imports, definitions, and call-path evidence connected to the reviewed target
  command.
- Context Pinching Filter: build a compact hash-anchored repair capsule from
  approved decision-time evidence only.
- Failure Memory Weight Ledger: record diagnostic loci and outcomes for the
  exact candidate/failure signature without claiming aggregate lift.
- Fragmented Patch Assembly Gate: permit at most three audited source-only
  fragments assembled into one final patch.
- Pre/Post Handoff Consistency Gate: keep the candidate, commit, target
  command, failure signature, context hash, patch bytes, and validation result
  aligned.

Full scoring is not run. Current protocol remains v2.13.
