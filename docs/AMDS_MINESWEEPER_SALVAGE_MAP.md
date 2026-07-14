# AMDS Minesweeper design salvage map

ControllerGate reviewed the pinned `AI-Minesweeper-Discovery-Framework` commit `bcd4d6c3bcbd60502e04116f4d6b72377864e6e7` as a read-only design and adversarial source. It is not a runtime dependency, its package is not imported, and its documentation claims are not treated as executed evidence.

## Concepts retained in neutral engineering form

- Falsifiable hypothesis cells with stable identities.
- Typed hard and soft constraints propagated to a fixed point.
- Mutual-exclusion, implication, exact-count, at-most, and dependency rules.
- Probe selection by expected information gain when calibrated likelihoods exist.
- Deterministic minimax partition selection otherwise.
- Explicit probe contracts with cost, risk, and network budgets.
- Bounded meta-cell decomposition for unresolved coarse hypotheses.
- Failed-branch lineage and checkpointed truth maintenance.
- Traceable decision-frame state and safe abstention when no legal discriminating probe remains.

## Patterns rejected

- Test-mode or other access to hidden truth.
- Revealing safe cells from hidden markers.
- First-hidden-cell or forced lowest-risk fallbacks.
- Heuristic confidence adjustments treated as evidence.
- Confidence updates without a registered calibration or scoring basis.
- Causal-family names in probe identifiers, scripts, paths, environment variables, sentinels, or output fields.
- Duplicated boards presented as independent diagnosis lanes.
- Shared mutable state between parallel lanes.
- Language-model suggestions treated as causal certainty.
- Any fallback decision without proof or exact abstention.

Only the design concepts above were translated. No source file was copied wholesale and no component of the reviewed repository is product-reachable.
