from __future__ import annotations


ROLE_CONTRACTS = {
    "source_revision": ("commit_sha", "commit_object_type", "repository_url", "source_revision_timestamp"),
    "source_tree": ("source_file_hashes", "source_tree_hash", "dirty_state", "submodule_state"),
    "test_tree": ("test_file_hashes", "collection_identity", "support_file_hashes", "test_tree_hash"),
    "provider_runtime_abi": ("interpreter_hash", "python_version", "abi_tags", "platform", "distribution_graph_hash"),
    "target_reproducer": ("target_identity", "collection_result", "failure_signature_schema", "project_level_reproducer"),
    "command": ("argv", "cwd", "environment_allowlist", "timeout_seconds", "network_policy", "command_authority"),
    "runner": ("executable_hash", "entrypoint", "process_parent", "interpreter_hash", "runner_version"),
    "harness": ("wrapper_hash", "plugin_set", "fixture_origins", "translation_layers"),
    "incident_snapshot": ("raw_log_hash", "structured_exception", "import_origins", "captured_at", "frame_hashes"),
    "proof_release_parent": ("sqlite_run_parent", "proof_ledger_parent", "release_state_parent", "public_state_parent"),
}

ROLE_NAMES = tuple(ROLE_CONTRACTS)
