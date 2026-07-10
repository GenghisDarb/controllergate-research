from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate_batch069b_recoverable_provider_command_followup.py"


def load_batch069b_module():
    spec = importlib.util.spec_from_file_location("batch069b_generator", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_batch069b_active_recoverable_set_excludes_audioread() -> None:
    module = load_batch069b_module()
    assert module.ACTIVE_RECOVERABLE == [
        "codex_wave3_aio_libs_aiosmtpd_issues_403",
        "codex_wave3_alpha_unito_streamflow_issues_1100",
        "codex_wave3_aws_neuron_nki_library_issues_5",
        "codex_wave3_biface_i18n_issues_86",
    ]
    assert module.AUDIOREAD not in module.ACTIVE_RECOVERABLE


def test_universal_interlock_manifest_contains_count_gate_and_duplicate_replay() -> None:
    module = load_batch069b_module()
    ids = {record["interlock_id"] for record in module.universal_interlock_manifest()["records"]}
    assert "count_gate" in ids
    assert "duplicate_clean_replay" in ids
    assert "command_translation" in ids


def test_batch069b_public_summary_preserves_claim_boundary() -> None:
    module = load_batch069b_module()
    assert "not repair proof" in module.PUBLIC_SUMMARY
    assert "Full scoring remains NOT_RUN/disallowed" in module.PUBLIC_SUMMARY
    assert "Self-maintaining software remains false/not_demonstrated" in module.PUBLIC_SUMMARY


def test_runtime_connector_record_is_explicit_for_nki() -> None:
    module = load_batch069b_module()
    record = module.runtime_connector_record(
        {
            "candidate_id": "codex_wave3_aws_neuron_nki_library_issues_5",
            "exact_blocker": "nki_library_runtime_connector_required",
            "reopen_condition": "approved_aws_neuron_nki_runtime_connector",
        }
    )
    assert record["required_connector"] == "aws_neuron_or_nki_runtime_connector"
    assert record["approval_condition"] == "connector_identity_and_runtime_output_hashes_verified"
