# Batch060c repository structure recommendations

Working well:

- Versioned outputs preserve evidence custody.
- Shared manifest and official-ingest helpers are already useful.
- Manual artifact custody remains clear and should not be simplified away.

Repeated friction:

- Audit scripts repeat git-status quarantine and claim-boundary checks.
- Workflows repeat byte custody, test, audit, and artifact packaging steps.
- Batch names are long and easy to confuse.

Highest-payoff future work:

- `batch06x_artifact_ingestion_utility_consolidation`
- `batch06x_audit_boilerplate_deduplication`
- `batch06x_provider_capsule_registry_consolidation`
- `batch06x_amds_bridge_registry_consolidation`
- `batch06x_workflow_template_hardening`
- `batch06x_repo_topology_cleanup_review`

Do not simplify safety gates that enforce manual artifact custody, forbidden evidence exclusion, duplicate replay before count, or claim boundaries.
