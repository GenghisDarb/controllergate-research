from pathlib import Path

from controllergate.core.provider_input_bundle import build_provider_input_bundle, validate_provider_input_bundle


def test_provider_input_bundle_excludes_forbidden_data():
    bundle = build_provider_input_bundle(
        lock_path=Path("external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json"),
        redacted_issue_snapshot_hash="0" * 64,
        target_command_manifest_hash="1" * 64,
        source_repo_url="https://github.com/akaihola/darker",
        source_commit_sha="a2d13656adfaa010fb6c7339087f3347ad2b815a",
        allowed_command_variants=["GIT_DIR=.git python -m darker --check src"],
    )
    audit = validate_provider_input_bundle(bundle)
    assert audit["status"] == "PASS"
    assert audit["write_credentials_included"] is False
    assert audit["secrets_included"] is False
    assert not audit["forbidden_keys_present"]
