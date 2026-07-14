from __future__ import annotations

SCHEMA_VERSION = 1

TABLES = (
    "runs", "run_manifests", "events", "reaction_tokens", "failed_reactions",
    "blockers", "reopen_conditions", "authorizations", "spent_nonces", "checkpoints",
    "worker_leases", "provider_identities", "candidate_identities", "proof_events",
    "count_records", "routing_memory_records", "truth_records", "patch_records",
    "connector_cursors", "notifications", "schema_migrations",
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
CREATE TABLE IF NOT EXISTS notifications(notification_id TEXT PRIMARY KEY, connector_id TEXT NOT NULL, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, delivered INTEGER NOT NULL DEFAULT 0);
"""
