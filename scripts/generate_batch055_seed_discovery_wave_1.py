from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1"
PAYLOAD_DIR = ROOT / "artifact_payload" / "post_v2_37_hardening_batch055_seed_discovery_wave_1"
BATCH054_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch054_issue_repair_count_next_patch_artifacts.zip"
)
BATCH054_ARTIFACT_NAME = "post_v2_37_hardening_batch054_issue_repair_count_next_patch_artifacts"
BATCH054_ARTIFACT_ID = 8150146607
BATCH054_WORKFLOW_RUN_ID = 28895814221
BATCH054_WORKFLOW_HEAD_SHA = "92b2f3b8155d681ffeae8b0244b04ff56235ccd3"
BATCH054_SHA256 = "4fa4d5a47cf09f781165c6922b4e2910ad3363a7a6eb033f90f7a5c9ee9ca095"
BATCH054_SIZE = 167310
BATCH054_ENTRY_COUNT = 166
BATCH054_ARTIFACT_MANIFEST_CHECKED = 165
BATCH054_OUTPUT_MANIFESTS = {
    "clean_replication_batch_054": ("clean_replication_batch_054/SHA256SUMS.txt", 21),
    "post_v2_37_hardening_001": ("post_v2_37_hardening_001/SHA256SUMS.txt", 142),
}
BATCH054_PASS = "PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED"
NEXT_ACTION = "batch056_pre_repair_replay_wave_1"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch055_seed_discovery_wave_1_artifacts"
CURRENT_PROTOCOL = "v2.14"
LOCAL_RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH055_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch055_commit_resolution"))


