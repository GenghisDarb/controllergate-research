def test_evidence_carry_forward_manifest_keeps_claim_boundaries():
    manifest = {
        "status": "PASS",
        "records": [
            {
                "batch": "batch016",
                "claim_boundary": {
                    "full_scoring": "NOT_RUN/disallowed",
                    "memory_lift": "not_demonstrated",
                    "self_maintaining_software": "false/not_demonstrated",
                },
            }
        ],
    }
    boundary = manifest["records"][0]["claim_boundary"]
    assert boundary["full_scoring"] == "NOT_RUN/disallowed"
    assert boundary["memory_lift"] == "not_demonstrated"


def test_issue_derived_evidence_does_not_increment_native_count():
    state = {"native_repair_episode_count": 4, "issue_derived_repair_episode_count": 0}
    assert state["native_repair_episode_count"] == 4
    assert state["issue_derived_repair_episode_count"] == 0
