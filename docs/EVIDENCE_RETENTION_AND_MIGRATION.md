# Evidence Retention and Migration

ControllerGate retains historical evidence until a verified replacement and an explicit migration proof both exist. A newer lane, manifest, or protocol does not by itself authorize deletion.

The canonical machine-readable catalog is `outputs/frontier/EVIDENCE_CATALOG.json`; the governing policy is `configs/controllergate_evidence_retention_policy.json`.

Storage classes distinguish current product state, current evidence manifests, historical evidence manifests, externally retained large payloads, and deprecated-but-retained records. Large payloads may remain outside Git when their external identity and cryptographic manifest are retained. Deletion eligibility must be recorded per catalog entry and currently remains false for every entry.

Migration requires all of the following:

1. A replacement evidence identity with verified byte custody.
2. A documented mapping from the historical record to the replacement.
3. Independent audit confirmation that claim boundaries and traceability are preserved.
4. An explicit deletion decision; absence from the current protocol is not a deletion decision.

Batch068h does not delete or rewrite historical evidence.