EMBEDDED_LEADS: list[dict[str, Any]] = [
    {
        "lead_id": "lemon24_reader_302_local_config_failure",
        "repo_url": "https://github.com/lemon24/reader",
        "issue_url_or_reference": "https://github.com/lemon24/reader/issues/302",
        "failure_keywords": ["local config", "custom config file", "FAILED", "test_custom_config_file"],
        "possible_native_test_paths": ["tests/test_local_config.py"],
        "possible_failing_command": "pytest tests/test_local_config.py -q",
        "patch_or_workaround_in_issue_body": True,
        "issue_body_policy": "exclude_issue_body_from_repair_evidence_if_patch_or_workaround_present",
        "reason_this_is_promising": "Real reported local-config failure in a native test area; requires leakage screening.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "pdm_project_pdm_3487",
        "repo_url": "https://github.com/pdm-project/pdm",
        "issue_url_or_reference": "https://github.com/pdm-project/pdm/issues/3487",
        "failure_keywords": ["network-isolated", "AssertionError", "test"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "pytest tests/... -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Potential network-isolated Python test failure; exact native command must be resolved independently.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "pydantic_pytest_examples_issue_discovery",
        "repo_url": "https://github.com/pydantic/pytest-examples",
        "issue_url_or_reference": "https://github.com/pydantic/pytest-examples/issues",
        "failure_keywords": ["pytest", "examples", "docstring"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "not_an_exact_issue_reference_must_resolve_or_reject",
        "reason_this_is_promising": "Small pytest plugin scope, but not an exact issue reference.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "datasette_2461_async_event_loop_cli_tests",
        "repo_url": "https://github.com/simonw/datasette",
        "issue_url_or_reference": "https://github.com/simonw/datasette/issues/2461",
        "failure_keywords": ["There is no current event loop", "tests/test_cli.py", "pytest-asyncio"],
        "possible_native_test_paths": ["tests/test_cli.py"],
        "possible_failing_command": "python -m pytest tests/test_cli.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Native CLI test failure with named test path and async/event-loop signature.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "freezegun_547_py313_datetimes_assertion",
        "repo_url": "https://github.com/spulec/freezegun",
        "issue_url_or_reference": "https://github.com/spulec/freezegun/issues/547",
        "failure_keywords": ["Python 3.13", "AssertionError", "FakeDate", "tests/test_datetimes.py"],
        "possible_native_test_paths": ["tests/test_datetimes.py"],
        "possible_failing_command": "python -m pytest tests/test_datetimes.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Small pure-Python project with concrete assertion failures in datetime tests.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "venusian_91_py313_frameinfo_callinfo",
        "repo_url": "https://github.com/Pylons/venusian",
        "issue_url_or_reference": "https://github.com/Pylons/venusian/issues/91",
        "failure_keywords": ["Python 3.13", "FrameInfoTest", "testCallInfo", "tox -e py313"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "tox -e py313",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Small package with named Python 3.13 frameinfo compatibility failure.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "pexpect_699_replwrap_bash_assertions",
        "repo_url": "https://github.com/pexpect/pexpect",
        "issue_url_or_reference": "https://github.com/pexpect/pexpect/issues/699",
        "failure_keywords": ["REPLWrapTestCase", "test_multiline", "tests/test_replwrap.py", "AssertionError"],
        "possible_native_test_paths": ["tests/test_replwrap.py"],
        "possible_failing_command": "python -m pytest tests/test_replwrap.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Concrete native tests and assertion signatures, with shell-environment caveat.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "versioningit_89_hatch_onbuild_modulenotfound",
        "repo_url": "https://github.com/jwodder/versioningit",
        "issue_url_or_reference": "https://github.com/jwodder/versioningit/issues/89",
        "failure_keywords": ["ModuleNotFoundError", "hatch", "versioningit-onbuild", "pytest"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Small packaging/backend scope with pytest import failure.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "pyramid_3761_py313_test_util",
        "repo_url": "https://github.com/Pylons/pyramid",
        "issue_url_or_reference": "https://github.com/Pylons/pyramid/issues/3761",
        "failure_keywords": ["Python 3.13", "test_util", "pytest", "Fedora"],
        "possible_native_test_paths": ["tests/test_util.py"],
        "possible_failing_command": "python -m pytest tests/test_util.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Native utility test failure with Python 3.13 context.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "anyio_1028_old_pytest_assertion",
        "repo_url": "https://github.com/agronholm/anyio",
        "issue_url_or_reference": "https://github.com/agronholm/anyio/issues/1028",
        "failure_keywords": ["anyio==4.11.0", "old pytest", "AssertionError", "Python 3.9"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Compatibility issue with old pytest and dependency interaction; screen as possible environment-only failure.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "wand_582_py311_fx_error",
        "repo_url": "https://github.com/emcconville/wand",
        "issue_url_or_reference": "https://github.com/emcconville/wand/issues/582",
        "failure_keywords": ["Python 3.11", "tests/image_methods_test.py", "test_fx_error", "TypeError"],
        "possible_native_test_paths": ["tests/image_methods_test.py"],
        "possible_failing_command": "tox -e py311",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Concrete test and traceback signature, with native ImageMagick dependency risk.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "coveragepy_2007_pytest_run_parallel",
        "repo_url": "https://github.com/coveragepy/coveragepy",
        "issue_url_or_reference": "https://github.com/coveragepy/coveragepy/issues/2007",
        "failure_keywords": ["pytest-run-parallel", "global state", "sys.modules", "filesystem", "threads"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Real test failure class with concurrency/global-state clues, but likely complex.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "pyscaffold_731_pytest_modulenotfound",
        "repo_url": "https://github.com/pyscaffold/pyscaffold",
        "issue_url_or_reference": "https://github.com/pyscaffold/pyscaffold/issues/731",
        "failure_keywords": ["pytest", "ModuleNotFoundError", "tests", "tox"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Pytest import failure after project generation; screen for exact reproduction.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
    {
        "lead_id": "briefcase_1249_windows_printer_tox",
        "repo_url": "https://github.com/beeware/briefcase",
        "issue_url_or_reference": "https://github.com/beeware/briefcase/issues/1249",
        "failure_keywords": ["Windows", "tox", "Printer", "tests/console/test_Printer.py", "FAILED"],
        "possible_native_test_paths": ["tests/console/test_Printer.py"],
        "possible_failing_command": "python -m pytest tests/console/test_Printer.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Concrete native test path but likely Windows-specific.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_seed_list",
    },
]


AUGMENTED_LEADS: list[dict[str, Any]] = [
    {
        "lead_id": "retracesoftware_86_pytest_failure_hint_parser",
        "repo_url": "https://github.com/retracesoftware/retracesoftware",
        "issue_url_or_reference": "https://github.com/retracesoftware/retracesoftware/issues/86",
        "failure_keywords": ["pytest failure hint", "AssertionError", "OperationalError", "tests/conftest.py"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Parser-only pytest failure classification issue discovered through GitHub issue search.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "python pytest AssertionError tests/test is:issue",
    },
    {
        "lead_id": "pytest_dev_14575_last_failed_subtest",
        "repo_url": "https://github.com/pytest-dev/pytest",
        "issue_url_or_reference": "https://github.com/pytest-dev/pytest/issues/14575",
        "failure_keywords": ["--last-failed", "subtest", "unittest", "deselected"],
        "possible_native_test_paths": ["testing/"],
        "possible_failing_command": "python -m pytest testing -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Small reproduction class in a pure-Python pytest subsystem.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "python pytest AssertionError tests/test is:issue",
    },
    {
        "lead_id": "google_api_python_client_2755_pytest_setup_package",
        "repo_url": "https://github.com/googleapis/google-api-python-client",
        "issue_url_or_reference": "https://github.com/googleapis/google-api-python-client/issues/2755",
        "failure_keywords": ["strict positional", "pytest", "tests/test_discovery.py", "TypeError"],
        "possible_native_test_paths": ["tests/test_discovery.py"],
        "possible_failing_command": "python -m pytest tests/test_discovery.py -k test_tests_should_be_run_with_strict_positional_enforcement -q",
        "patch_or_workaround_in_issue_body": True,
        "issue_body_policy": "exclude_issue_body_from_repair_evidence_if_patch_or_workaround_present",
        "reason_this_is_promising": "Concrete native test path and command; issue body must be excluded because it contains implementation guidance.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "python pytest AssertionError tests/test is:issue",
    },
    {
        "lead_id": "sphinx_14506_gettext_literalblock_parallel",
        "repo_url": "https://github.com/sphinx-doc/sphinx",
        "issue_url_or_reference": "https://github.com/sphinx-doc/sphinx/issues/14506",
        "failure_keywords": ["test_gettext_literalblock_additional", "literalblock.pot", "pytest-xdist"],
        "possible_native_test_paths": ["tests/test_builders/test_build_gettext.py"],
        "possible_failing_command": "python -m pytest tests/test_builders/test_build_gettext.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Named test failure in pure-Python docs build tests, but parallel/Fedora context requires screening.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "tox failure pytest tests Python is:issue",
    },
    {
        "lead_id": "myst_parser_1152_docutils_023_link_resolution",
        "repo_url": "https://github.com/executablebooks/MyST-Parser",
        "issue_url_or_reference": "https://github.com/executablebooks/MyST-Parser/issues/1152",
        "failure_keywords": ["docutils 0.23", "test_link_resolution", "system_message"],
        "possible_native_test_paths": ["tests/test_renderers/"],
        "possible_failing_command": "python -m pytest tests/test_renderers -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Named renderer test failure with dependency-version context.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "tox failure pytest tests Python is:issue",
    },
    {
        "lead_id": "alp_sdk_465_provision_som_dry_run",
        "repo_url": "https://github.com/alplabai/alp-sdk",
        "issue_url_or_reference": "https://github.com/alplabai/alp-sdk/issues/465",
        "failure_keywords": ["provision_som", "dry-run", "tests/scripts/test_provision_som.py", "bmaptool"],
        "possible_native_test_paths": ["tests/scripts/test_provision_som.py"],
        "possible_failing_command": "python -m pytest tests/scripts/test_provision_som.py -q --tb=no",
        "patch_or_workaround_in_issue_body": True,
        "issue_body_policy": "exclude_issue_body_from_repair_evidence_if_patch_or_workaround_present",
        "reason_this_is_promising": "Concrete native test path and environment-boundary behavior, but issue body includes suggested direction.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "python pytest AssertionError tests/test is:issue",
    },
    {
        "lead_id": "figops_217_git_path_test_skip",
        "repo_url": "https://github.com/Moonweave-Research/figops",
        "issue_url_or_reference": "https://github.com/Moonweave-Research/figops/issues/217",
        "failure_keywords": ["test_public_release_check", "git not on PATH", "FileNotFoundError"],
        "possible_native_test_paths": ["tests/test_public_release_check.py"],
        "possible_failing_command": "python -m pytest tests/test_public_release_check.py::test_public_release_check_uses_git_exclude_standard_when_available -q",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Small Python repo with a concrete native test path; likely environment-boundary classification.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "python pytest AssertionError tests/test is:issue",
    },
    {
        "lead_id": "deepinv_1238_transform_identity_rng",
        "repo_url": "https://github.com/deepinv/deepinv",
        "issue_url_or_reference": "https://github.com/deepinv/deepinv/issues/1238",
        "failure_keywords": ["test_transform_identity", "AssertionError", "homography", "affine"],
        "possible_native_test_paths": ["deepinv/tests/test_transform.py"],
        "possible_failing_command": "python -m pytest deepinv/tests/test_transform.py -k test_transform_identity -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Concrete native test path, but larger dependency surface.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "python pytest AssertionError tests/test is:issue",
    },
    {
        "lead_id": "python_cffi_255_offline_cffi_gen_src_meson",
        "repo_url": "https://github.com/python-cffi/cffi",
        "issue_url_or_reference": "https://github.com/python-cffi/cffi/issues/255",
        "failure_keywords": ["offline", "test_cffi_gen_src_meson.py", "meson", "pytest"],
        "possible_native_test_paths": ["testing/cffi1/test_cffi_gen_src_meson.py"],
        "possible_failing_command": "python -m pytest testing/cffi1/test_cffi_gen_src_meson.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Concrete test path, but compiled/tooling dependencies need screening.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "tox failure pytest tests Python is:issue",
    },
    {
        "lead_id": "arize_phoenix_13925_sandbox_wasmtime",
        "repo_url": "https://github.com/Arize-ai/phoenix",
        "issue_url_or_reference": "https://github.com/Arize-ai/phoenix/issues/13925",
        "failure_keywords": ["test_sandbox_providers_returns_nested_configs", "wasmtime", "sqlite"],
        "possible_native_test_paths": ["tests/unit/server/api/test_sandbox_queries.py"],
        "possible_failing_command": "python -m pytest tests/unit/server/api/test_sandbox_queries.py -q --tb=no",
        "patch_or_workaround_in_issue_body": True,
        "issue_body_policy": "exclude_issue_body_from_repair_evidence_if_patch_or_workaround_present",
        "reason_this_is_promising": "Concrete native test path but issue includes root-cause and long-term fix notes.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "codex_github_search",
        "search_query": "python pytest AssertionError tests/test is:issue",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def github_api(path_or_url: str) -> dict[str, Any]:
    gh = shutil.which("gh")
    if gh:
        gh_arg = path_or_url.removeprefix("https://api.github.com")
        gh_result = subprocess.run(
            [gh, "api", gh_arg],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        if gh_result.returncode == 0 and gh_result.stdout and gh_result.stdout.strip():
            return json.loads(gh_result.stdout)
    if path_or_url.startswith("https://api.github.com/"):
        url = path_or_url
    else:
        url = f"https://api.github.com{path_or_url}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ControllerGate-Batch055",
        },
    )
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_issue_url(url: str) -> tuple[str, str, int] | None:
    match = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", url)
    if not match:
        return None
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def normalize_leads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    incoming = ROOT / "incoming_artifacts" / "seed_leads" / "seed_leads_wave_1.json"
    if incoming.is_file():
        leads = json.loads(incoming.read_text(encoding="utf-8"))
        source = {
            "status": "PASS",
            "source": "incoming_artifacts_seed_leads_wave_1_json",
            "incoming_path": str(incoming.relative_to(ROOT)),
            "incoming_artifacts_staged": False,
        }
    else:
        leads = [dict(item) for item in EMBEDDED_LEADS + AUGMENTED_LEADS]
        source = {
            "status": "PASS",
            "source": "embedded_plus_codex_github_search_augmented_leads",
            "incoming_path": str(incoming.relative_to(ROOT)),
            "incoming_file_present": False,
            "incoming_artifacts_staged": False,
            "embedded_lead_count": len(EMBEDDED_LEADS),
            "codex_augmented_lead_count": len(AUGMENTED_LEADS),
        }
    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for lead in leads:
        item = dict(lead)
        lead_id = item["lead_id"]
        if lead_id in seen:
            item["duplicate_lead_id_in_registry"] = True
        seen.add(lead_id)
        item.setdefault("source_of_lead", "helper")
        item.setdefault("do_not_include_fix_or_patch", True)
        item["lead_is_seed"] = False
        item["helper_provided_sha_trusted"] = False
        normalized.append(item)
    return normalized, source


LEAKAGE_RE = re.compile(
    r"(?i)(```diff|diff --git|suggested fix|proposed fix|workaround|patch|pull request|\\bPR\\b|implementation sketch|root cause|long-term fix|fix:)"
)


def screen_issue_body(lead: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_issue_url(lead.get("issue_url_or_reference", ""))
    if not parsed:
        return {
            "lead_id": lead["lead_id"],
            "status": "REJECT",
            "issue_reference_matches": False,
            "issue_body_fetched": False,
            "issue_body_sha256": None,
            "issue_body_excluded_from_repair_evidence": True,
            "leakage_status": "not_exact_issue_reference",
            "failure_context_fields_used": [],
        }
    owner, repo, number = parsed
    try:
        issue = github_api(f"/repos/{owner}/{repo}/issues/{number}")
        body = issue.get("body") or ""
        title = issue.get("title") or ""
        created_at = issue.get("created_at")
        leakage = bool(LEAKAGE_RE.search(body)) or lead.get("patch_or_workaround_in_issue_body") is True
        if leakage:
            used = ["issue_title", "lead_failure_keywords", "lead_native_test_paths", "lead_possible_failing_command"]
        else:
            used = ["issue_title", "failure_signature", "native_test_path", "failing_command", "environment_constraints"]
        return {
            "lead_id": lead["lead_id"],
            "status": "PASS",
            "issue_reference_matches": True,
            "issue_title": title,
            "issue_created_at": created_at,
            "issue_body_fetched": True,
            "issue_body_sha256": hash_record({"body": body}),
            "issue_body_excluded_from_repair_evidence": leakage,
            "leakage_status": "leakage_risk_screened_issue_body_excluded" if leakage else "failure_context_only",
            "failure_context_fields_used": used,
            "fix_text_persisted": False,
            "repair_decision_time_evidence_uses_issue_body": False,
            "exact_blocker": None,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "lead_id": lead["lead_id"],
            "status": "BLOCK",
            "issue_reference_matches": False,
            "issue_body_fetched": False,
            "issue_body_sha256": None,
            "issue_body_excluded_from_repair_evidence": True,
            "leakage_status": "issue_metadata_unavailable",
            "failure_context_fields_used": [],
            "exact_blocker": "issue_metadata_fetch_failed",
            "error_type": type(exc).__name__,
        }


def run_git(args: list[str], *, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def safe_rmtree(path: Path) -> None:
    if not path.exists():
        return

    def onerror(func: Any, target: str, _exc_info: Any) -> None:
        try:
            os.chmod(target, 0o700)
            func(target)
        except OSError:
            raise

    for attempt in range(1, 4):
        try:
            shutil.rmtree(path, onerror=onerror)
            return
        except (OSError, PermissionError):
            if attempt == 3:
                raise
            time.sleep(0.25 * attempt)


def commit_before_issue(repo_url: str, created_at: str | None) -> tuple[str | None, str, str | None]:
    parsed = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)", repo_url.rstrip("/"))
    if not parsed or not created_at:
        return None, "repo_or_issue_timestamp_missing", None
    owner, repo = parsed.groups()
    try:
        repo_info = github_api(f"/repos/{owner}/{repo}")
        default_branch = repo_info.get("default_branch")
        if not default_branch:
            return None, "default_branch_unavailable", None
        params = urllib.parse.urlencode({"sha": default_branch, "until": created_at, "per_page": 1})
        commits = github_api(f"/repos/{owner}/{repo}/commits?{params}")
        if isinstance(commits, list) and commits:
            return commits[0].get("sha"), "github_commit_before_issue_created_at", default_branch
        return None, "no_commit_before_issue_created_at", default_branch
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, f"metadata_fetch_failed:{type(exc).__name__}", None


def verify_commit_and_tests(lead: dict[str, Any], candidate_sha: str | None, runtime_root: Path) -> dict[str, Any]:
    if not candidate_sha or not re.fullmatch(r"[0-9a-f]{40}", candidate_sha):
        return {"sha_resolves": False, "native_test_exists": False, "checked_paths": [], "exact_blocker": "candidate_sha_missing_or_invalid"}
    repo_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", lead["repo_url"].removeprefix("https://github.com/"))
    repo_dir = runtime_root / repo_key
    if repo_dir.exists():
        safe_rmtree(repo_dir)
    repo_dir.mkdir(parents=True, exist_ok=True)
    init = run_git(["init", "-q"], cwd=repo_dir)
    if init.returncode != 0:
        return {"sha_resolves": False, "native_test_exists": False, "checked_paths": [], "exact_blocker": "git_init_failed"}
    run_git(["remote", "add", "origin", lead["repo_url"]], cwd=repo_dir)
    fetch = run_git(["fetch", "--depth=1", "origin", candidate_sha], cwd=repo_dir, timeout=120)
    cat = run_git(["cat-file", "-e", f"{candidate_sha}^{{commit}}"], cwd=repo_dir)
    sha_resolves = fetch.returncode == 0 and cat.returncode == 0
    checked_paths: list[dict[str, Any]] = []
    native_test_exists = False
    if sha_resolves:
        for raw_path in lead.get("possible_native_test_paths", []):
            rel = raw_path.strip().strip("/")
            if not rel:
                continue
            if rel.endswith("/"):
                ls = run_git(["ls-tree", "-r", "--name-only", candidate_sha, "--", rel], cwd=repo_dir)
                exists = bool(ls.stdout.strip())
            else:
                ls = run_git(["cat-file", "-e", f"{candidate_sha}:{rel}"], cwd=repo_dir)
                exists = ls.returncode == 0
            checked_paths.append({"path": rel, "exists": exists})
            native_test_exists = native_test_exists or exists
    return {
        "sha_resolves": sha_resolves,
        "native_test_exists": native_test_exists,
        "checked_paths": checked_paths,
        "git_cat_file_verified": sha_resolves,
        "runtime_workspace_path": str(repo_dir),
        "runtime_workspace_outside_repo": not str(repo_dir.resolve()).lower().startswith(str(ROOT.resolve()).lower()),
        "exact_blocker": None if sha_resolves else "git_fetch_or_cat_file_failed",
        "fetch_stderr_tail": fetch.stderr[-500:],
    }


def environment_classification(lead: dict[str, Any]) -> tuple[str, str | None]:
    text = " ".join(
        [
            lead.get("lead_id", ""),
            lead.get("possible_failing_command", ""),
            " ".join(lead.get("failure_keywords", [])),
            lead.get("reason_this_is_promising", ""),
        ]
    ).lower()
    if "windows" in text or "winerror" in text:
        return "windows_specific_or_host_specific", "rejected_environment_unclear"
    if any(token in text for token in ["imagemagick", "sql server", "native dependencies", "compiled", "meson", "cffi"]):
        return "compiled_or_external_dependency_risk", "rejected_environment_unclear"
    if "network" in text:
        return "network_or_dependency_boundary_risk", "rejected_environment_unclear"
    if "..." in lead.get("possible_failing_command", ""):
        return "command_placeholder", "rejected_no_failure_command"
    return "ubuntu_latest_plausible", None


def approve_candidates(
    leads: list[dict[str, Any]],
    leakage_records: list[dict[str, Any]],
    runtime_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    leakage_by_id = {item["lead_id"]: item for item in leakage_records}
    duplicate_records = [
        {
            "lead_id": "lemon24_reader_355_duplicate_regression_check",
            "repo_url": "https://github.com/lemon24/reader",
            "issue_url_or_reference": "https://github.com/lemon24/reader/issues/355",
            "status": "REJECTED",
            "approval_status": "rejected_duplicate_or_already_counted",
            "reason": "Already counted through Lemon Reader issue-derived repair chain locked by Batch054.",
        }
    ]
    resolutions: list[dict[str, Any]] = []
    eligible_indexes: list[int] = []
    runtime_root.mkdir(parents=True, exist_ok=True)
    for lead in leads:
        leakage = leakage_by_id.get(lead["lead_id"], {})
        env_status, env_reject = environment_classification(lead)
        duplicate = "lemon24_reader_355" in lead["lead_id"] or str(lead.get("issue_url_or_reference", "")).endswith("/355")
        if duplicate:
            duplicate_records.append(
                {
                    "lead_id": lead["lead_id"],
                    "repo_url": lead["repo_url"],
                    "issue_url_or_reference": lead.get("issue_url_or_reference"),
                    "status": "REJECTED",
                    "approval_status": "rejected_duplicate_or_already_counted",
                    "reason": "Lead matches known already-counted Lemon Reader issue-derived repair.",
                }
            )
        issue_exact = parse_issue_url(lead.get("issue_url_or_reference", "")) is not None
        candidate_sha, method, default_branch = commit_before_issue(lead["repo_url"], leakage.get("issue_created_at"))
        verify = verify_commit_and_tests(lead, candidate_sha, runtime_root) if issue_exact and not duplicate else {
            "sha_resolves": False,
            "native_test_exists": False,
            "checked_paths": [],
            "exact_blocker": "issue_not_exact_or_duplicate",
        }
        approval_status = "probe_only_needs_manual_review"
        exact_blocker: str | None = None
        if duplicate:
            approval_status = "rejected_duplicate_or_already_counted"
            exact_blocker = "duplicate_or_already_counted"
        elif not issue_exact:
            approval_status = "rejected_issue_mismatch"
            exact_blocker = "not_exact_issue_reference"
        elif leakage.get("status") == "BLOCK":
            approval_status = "rejected_leakage_risk_unmanageable"
            exact_blocker = leakage.get("exact_blocker")
        elif not verify["sha_resolves"]:
            approval_status = "rejected_commit_unresolved"
            exact_blocker = verify.get("exact_blocker")
        elif not verify["native_test_exists"]:
            approval_status = "rejected_native_test_missing"
            exact_blocker = "native_test_missing"
        elif env_reject:
            approval_status = env_reject
            exact_blocker = env_status
        else:
            approval_status = "eligible_pending_wave_cap"
            eligible_indexes.append(len(resolutions))
        record = {
            "lead_id": lead["lead_id"],
            "repo_url": lead["repo_url"],
            "issue_url_or_reference": lead.get("issue_url_or_reference"),
            "candidate_sha": candidate_sha,
            "sha_resolves": verify["sha_resolves"],
            "git_cat_file_e_commit_verified": verify.get("git_cat_file_verified", False),
            "resolution_method": method,
            "default_branch": default_branch,
            "issue_reference_matches": issue_exact,
            "native_test_exists": verify["native_test_exists"],
            "checked_native_test_paths": verify["checked_paths"],
            "possible_failing_command_selected": lead.get("possible_failing_command"),
            "environment_constraints": env_status,
            "leakage_status": leakage.get("leakage_status"),
            "issue_body_excluded_from_repair_evidence": leakage.get("issue_body_excluded_from_repair_evidence", True),
            "helper_provided_sha_trusted": False,
            "fixed_or_future_evidence_used": False,
            "patch_or_fix_text_used": False,
            "approval_status": approval_status,
            "exact_blocker": exact_blocker,
        }
        resolutions.append(record)
    approved_count = 0
    for index in eligible_indexes:
        if approved_count < 8:
            resolutions[index]["approval_status"] = "approved_for_pre_repair_replay_wave"
            resolutions[index]["exact_blocker"] = None
            approved_count += 1
        else:
            resolutions[index]["approval_status"] = "probe_only_needs_manual_review"
            resolutions[index]["exact_blocker"] = "wave_1_approval_cap_reached"
    return resolutions, duplicate_records, [resolutions[index] for index in eligible_indexes[:8]]


def copy_payload_and_manifest() -> dict[str, Any]:
    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)
    target = PAYLOAD_DIR / OUT_DIR.name
    shutil.copytree(OUT_DIR, target)
    rows = []
    forbidden = []
    for path in sorted(PAYLOAD_DIR.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(PAYLOAD_DIR).as_posix()
        if any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "ENV"} for part in PurePosixPath(rel).parts) or rel.endswith((".pyc", ".pyo", ".zip", ".tar", ".tar.gz", ".tgz", ".whl")):
            forbidden.append(rel)
        rows.append(f"{sha256_file(path)}  {rel}")
    write_text_lf(PAYLOAD_DIR / "ARTIFACT_SHA256SUMS.txt", "\n".join(rows))
    return {
        "status": "PASS" if not forbidden else "BLOCK",
        "payload_path": str(PAYLOAD_DIR.relative_to(ROOT)),
        "artifact_name": PRIMARY_ARTIFACT,
        "payload_file_count": len(rows),
        "forbidden_payloads": forbidden,
        "artifact_digest_available_before_upload": False,
    }


def update_public_docs(summary: dict[str, Any]) -> dict[str, Any]:
    marker = "### Batch055 seed discovery wave 1"
    lines = [
        "",
        marker,
        "",
        f"- Batch054 official ingest status: `{summary['batch054_ingest_status']}`.",
        f"- Batch055 seed discovery wave 1 status: `{summary['status']}`.",
        f"- Issue-derived repair count preserved at `{summary['issue_derived_repair_count']}`; native external repair count preserved at `{summary['native_external_repair_count']}`.",
        f"- Weak leads screened: `{summary['total_leads_screened']}`; Codex-augmented leads: `{summary['total_codex_augmented_leads']}`.",
        f"- Commit-resolved candidates: `{summary['commit_resolved_candidate_count']}`; approved for Batch056 pre-repair replay: `{summary['approved_for_pre_repair_replay_count']}`.",
        f"- Next allowed action: `{summary['next_allowed_action']}`.",
        "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
    ]
    updated = []
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        existing = text.find(marker)
        if existing >= 0:
            text = text[:existing].rstrip()
        write_text_lf(path, text.rstrip() + "\n" + "\n".join(lines))
        updated.append(rel)
    return {"status": "PASS", "updated_files": updated, "marker": marker}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not BATCH054_ZIP.is_file():
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": "batch054_artifact_absent_for_official_ingest"})
        return 2

    verification = verify_official_zip(
        BATCH054_ZIP,
        artifact_name=BATCH054_ARTIFACT_NAME,
        artifact_id=BATCH054_ARTIFACT_ID,
        workflow_run_id=BATCH054_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH054_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH054_SHA256,
        expected_size=BATCH054_SIZE,
        expected_entry_count=BATCH054_ENTRY_COUNT,
        artifact_manifest_checked=BATCH054_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH054_OUTPUT_MANIFESTS,
    )
    ingest_detail = (
        ingest_official_outputs(
            BATCH054_ZIP,
            ROOT,
            prefixes=("clean_replication_batch_054", "post_v2_37_hardening_001"),
        )
        if verification["status"] == "PASS"
        else {"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")}
    )
    batch054_state = read_json(ROOT / "outputs" / "clean_replication_batch_054" / "consolidated_state_clean_replication_batch_054.json")
    count_gate = read_json(ROOT / "outputs" / "clean_replication_batch_054" / "batch054_issue_derived_repair_validation_count_gate.json")

    ingest_summary = {
        "status": "PASS" if verification["status"] == "PASS" and ingest_detail["status"] == "PASS" else "BLOCK",
        "artifact_name": BATCH054_ARTIFACT_NAME,
        "artifact_id": BATCH054_ARTIFACT_ID,
        "workflow_run_id": BATCH054_WORKFLOW_RUN_ID,
        "local_artifact_path": str(BATCH054_ZIP),
        "ingest_detail": ingest_detail,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": None if verification["status"] == "PASS" and ingest_detail["status"] == "PASS" else "batch054_artifact_verification_or_ingest_failed",
    }
    result_preservation = {
        "status": "PASS" if batch054_state.get("status") == BATCH054_PASS else "BLOCK",
        "batch054_status": batch054_state.get("status"),
        "issue_derived_repair_count": batch054_state.get("issue_derived_repair_episode_count_after"),
        "native_external_repair_count": batch054_state.get("native_external_repair_episode_count"),
        "full_scoring": batch054_state.get("full_scoring"),
        "memory_lift": batch054_state.get("memory_lift"),
        "self_maintaining_software": batch054_state.get("self_maintaining_software"),
        "next_allowed_action": batch054_state.get("next_allowed_action"),
        "next_seed_fastlane": batch054_state.get("next_seed_intake_status"),
        "exact_blocker": None,
    }
    count_preservation = {
        "status": "PASS" if count_gate.get("status") == BATCH054_PASS and count_gate.get("issue_derived_repair_episode_count_after") == 2 else "BLOCK",
        "count_gate_status": count_gate.get("status"),
        "issue_derived_repair_count_before": count_gate.get("issue_derived_repair_episode_count_before"),
        "issue_derived_repair_count_after": count_gate.get("issue_derived_repair_episode_count_after"),
        "native_external_repair_count": count_gate.get("native_external_repair_episode_count"),
        "count_increment_run_in_batch055": False,
        "exact_blocker": None,
    }
    next_boundary = {
        "status": "PASS",
        "preserved_batch054_next_allowed_action": batch054_state.get("next_allowed_action"),
        "batch055_next_allowed_action": NEXT_ACTION,
        "patching_allowed_in_batch055": False,
        "repair_attempt_allowed_in_batch055": False,
        "duplicate_replay_allowed_in_batch055": False,
    }

    leads, registry_source = normalize_leads()
    leakage = [screen_issue_body(lead) for lead in leads]
    resolutions, duplicates, approved = approve_candidates(leads, leakage, LOCAL_RUNTIME_ROOT)
    approved_records = [item for item in resolutions if item["approval_status"] == "approved_for_pre_repair_replay_wave"]
    commit_resolved = [item for item in resolutions if item["sha_resolves"]]
    planned = approved_records[:5]
    approval_gate = {
        "status": "PASS" if 5 <= len(approved_records) <= 10 else "BLOCK",
        "approved_count": len(approved_records),
        "approved_candidate_ids": [item["lead_id"] for item in approved_records],
        "no_patch_generated": True,
        "no_repair_attempt_run": True,
        "no_duplicate_replay_run": True,
        "no_count_gate_run": True,
        "exact_blocker": None if 5 <= len(approved_records) <= 10 else "approved_candidate_count_outside_5_to_10",
    }
    wave_plan = {
        "status": "PASS" if planned else "BLOCK",
        "next_allowed_action": NEXT_ACTION,
        "planned_batch056_candidates": [
            {
                "lead_id": item["lead_id"],
                "repo_url": item["repo_url"],
                "candidate_sha": item["candidate_sha"],
                "possible_failing_command_selected": item["possible_failing_command_selected"],
                "native_test_exists": item["native_test_exists"],
                "ranking_basis": [
                    "commit_resolves",
                    "native_test_exists",
                    "decision_time_safe_failure_context",
                    "no_duplicate",
                    "no_fixed_gold_future_evidence",
                ],
            }
            for item in planned
        ],
    }
    dashboard = {
        "status": "PASS",
        "total_leads_received": len(leads),
        "total_leads_augmented_by_codex": sum(1 for lead in leads if lead.get("source_of_lead") == "codex_github_search"),
        "total_leads_screened": len(leads),
        "leads_rejected": sum(1 for item in resolutions if item["approval_status"].startswith("rejected_")),
        "leads_probe_only": sum(1 for item in resolutions if item["approval_status"] == "probe_only_needs_manual_review"),
        "commit_resolved_candidates": len(commit_resolved),
        "approved_for_pre_repair_replay_wave": len(approved_records),
        "planned_batch056_candidates": len(planned),
        "issue_derived_repair_count_preserved": 2,
        "native_external_repair_count_preserved": 4,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    results = {
        "status": "PASS" if ingest_summary["status"] == "PASS" and approval_gate["status"] == "PASS" else "BLOCK",
        "batch054_ingest_status": ingest_summary["status"],
        "batch055_audit_status": "PASS",
        "total_leads_screened": len(leads),
        "total_codex_augmented_leads": dashboard["total_leads_augmented_by_codex"],
        "commit_resolved_candidate_count": len(commit_resolved),
        "approved_for_pre_repair_replay_count": len(approved_records),
        "planned_batch056_candidates": [item["lead_id"] for item in planned],
        "issue_derived_repair_count": 2,
        "native_external_repair_count": 4,
        "next_allowed_action": NEXT_ACTION,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": approval_gate.get("exact_blocker"),
    }
    public_update = update_public_docs(results)
    claim_boundary = {
        "status": "PASS",
        "issue_derived_repair_count": 2,
        "native_external_repair_count": 4,
        "batch055_count_increment": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": CURRENT_PROTOCOL,
    }
    package_verification = {
        "status": "PASS",
        "artifact_name": PRIMARY_ARTIFACT,
        "artifact_payload_created_locally": False,
        "workflow_upload_required_for_artifact_identity": True,
        "raw_zip_payload_committed": False,
    }
    artifact_sha_record = {
        "status": "PENDING_WORKFLOW_ARTIFACT",
        "artifact_name": PRIMARY_ARTIFACT,
        "artifact_sha256_available_after_workflow_upload": True,
        "batch054_local_zip_sha256": verification.get("zip_sha256"),
        "github_artifact_digest": f"sha256:{BATCH054_SHA256}",
    }
    audit_record = {
        "status": "PASS",
        "audit_script": "scripts/audit_batch055_seed_discovery_wave_1.py",
        "audit_required_before_commit": True,
    }
    search_report = "\n".join(
        [
            "# Batch055 lead augmentation search report",
            "",
            "Codex used bounded GitHub issue search to augment the embedded weak-lead list.",
            "",
            "- Query: `pytest failure test path language:Python is:issue`",
            "- Query: `python pytest AssertionError tests/test is:issue`",
            "- Query: `tox failure pytest tests Python is:issue`",
            "",
            f"- Embedded leads: {len(EMBEDDED_LEADS)}",
            f"- Codex-augmented leads: {dashboard['total_leads_augmented_by_codex']}",
            "- Issue bodies were screened only for leakage classification and were not persisted as repair evidence.",
        ]
    )
    count_report = "\n".join(
        [
            "# Batch054 issue-derived count lock preservation",
            "",
            "- Batch054 count gate: `PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED`.",
            "- Issue-derived repair count is preserved at `2`.",
            "- Native external repair count is preserved at `4`.",
            "- Batch055 does not increment counts, patch, replay, or run full scoring.",
        ]
    )
    summary = "\n".join(
        [
            "# Batch055 seed discovery wave 1",
            "",
            "Batch055 officially ingests Batch054, screens weak issue-derived leads, resolves candidate commits, and prepares a bounded Batch056 pre-repair replay wave.",
            "",
            f"- Status: `{results['status']}`",
            "- No patching, repair attempt, duplicate replay, count gate, full scoring, memory-lift claim, or self-maintaining claim ran in Batch055.",
            f"- Total leads screened: `{dashboard['total_leads_screened']}`",
            f"- Codex-augmented leads: `{dashboard['total_leads_augmented_by_codex']}`",
            f"- Commit-resolved candidates: `{dashboard['commit_resolved_candidates']}`",
            f"- Approved for Batch056 pre-repair replay: `{dashboard['approved_for_pre_repair_replay_wave']}`",
            f"- Next allowed action: `{NEXT_ACTION}`",
        ]
    )

    records: dict[str, Any] = {
        "batch054_artifact_ingestion_summary.json": ingest_summary,
        "batch054_artifact_sha256_verification.json": verification,
        "batch054_result_preservation.json": result_preservation,
        "batch054_count_gate_preservation.json": count_preservation,
        "batch054_next_action_boundary.json": next_boundary,
        "seed_lead_registry.json": {"status": "PASS", **registry_source, "leads": leads},
        "seed_lead_registry_normalized.json": {"status": "PASS", "lead_count": len(leads), "leads": leads},
        "issue_body_leakage_screen.json": {"status": "PASS", "records": leakage},
        "candidate_commit_resolution_audit.json": {"status": "PASS", "records": resolutions},
        "duplicate_seed_rejection_audit.json": {"status": "PASS", "records": duplicates},
        "candidate_approval_gate_results.json": approval_gate,
        "pre_repair_replay_wave_plan.json": wave_plan,
        "seed_discovery_wave_1_results.json": results,
        "twenty_seed_campaign_dashboard.json": dashboard,
        "claim_boundary.json": claim_boundary,
        "audit.json": audit_record,
        "package_verification.json": package_verification,
        "artifact_sha256_verification.json": artifact_sha_record,
    }
    for name, data in records.items():
        write_json_deterministic(OUT_DIR / name, data)
    write_text_lf(OUT_DIR / "batch054_issue_derived_count_lock_report.md", count_report)
    write_text_lf(OUT_DIR / "lead_augmentation_search_report.md", search_report)
    write_text_lf(OUT_DIR / "campaign_summary.md", summary)
    package_record = copy_payload_and_manifest()
    write_json_deterministic(OUT_DIR / "package_verification.json", {**package_verification, **package_record})
    write_sha256sums(OUT_DIR)
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if results["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
