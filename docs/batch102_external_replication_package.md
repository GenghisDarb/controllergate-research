# Batch102 external replication package

This package defines a public, non-authorizing replication path for the Batch102 fresh-execution contract. It contains the v4 candidate/cell contracts, semantic projection registry, provider exactness rules, synthetic receipt examples, and audit commands. It excludes private truth, private ordering data, accepted fixes, gold patches, and repair authority.

An external replicator must run each candidate operation through the canonical broker, retain two independently verified receipts per cell, preserve source/test trees, and report blocked exact providers honestly. A replication result cannot change repair counts, protocol v2.19, package version `0.2.0b2.dev0`, or the Product Beta boundary.

Suggested verification:

1. Run `python -m pytest tests/test_batch102_fresh_execution_and_capsules.py tests/test_batch102_contract_freeze.py tests/test_batch102_causal_interventions.py -q`.
2. Dispatch the Batch102 workflow from an immutable commit.
3. Verify every receipt with `scripts/verify_batch102_fresh_execution_receipts.py`.
4. Keep any truth bundle outside Actions; perform the local join only after terminal sealing.

Status: `PROTOCOL_READY`. External replication has not occurred.
