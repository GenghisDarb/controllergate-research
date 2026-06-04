# v1.8 Episodes 004-010 Memory-Relevance Replay Campaign

This campaign tests whether memory helps under replay-ready seeded controlled conditions. It does not run full scoring, does not demonstrate self-maintaining software, and does not convert seeded evidence into organic external repo evidence.

- Executed episodes: 7
- Deterministic replay-ready limited scoring episodes: 7
- Positive seeded memory-lift episodes: 6
- Negative episodes: 0
- Inconclusive episodes: 1
- Blocked episodes: 0
- Decision-time/outcome overlap count: 0
- Corruption episode count: 0
- Aggregate memory-lift assessment: `limited_seeded_controlled_memory_lift_criteria_met`
- Full scoring remains disallowed.
- ControllerGate full scoring remains `NOT_RUN`.
- Self-maintaining software remains undemonstrated.
- Validator-level hash mismatch is a valid deterministic target when replay/custody passes.
- Artifact-custody hash mismatch blocks scoring.

## Episode Results
### episode_004
- Failure signature: `MULTI_EPOCH_CONSTRAINT_FAILURE: version_readme_changelog`
- Classification: `positive_evidence_memory_lift_seeded_controlled_episode`
- No-memory result: `failed`
- Memory-enabled result: `passed`
- Memory-enabled outperformed no-memory: `true`
- Positive dimensions: `pass_fail`

### episode_005
- Failure signature: `KERNEL_CONSISTENCY_FAILURE: metadata_manifest+README+CHANGELOG`
- Classification: `positive_evidence_memory_lift_seeded_controlled_episode`
- No-memory result: `failed`
- Memory-enabled result: `passed`
- Memory-enabled outperformed no-memory: `true`
- Positive dimensions: `pass_fail`

### episode_006
- Failure signature: `STALE_MEMORY_INVERSION: version_rule_changed`
- Classification: `positive_evidence_memory_lift_seeded_controlled_episode`
- No-memory result: `failed`
- Memory-enabled result: `passed`
- Memory-enabled outperformed no-memory: `true`
- Positive dimensions: `pass_fail, stale_memory_quarantine`

### episode_007
- Failure signature: `DOWNSTREAM_CORRUPTION_RISK: manifest_passes_index_fails`
- Classification: `positive_evidence_memory_lift_seeded_controlled_episode`
- No-memory result: `failed`
- Memory-enabled result: `passed`
- Memory-enabled outperformed no-memory: `true`
- Positive dimensions: `pass_fail`

### episode_008
- Failure signature: `FALSE_POSITIVE_TRANSFER_TRAP: similar_error_different_fix`
- Classification: `positive_evidence_memory_lift_seeded_controlled_episode`
- No-memory result: `failed`
- Memory-enabled result: `passed`
- Memory-enabled outperformed no-memory: `true`
- Positive dimensions: `pass_fail, precision_gate_avoids_false_positive_transfer`

### episode_009
- Failure signature: `REPAIR_SPRAWL_RISK: manifest_hash_required_file`
- Classification: `positive_evidence_memory_lift_seeded_controlled_episode`
- No-memory result: `passed`
- Memory-enabled result: `passed`
- Memory-enabled outperformed no-memory: `true`
- Positive dimensions: `fewer_changed_files, smaller_patch`

### episode_010
- Failure signature: `SEEDED_RECURRENCE_CONSISTENCY_FAILURE: validator_registry`
- Classification: `inconclusive_equal_performance`
- No-memory result: `passed`
- Memory-enabled result: `passed`
- Memory-enabled outperformed no-memory: `false`
- Positive dimensions: `none`

## Evidence Interpretation

Positive evidence means replay gate passed, both paths were captured under identical replay conditions, memory-enabled outperformed no-memory on a preregistered dimension, and no corruption occurred.
Negative results are valid evidence against this memory design for these task classes when replay gate passes and the paths are comparable.
Blocked results reflect missing artifacts or replay failure, not capability failure.
Inconclusive results mean both paths were comparable but memory did not show a distinct advantage.
