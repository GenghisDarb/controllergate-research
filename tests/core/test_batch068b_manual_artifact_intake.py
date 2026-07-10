from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate_batch068b_manual_artifact_and_external_source_custody_intake.py"


def load_batch068b_module():
    spec = importlib.util.spec_from_file_location("batch068b_generator", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_batch068b_manual_candidate_set_is_three() -> None:
    module = load_batch068b_module()
    assert sorted(module.MANUAL_CANDIDATES) == [
        "codex_wave3_aio_libs_aiosmtpd_issues_403",
        "codex_wave3_alpha_unito_streamflow_issues_1100",
        "codex_wave3_biface_i18n_issues_86",
    ]


def test_batch068b_nki_connector_candidate_is_separate() -> None:
    module = load_batch068b_module()
    assert module.NKI_CANDIDATE == "codex_wave3_aws_neuron_nki_library_issues_5"
    assert module.NKI_CANDIDATE not in module.MANUAL_CANDIDATES


def test_batch068b_public_summary_is_not_repair_proof() -> None:
    module = load_batch068b_module()
    assert "not repair proof" in module.PUBLIC_SUMMARY
    assert "Full scoring remains NOT_RUN/disallowed" in module.PUBLIC_SUMMARY
    assert "Self-maintaining software remains false/not_demonstrated" in module.PUBLIC_SUMMARY


def test_native_artifact_template_forbids_patch_guidance() -> None:
    from controllergate.core.manual_artifact_intake import native_command_artifact_template

    template = native_command_artifact_template()
    assert "patch_guidance" in template["forbidden_use"]
    assert template["gold_fixed_future_exclusion"] is True
    assert template["issue_comment_fix_text_exclusion"] is True
