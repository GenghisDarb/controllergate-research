from __future__ import annotations

from controllergate.core.clean_repair import build_source_context_handoff


def test_source_context_handoff_records_context_and_patch_hash():
    handoff = build_source_context_handoff(
        {"candidate_id": "candidate"},
        {"semantic_failure_signature_hash": "f" * 64, "context_capsule_hash": "c" * 64},
        {"candidate_id": "candidate", "patchable_source_files": ["src/a.py"]},
        {"patch_candidate_generated": True, "patch_sha256": "p" * 64},
        {"status": "PASS"},
        {"command_record": {"normalized_output_sha256": "v" * 64}},
        None,
    )

    assert handoff["status"] == "PASS"
    assert handoff["context_capsule_hash"] == "c" * 64
    assert handoff["patch_hash"] == "p" * 64
