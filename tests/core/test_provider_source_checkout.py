from controllergate.core.provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL, provider_source_checkout_policy


def test_provider_source_checkout_policy_pins_source_commit():
    policy = provider_source_checkout_policy()
    assert policy["status"] == "PASS"
    assert policy["repo_url"] == SOURCE_REPO_URL
    assert policy["source_commit_sha"] == SOURCE_COMMIT_SHA
    assert policy["full_source_tree_copy_to_repo_allowed"] is False
