# Reactome–ControllerGate completion status

## Current result

Reactome integration is structurally advanced but is not complete. Completion requires cross-candidate gain at R5; prospective validation remains a separate future R6 requirement.

| Level | Meaning | Current status |
|---|---|---|
| R0 | Source custody | `PASS` |
| R1 | Lossless RPIR graph | `PASS_WITH_FORMAT_LIMITATIONS` |
| R2 | Source-bound translation | `PASS_WITH_GROUNDING_CAVEATS` |
| R3 | Executable shadow | `PASS_NONAUTHORIZING_SHADOW` |
| R4 | Causal-planning gain | `NOT_ESTABLISHED` |
| R5 | Cross-candidate generalization | `NOT_ESTABLISHED` |
| R6 | Prospective validation | `NOT_RUN` |

## Structural coverage

The locked public structured source covers 2,916 pathway occurrences, 16,814 reaction occurrences, 46 ControllerGate primitive classes, and 29 source-family indexes. Every current reaction mapping preserves its raw Reactome chapter identity, source object, source hash, wrapped field state, and public-safe origin classification. Source-family normalization is an indexing layer only; it is not a biological-equivalence claim.

The current mapping authority derives primitives from reaction relations such as inputs, outputs, catalysts, regulators, compartments, event ordering, variants, failed reactions, entity sets, and complex membership. The older chapter-position slicing routine remains only as a historical synthetic coverage fixture and has no current mapping authority.

## Execution boundary

Reaction-specific shadow operations cover source identity, compartment and prerequisite materialization, activation and inhibitor gates, ordered and parallel routes, failed-branch capture, rollback, duplicate replay, proof-ledger commit, and safe termination. These operations cannot write a causal terminal, create an ownership fact, authorize a patch, change a repair count, read sealed truth, or promote a release.

## Causal-planning boundary

R4 requires a frozen, equal-budget Reactome-on/off ablation. A Reactome-enabled arm must improve at least one preregistered metric over canonical AMDS on at least two candidates without worsening false attribution, unsafe authority, truth leakage, or private-data leakage. R5 additionally requires replication across at least three candidates, two causal families, and more than one repository/provider class. Until those gates pass, structural coverage and executable shadow must not be described as causal gain.
