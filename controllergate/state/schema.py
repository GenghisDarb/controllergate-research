from __future__ import annotations

SCHEMA_VERSION = 5

TABLES = (
    "runs", "run_manifests", "events", "reaction_tokens", "failed_reactions",
    "blockers", "reopen_conditions", "authorizations", "spent_nonces", "checkpoints",
    "worker_leases", "provider_identities", "candidate_identities", "proof_events",
    "count_records", "routing_memory_records", "truth_records", "patch_records",
    "connector_cursors", "candidate_queue", "notifications", "failed_branch_lineage",
    "stage_outputs", "broker_records", "release_decisions", "json_state_migrations",
    "reaction_contracts", "reaction_executions", "evidence_facts", "hypothesis_states",
    "constraint_states", "nogood_constraints", "access_leases", "compartments",
    "translocations", "junction_contracts", "global_inhibitors", "resource_budgets",
    "resource_events", "cleanup_events", "lineage_nodes", "authority_handovers",
    "variant_audits", "scaffold_changes", "source_ownership_tokens", "repair_license_tokens",
    "schema_migrations",
)

DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(
  run_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, status TEXT NOT NULL,
  blocker TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  terminal INTEGER NOT NULL DEFAULT 0, reopen_state TEXT, retry_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS run_manifests(run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE, manifest_json TEXT NOT NULL, manifest_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(
  event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
  event_type TEXT NOT NULL, parent_event_hash TEXT NOT NULL, input_token_hashes TEXT NOT NULL,
  output_token_hashes TEXT NOT NULL, status TEXT NOT NULL, blocker TEXT, created_at TEXT NOT NULL,
  worker_identity TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS reaction_tokens(
  token_hash TEXT PRIMARY KEY, token_type TEXT NOT NULL, candidate_id TEXT NOT NULL,
  run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE, producer_event TEXT NOT NULL,
  input_token_hashes TEXT NOT NULL, payload_identity TEXT NOT NULL,
  independent_verifier TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS failed_reactions(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(run_id), event_id TEXT NOT NULL, blocker TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS blockers(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(run_id), blocker TEXT NOT NULL, active INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reopen_conditions(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES runs(run_id), condition_json TEXT NOT NULL, satisfied INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS authorizations(authorization_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), scope_json TEXT NOT NULL, expires_at TEXT, consumed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS spent_nonces(nonce TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), spent_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checkpoints(run_id TEXT PRIMARY KEY REFERENCES runs(run_id), stage TEXT NOT NULL, event_hash TEXT NOT NULL, state_json TEXT NOT NULL, committed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS worker_leases(run_id TEXT PRIMARY KEY REFERENCES runs(run_id), worker_identity TEXT NOT NULL, acquired_at REAL NOT NULL, expires_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS provider_identities(provider_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), identity_json TEXT NOT NULL, classification TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS candidate_identities(candidate_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), identity_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS proof_events(proof_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), candidate_id TEXT NOT NULL, proof_type TEXT NOT NULL, proof_json TEXT NOT NULL, parent_hash TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS count_records(count_hash TEXT PRIMARY KEY, proof_hash TEXT NOT NULL REFERENCES proof_events(proof_hash), candidate_id TEXT NOT NULL UNIQUE, repair_class TEXT NOT NULL, decision TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS routing_memory_records(memory_hash TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, structural_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS truth_records(truth_hash TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, sealed_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS patch_records(patch_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), candidate_id TEXT NOT NULL, path TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS connector_cursors(connector_id TEXT PRIMARY KEY, cursor TEXT, last_successful_read TEXT, retry_count INTEGER NOT NULL DEFAULT 0, next_retry_time REAL, circuit_state TEXT NOT NULL DEFAULT 'CLOSED');
CREATE TABLE IF NOT EXISTS candidate_queue(event_hash TEXT PRIMARY KEY, connector_id TEXT NOT NULL, event_json TEXT NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notifications(notification_id TEXT PRIMARY KEY, connector_id TEXT NOT NULL, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, delivered INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS failed_branch_lineage(
  branch_hash TEXT PRIMARY KEY, attempt_identity TEXT NOT NULL, parent_event TEXT NOT NULL,
  input_tokens TEXT NOT NULL, candidate_id TEXT NOT NULL, source_identity TEXT NOT NULL,
  provider_seal TEXT NOT NULL, operation_identity TEXT NOT NULL, patch_hash TEXT,
  failure_class TEXT NOT NULL, new_information TEXT NOT NULL, rollback_target TEXT NOT NULL,
  branch_closed INTEGER NOT NULL, count_increment INTEGER NOT NULL DEFAULT 0,
  reopen_condition TEXT NOT NULL, next_legal_action TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stage_outputs(
  event_id TEXT PRIMARY KEY REFERENCES events(event_id), run_id TEXT NOT NULL REFERENCES runs(run_id),
  stage_id TEXT NOT NULL, input_identity TEXT NOT NULL, output_json TEXT NOT NULL, output_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS broker_records(
  record_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), operation_id TEXT NOT NULL UNIQUE,
  stage_id TEXT NOT NULL, authorization_id TEXT NOT NULL, nonce TEXT NOT NULL UNIQUE,
  record_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS release_decisions(
  decision_hash TEXT PRIMARY KEY, status TEXT NOT NULL, package_version TEXT NOT NULL,
  parent_hash TEXT NOT NULL, decision_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS json_state_migrations(
  source_hash TEXT PRIMARY KEY, source_path TEXT NOT NULL, imported_run_id TEXT NOT NULL,
  result_hash TEXT NOT NULL, migrated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reaction_contracts(
  contract_hash TEXT PRIMARY KEY, reaction_type TEXT NOT NULL, contract_json TEXT NOT NULL,
  verifier_identity TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reaction_executions(
  execution_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  contract_hash TEXT NOT NULL REFERENCES reaction_contracts(contract_hash), stage TEXT NOT NULL,
  input_hash TEXT NOT NULL, output_hash TEXT, status TEXT NOT NULL, blocker TEXT,
  parent_execution_hash TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence_facts(
  fact_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), subject TEXT NOT NULL,
  predicate TEXT NOT NULL, object_json TEXT NOT NULL, epistemic_state TEXT NOT NULL,
  decision_time_safe INTEGER NOT NULL, source_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hypothesis_states(
  hypothesis_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  hypothesis_json TEXT NOT NULL, state TEXT NOT NULL, direct_support_hash TEXT,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS constraint_states(
  constraint_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  kind TEXT NOT NULL, constraint_json TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nogood_constraints(
  nogood_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  facts_json TEXT NOT NULL, learned_from_execution TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS access_leases(
  lease_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), region TEXT NOT NULL,
  mode TEXT NOT NULL, authorization_hash TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0,
  resealed INTEGER NOT NULL DEFAULT 0, expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS compartments(
  compartment_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  compartment_type TEXT NOT NULL, identity_json TEXT NOT NULL, state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS translocations(
  receipt_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  source_compartment TEXT NOT NULL, destination_compartment TEXT NOT NULL,
  payload_hash TEXT NOT NULL, conserved INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS junction_contracts(
  junction_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  junction_class TEXT NOT NULL, contract_json TEXT NOT NULL, state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS global_inhibitors(
  inhibitor_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  checkpoint_id TEXT NOT NULL, active INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resource_budgets(
  budget_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  resource_key TEXT NOT NULL, limit_value INTEGER NOT NULL, remaining_value INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS resource_events(
  resource_event_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  budget_hash TEXT NOT NULL REFERENCES resource_budgets(budget_hash), delta INTEGER NOT NULL,
  reason TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cleanup_events(
  cleanup_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  target_hash TEXT NOT NULL, cleanup_class TEXT NOT NULL, evidence_preserved INTEGER NOT NULL,
  status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lineage_nodes(
  node_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  node_type TEXT NOT NULL, parent_hash TEXT, lineage_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS authority_handovers(
  handover_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  prior_authority_hash TEXT NOT NULL, new_authority_hash TEXT NOT NULL,
  retained_state_hash TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS variant_audits(
  audit_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  variant_type TEXT NOT NULL, effect_class TEXT NOT NULL, audit_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scaffold_changes(
  change_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  component TEXT NOT NULL, prior_hash TEXT NOT NULL, new_hash TEXT NOT NULL,
  reversible INTEGER NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_ownership_tokens(
  token_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  candidate_id TEXT NOT NULL, evidence_json TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS repair_license_tokens(
  token_hash TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id),
  candidate_id TEXT NOT NULL, source_ownership_hash TEXT NOT NULL,
  license_json TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0
);
"""
