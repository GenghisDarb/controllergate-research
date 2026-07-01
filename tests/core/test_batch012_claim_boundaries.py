from __future__ import annotations

from pathlib import Path


def test_batch012_config_keeps_claim_boundaries_closed():
    config = Path("configs/clean_replication_batch_012.json").read_text(encoding="utf-8")

    assert "NOT_RUN/disallowed" in config
    assert "false/not_demonstrated" in config
    assert "external_seeds_pending/targeted_prospective_seed_batch012.json" in config


def test_active_public_outputs_do_not_contain_blocked_internal_terms():
    blocked_terms = [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "Klein " + "twist",
        "RNA " + "primase",
        "OS" + "QN",
        "N" + "\u2248",
        "cym" + "atics",
        "res" + "onance",
        "chro" + "matin",
        "epi" + "genetic",
    ]
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/memory_lift_definition.md"),
        Path("docs/public_release_readiness.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/replication_protocol.md"),
        Path("docs/operational_gate_matrix.md"),
        Path("controllergate/core/targeted_seed.py"),
        Path("controllergate/core/issue_derived_harness.py"),
    ]

    for path in public_paths:
        text = path.read_text(encoding="utf-8")
        assert not [term for term in blocked_terms if term in text], path.as_posix()
