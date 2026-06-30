from controllergate.core.proof_chain import build_proof_chain_lock


def test_proof_chain_lock_links_patch_and_replay_hashes() -> None:
    chain = build_proof_chain_lock(
        [
            {"label": "candidate_commit", "sha256": "a" * 64},
            {"label": "assembled_patch", "sha256": "b" * 64},
            {"label": "duplicate_replay", "sha256": "c" * 64},
        ]
    )
    labels = [item["label"] for item in chain["chain"]]
    assert chain["status"] == "PASS"
    assert chain["hash_chain_valid"] is True
    assert labels == ["candidate_commit", "assembled_patch", "duplicate_replay"]
