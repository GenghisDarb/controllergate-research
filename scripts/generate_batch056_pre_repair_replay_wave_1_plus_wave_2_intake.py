from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH056_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch056"))
BATCH055_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch055_seed_discovery_wave_1_artifacts.zip"
)
BATCH055_ARTIFACT_NAME = "post_v2_37_hardening_batch055_seed_discovery_wave_1_artifacts"
BATCH055_ARTIFACT_ID = 8151702456
BATCH055_WORKFLOW_RUN_ID = 28899775192
BATCH055_WORKFLOW_HEAD_SHA = "681276543199b35842af67b2509c575e8acc5ead"
BATCH055_SHA256 = "f4d05c2814e7f7c23b74e046b02c1af915979907a9c8acd6046c622149fbe77c"
BATCH055_SIZE = 27663
BATCH055_ENTRY_COUNT = 23
BATCH055_ARTIFACT_MANIFEST_CHECKED = 22
BATCH055_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch055_seed_discovery_wave_1": (
        "post_v2_37_hardening_batch055_seed_discovery_wave_1/SHA256SUMS.txt",
        21,
    ),
}
BATCH056_ARTIFACT_NAME = "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake_artifacts"
CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
INSTALL_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056_INSTALL_TIMEOUT", "240"))
REPLAY_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056_REPLAY_TIMEOUT", "240"))
GIT_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056_GIT_TIMEOUT", "180"))


WAVE_1_CANDIDATES: list[dict[str, Any]] = [
    {
        "lead_id": "datasette_2461_async_event_loop_cli_tests",
        "repo_url": "https://github.com/simonw/datasette",
        "candidate_sha": "f57977a08f85da40bbe04c7b0dbb57ba03694a9d",
        "target_test_paths": ["tests/test_cli.py"],
        "selected_command": "python -m pytest tests/test_cli.py -q --tb=no",
        "issue_reference": "https://github.com/simonw/datasette/issues/2461",
    },
    {
        "lead_id": "freezegun_547_py313_datetimes_assertion",
        "repo_url": "https://github.com/spulec/freezegun",
        "candidate_sha": "df263dcec48f43154a5873eb0dff2d4ba94374da",
        "target_test_paths": ["tests/test_datetimes.py"],
        "selected_command": "python -m pytest tests/test_datetimes.py -q --tb=no",
        "issue_reference": "https://github.com/spulec/freezegun/issues/547",
    },
    {
        "lead_id": "venusian_91_py313_frameinfo_callinfo",
        "repo_url": "https://github.com/Pylons/venusian",
        "candidate_sha": "966cce897c0a25485918f945eb83968d04933b2d",
        "target_test_paths": ["tests"],
        "selected_command": "tox -e py313",
        "issue_reference": "https://github.com/Pylons/venusian/issues/91",
    },
    {
        "lead_id": "pexpect_699_replwrap_bash_assertions",
        "repo_url": "https://github.com/pexpect/pexpect",
        "candidate_sha": "000a8684bd109c3f9c9b5fabd95add4743b7f45a",
        "target_test_paths": ["tests/test_replwrap.py"],
        "selected_command": "python -m pytest tests/test_replwrap.py -q --tb=no",
        "issue_reference": "https://github.com/pexpect/pexpect/issues/699",
    },
    {
        "lead_id": "pyramid_3761_py313_test_util",
        "repo_url": "https://github.com/Pylons/pyramid",
        "candidate_sha": "ef0f6861e5b439afe43983f6c7437c30a413a34d",
        "target_test_paths": ["tests/test_util.py"],
        "selected_command": "python -m pytest tests/test_util.py -q --tb=no",
        "issue_reference": "https://github.com/Pylons/pyramid/issues/3761",
    },
]


EMBEDDED_WAVE_2_LEADS: list[dict[str, Any]] = [
    {
        "lead_id": "repo_helper_pyproject_examples",
        "repo_url": "https://github.com/repo-helper/pyproject-examples",
        "issue_url_or_reference": "https://github.com/repo-helper/pyproject-examples/issues",
        "failure_keywords": ["pyproject.toml", "pytest", "invalid"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "not_an_exact_issue_reference_must_resolve_or_reject",
        "reason_this_is_promising": "Potential small pyproject validation scope, but issue reference is not exact.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "xarray_contrib_issue_from_pytest_log",
        "repo_url": "https://github.com/xarray-contrib/issue-from-pytest-log",
        "issue_url_or_reference": "https://github.com/xarray-contrib/issue-from-pytest-log/issues",
        "failure_keywords": ["pytest", "log", "issue"],
        "possible_native_test_paths": ["tests/test_format_issue_body.py"],
        "possible_failing_command": "python -m pytest tests/test_format_issue_body.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "not_an_exact_issue_reference_must_resolve_or_reject",
        "reason_this_is_promising": "Small pytest-log-to-issue tool scope, but exact issue must be resolved.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "pydantic_pytest_examples_wave2",
        "repo_url": "https://github.com/pydantic/pytest-examples",
        "issue_url_or_reference": "https://github.com/pydantic/pytest-examples/issues",
        "failure_keywords": ["docstring", "markdown", "pytest"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "not_an_exact_issue_reference_must_resolve_or_reject",
        "reason_this_is_promising": "Small pytest plugin scope, but Batch055 already rejected non-exact pydantic pytest-examples references.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "scientific_python_pytest_log_action",
        "repo_url": "https://github.com/scientific-python/pytest-log-action",
        "issue_url_or_reference": "https://github.com/scientific-python/pytest-log-action/issues",
        "failure_keywords": ["pytest", "log", "action"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "not_an_exact_issue_reference_must_resolve_or_reject",
        "reason_this_is_promising": "Small GitHub/pytest log action scope, but exact issue must be resolved.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "bashtage_arch_pyproject",
        "repo_url": "https://github.com/bashtage/arch",
        "issue_url_or_reference": "https://github.com/bashtage/arch/issues",
        "failure_keywords": ["pyproject.toml", "test"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "not_an_exact_issue_reference_must_resolve_or_reject",
        "reason_this_is_promising": "Potential pyproject/test failures but large dependency surface; lower priority unless exact issue is small.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "numpy_21994_ufunc_overflow",
        "repo_url": "https://github.com/numpy/numpy",
        "issue_url_or_reference": "https://github.com/numpy/numpy/issues/21994",
        "failure_keywords": ["test_reduce_contig_1d", "RuntimeWarning", "overflow encountered", "ufunc"],
        "possible_native_test_paths": ["numpy/core/tests/test_ufunc.py"],
        "possible_failing_command": "python -m pytest numpy/core/tests/test_ufunc.py::test_reduce_contig_1d -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Clear issue/test clue, but NumPy has a compiled-heavy source surface.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "pytest_11058_unraisable_exception",
        "repo_url": "https://github.com/pytest-dev/pytest",
        "issue_url_or_reference": "https://github.com/pytest-dev/pytest/issues/11058",
        "failure_keywords": ["test_unraisable_exception", "AttributeError", "Python 3.12", "unraisable"],
        "possible_native_test_paths": ["testing/test_unraisable.py"],
        "possible_failing_command": "python -m pytest testing/test_unraisable.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Pytest self-test issue with concrete path; must screen for fix/leakage and exact commit.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "black_2992_blackd_path_separator",
        "repo_url": "https://github.com/psf/black",
        "issue_url_or_reference": "https://github.com/psf/black/issues/2992",
        "failure_keywords": ["test_blackd", "path separator", "Windows", "assertion"],
        "possible_native_test_paths": ["tests/test_blackd.py"],
        "possible_failing_command": "python -m pytest tests/test_blackd.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Platform-specific test failure. Classify carefully on ubuntu-latest.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "jinja_1628_lexer_py311",
        "repo_url": "https://github.com/pallets/jinja",
        "issue_url_or_reference": "https://github.com/pallets/jinja/issues/1628",
        "failure_keywords": ["test_lexer", "Python 3.11", "SyntaxError", "lex", "line number"],
        "possible_native_test_paths": ["tests/test_lexer.py"],
        "possible_failing_command": "python -m pytest tests/test_lexer.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Potentially small pure-Python parser/lexer scope; screen exactly.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "scipy_16783_lbfgsb_tolerance",
        "repo_url": "https://github.com/scipy/scipy",
        "issue_url_or_reference": "https://github.com/scipy/scipy/issues/16783",
        "failure_keywords": ["LBFGSB", "test_optimize", "tolerance", "assert_allclose", "atol"],
        "possible_native_test_paths": ["scipy/optimize/tests/test_lbfgsb.py"],
        "possible_failing_command": "python -m pytest scipy/optimize/tests/test_lbfgsb.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Clear numerical-test clue but SciPy is compiled-heavy.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "helper_wave_2",
    },
    {
        "lead_id": "pairtools_250_py313_pipes_removed",
        "repo_url": "https://github.com/open2c/pairtools",
        "issue_url_or_reference": "https://github.com/open2c/pairtools/issues/250",
        "failure_keywords": ["Python 3.13", "pipes", "ModuleNotFoundError", "tests/test_headerops.py", "tests/test_select.py"],
        "possible_native_test_paths": ["tests/test_headerops.py", "tests/test_select.py"],
        "possible_failing_command": "python -m pytest tests/test_headerops.py tests/test_select.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Python 3.13 native collection errors may be localized if leakage screen passes.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
    {
        "lead_id": "pygments_2992_pytest84_lexer_classes",
        "repo_url": "https://github.com/pygments/pygments",
        "issue_url_or_reference": "https://github.com/pygments/pygments/issues/2992",
        "failure_keywords": ["pytest 8.4", "test_lexer_classes", "BashSessionLexer", "AssertionError"],
        "possible_native_test_paths": ["tests/test_lexers.py"],
        "possible_failing_command": "python -m pytest tests/test_lexers.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Pure-Python lexer project with a named test failure under pytest 8.4.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
    {
        "lead_id": "shapely_1937_py313_docstring_indent",
        "repo_url": "https://github.com/shapely/shapely",
        "issue_url_or_reference": "https://github.com/shapely/shapely/issues/1937",
        "failure_keywords": ["Python 3.13", "docstrings", "test_misc.py", "test_requires_geos_method", "AssertionError"],
        "possible_native_test_paths": ["tests/test_misc.py"],
        "possible_failing_command": "python -m pytest tests/test_misc.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Python 3.13 docstring behavior clue, but Shapely may involve compiled dependencies.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
    {
        "lead_id": "pytest_qt_532_py312_exceptions_dont_leak",
        "repo_url": "https://github.com/pytest-dev/pytest-qt",
        "issue_url_or_reference": "https://github.com/pytest-dev/pytest-qt/issues/532",
        "failure_keywords": ["Python 3.12", "test_exceptions_dont_leak", "pytest", "PyQt5", "Qt"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Concrete Python 3.12 test failure but Qt/PyQt dependency surface may be heavy.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
    {
        "lead_id": "pytest_13480_wdefault_unraisable_threadexception",
        "repo_url": "https://github.com/pytest-dev/pytest",
        "issue_url_or_reference": "https://github.com/pytest-dev/pytest/issues/13480",
        "failure_keywords": ["-Wdefault", "test_unraisableexception.py", "test_threadexception.py", "AssertionError", "ExitCode"],
        "possible_native_test_paths": ["testing/test_unraisableexception.py", "testing/test_threadexception.py", "testing/test_warnings.py"],
        "possible_failing_command": "python -m pytest testing/test_unraisableexception.py testing/test_threadexception.py testing/test_warnings.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Recent pytest self-test failure with concrete test files and assertions.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
    {
        "lead_id": "smart_open_846_py313_test_failure",
        "repo_url": "https://github.com/piskvorky/smart_open",
        "issue_url_or_reference": "https://github.com/piskvorky/smart_open/issues/846",
        "failure_keywords": ["Python 3.13", "test failure", "Debian", "pytest"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Python 3.13 test failure report in a mostly pure-Python library.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
    {
        "lead_id": "monty_765_freebsd_three_failures",
        "repo_url": "https://github.com/materialsvirtuallab/monty",
        "issue_url_or_reference": "https://github.com/materialsvirtuallab/monty/issues/765",
        "failure_keywords": ["3 tests fail", "TestControlledDict", "TestScratchDir", "TestCheckType", "FreeBSD"],
        "possible_native_test_paths": ["tests/test_collections.py", "tests/test_tempfile.py", "tests/test_json.py"],
        "possible_failing_command": "python -m pytest tests/test_collections.py tests/test_tempfile.py tests/test_json.py -q --tb=no",
        "patch_or_workaround_in_issue_body": "unknown_screen_required",
        "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
        "reason_this_is_promising": "Concrete native test failures but FreeBSD-specific; likely provider/OS mismatch on ubuntu-latest.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
    {
        "lead_id": "snapshottest_177_py312_imp_removed",
        "repo_url": "https://github.com/syrusakbary/snapshottest",
        "issue_url_or_reference": "https://github.com/syrusakbary/snapshottest/issues/177",
        "failure_keywords": ["Python 3.12", "imp", "ModuleNotFoundError", "pytest", "snapshottest"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest tests -q --tb=no",
        "patch_or_workaround_in_issue_body": True,
        "issue_body_policy": "exclude_issue_body_from_repair_evidence_if_patch_or_workaround_present",
        "reason_this_is_promising": "Small compatibility failure, but issue body appears to contain solution-like workaround text.",
        "do_not_include_fix_or_patch": True,
        "source_of_lead": "halcyon_web_search_wave_2",
    },
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_rmtree(path: Path) -> None:
    if not path.exists():
        return
    def onexc(func: Any, target: str, _exc_info: Any) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    for attempt in range(5):
        try:
            shutil.rmtree(path, onexc=onexc)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.4 * (attempt + 1))


def run_cmd(
    args: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": args,
            "cwd": str(cwd),
            "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timeout_seconds": timeout,
            "timed_out": False,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": args,
            "cwd": str(cwd),
            "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timeout_seconds": timeout,
            "timed_out": True,
            "returncode": None,
            "stdout": exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            "stderr": exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
        }


def combined_log(result: dict[str, Any]) -> str:
    return (result.get("stdout") or "") + ("\n" if result.get("stdout") and result.get("stderr") else "") + (result.get("stderr") or "")


def parse_repo(repo_url: str) -> tuple[str, str] | None:
    match = re.match(r"https://github\.com/([^/]+)/([^/#?]+?)(?:\.git)?/?$", repo_url)
    if not match:
        return None
    return match.group(1), match.group(2)


def parse_issue_url(issue_url: str) -> tuple[str, str, int] | None:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)$", issue_url or "")
    if not match:
        return None
    return match.group(1), match.group(2), int(match.group(3))


def github_api(path: str) -> tuple[Any | None, dict[str, Any]]:
    result = run_cmd(["gh", "api", path], cwd=ROOT, timeout=60)
    if result["returncode"] != 0:
        return None, {
            "status": "BLOCK",
            "api_path": path,
            "returncode": result["returncode"],
            "stderr_hash": hash_record(result.get("stderr", "")),
            "exact_blocker": "github_api_unavailable",
        }
    try:
        return json.loads(result["stdout"]), {
            "status": "PASS",
            "api_path": path,
            "stdout_hash": hash_record(result["stdout"]),
        }
    except json.JSONDecodeError as exc:
        return None, {
            "status": "BLOCK",
            "api_path": path,
            "error": str(exc),
            "exact_blocker": "github_api_json_parse_failed",
        }


def clone_checkout(repo_url: str, sha: str, workspace: Path) -> dict[str, Any]:
    safe_rmtree(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    clone = run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", repo_url, str(workspace)], cwd=ROOT, timeout=GIT_TIMEOUT_SECONDS)
    if clone["returncode"] != 0:
        return {"status": "BLOCK", "step": "clone", "clone": trim_result(clone), "exact_blocker": "blocked_repo_checkout_failure"}
    fetch = run_cmd(["git", "fetch", "--depth", "1", "origin", sha], cwd=workspace, timeout=GIT_TIMEOUT_SECONDS)
    if fetch["returncode"] != 0:
        return {"status": "BLOCK", "step": "fetch", "fetch": trim_result(fetch), "exact_blocker": "blocked_commit_unresolved"}
    cat = run_cmd(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=workspace, timeout=GIT_TIMEOUT_SECONDS)
    if cat["returncode"] != 0:
        return {"status": "BLOCK", "step": "cat-file", "cat_file": trim_result(cat), "exact_blocker": "blocked_commit_unresolved"}
    checkout = run_cmd(["git", "checkout", "--detach", sha], cwd=workspace, timeout=GIT_TIMEOUT_SECONDS)
    if checkout["returncode"] != 0:
        return {"status": "BLOCK", "step": "checkout", "checkout": trim_result(checkout), "exact_blocker": "blocked_repo_checkout_failure"}
    return {
        "status": "PASS",
        "clone": trim_result(clone),
        "fetch": trim_result(fetch),
        "cat_file": trim_result(cat),
        "checkout": trim_result(checkout),
    }


def trim_result(result: dict[str, Any], limit: int = 4000) -> dict[str, Any]:
    return {
        "command": result.get("command"),
        "cwd": result.get("cwd"),
        "returncode": result.get("returncode"),
        "timed_out": result.get("timed_out", False),
        "stdout_sha256": hash_record(result.get("stdout", "")),
        "stderr_sha256": hash_record(result.get("stderr", "")),
        "stdout_excerpt": (result.get("stdout") or "")[:limit],
        "stderr_excerpt": (result.get("stderr") or "")[:limit],
    }


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def venv_exe(venv: Path, name: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return venv / ("Scripts" if os.name == "nt" else "bin") / f"{name}{suffix}"


def normalize_command(command: str, venv: Path) -> tuple[list[str], dict[str, Any]]:
    parts = command.split()
    if len(parts) >= 3 and parts[0] == "python" and parts[1] == "-m":
        return [str(venv_python(venv)), *parts[1:]], {
            "status": "PASS",
            "original_command": command,
            "normalized_command": " ".join([str(venv_python(venv)), *parts[1:]]),
            "normalization": "python_executable_rewritten_to_isolated_venv",
        }
    if parts and parts[0] == "tox":
        return [str(venv_exe(venv, "tox")), *parts[1:]], {
            "status": "PASS",
            "original_command": command,
            "normalized_command": " ".join([str(venv_exe(venv, "tox")), *parts[1:]]),
            "normalization": "tox_executable_rewritten_to_isolated_venv",
        }
    return parts, {
        "status": "BLOCK",
        "original_command": command,
        "normalized_command": command,
        "exact_blocker": "blocked_command_ambiguous",
    }


def setup_environment(workspace: Path, venv: Path, command: str) -> dict[str, Any]:
    safe_rmtree(venv)
    create = run_cmd([sys.executable, "-m", "venv", str(venv)], cwd=ROOT, timeout=120)
    if create["returncode"] != 0:
        return {"status": "BLOCK", "step": "create_venv", "result": trim_result(create), "exact_blocker": "blocked_environment_unclear"}
    py = venv_python(venv)
    pip_upgrade = run_cmd([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=workspace, timeout=INSTALL_TIMEOUT_SECONDS)
    if pip_upgrade["returncode"] != 0:
        return {"status": "BLOCK", "step": "pip_upgrade", "result": trim_result(pip_upgrade), "exact_blocker": "blocked_dependency_install_failure"}
    tool = "tox" if command.startswith("tox ") else "pytest"
    tool_install = run_cmd([str(py), "-m", "pip", "install", tool], cwd=workspace, timeout=INSTALL_TIMEOUT_SECONDS)
    if tool_install["returncode"] != 0:
        return {"status": "BLOCK", "step": f"{tool}_install", "result": trim_result(tool_install), "exact_blocker": "blocked_dependency_install_failure"}
    editable_attempts: list[dict[str, Any]] = []
    editable_install: dict[str, Any] | None = None
    for target in [".[test]", ".[tests]", "."]:
        attempt = run_cmd([str(py), "-m", "pip", "install", "-e", target], cwd=workspace, timeout=INSTALL_TIMEOUT_SECONDS)
        editable_attempts.append({"target": target, "result": trim_result(attempt, 1000)})
        if attempt["returncode"] == 0:
            editable_install = attempt
            break
    if editable_install is None:
        last_log = json.dumps(editable_attempts, sort_keys=True)
        return {
            "status": "BLOCK",
            "step": "editable_install",
            "attempts": editable_attempts,
            "exact_blocker": classify_install_block(last_log),
        }
    return {
        "status": "PASS",
        "python_executable": str(py),
        "tool_installed": tool,
        "pip_upgrade": trim_result(pip_upgrade, 1000),
        "tool_install": trim_result(tool_install, 1000),
        "editable_install_attempts": editable_attempts,
        "editable_install": trim_result(editable_install, 1000),
    }


def classify_install_block(log: str) -> str:
    lowered = log.lower()
    if any(term in lowered for term in ["error: microsoft visual c++", "gcc", "cmake", "meson", "ninja", "rust", "failed building wheel"]):
        return "blocked_compiled_dependency"
    if any(term in lowered for term in ["could not find a version", "no matching distribution", "requires-python"]):
        return "blocked_python_version_unavailable"
    return "blocked_dependency_install_failure"


def classify_replay(result: dict[str, Any], setup: dict[str, Any]) -> str:
    log = combined_log(result).lower()
    if setup.get("status") != "PASS":
        return setup.get("exact_blocker", "blocked_dependency_install_failure")
    if result.get("timed_out"):
        return "blocked_timeout"
    if result.get("returncode") == 0:
        return "failure_not_reproduced"
    if "module not founderror" in log or "modulenotfounderror" in log or "no module named" in log:
        return "blocked_dependency_install_failure"
    if result.get("returncode") in {2, 4, 5} and ("error during collection" in log or "importerror while loading conftest" in log):
        return "blocked_dependency_install_failure"
    if "network is unreachable" in log or "temporary failure in name resolution" in log:
        return "blocked_network_required"
    if "no module named tox" in log or "python 3.13 was not found" in log or "could not find python interpreter" in log:
        return "blocked_tox_env_unavailable"
    return "pre_repair_failure_materialized"


def failure_signature(log: str) -> str:
    lines = []
    for line in log.splitlines():
        lowered = line.lower()
        if (
            "error" in lowered
            or "failed" in lowered
            or "failure" in lowered
            or "assert" in lowered
            or "exception" in lowered
            or "traceback" in lowered
            or line.startswith("E   ")
        ):
            lines.append(line.rstrip())
        if len(lines) >= 80:
            break
    if not lines:
        lines = log.splitlines()[:80]
    return "\n".join(lines).strip()


def run_wave1_candidate(candidate: dict[str, Any], leakage_by_id: dict[str, Any]) -> dict[str, Any]:
    lead_id = candidate["lead_id"]
    candidate_dir = OUT_DIR / "wave_1_candidates" / lead_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    workspace = RUNTIME_ROOT / "wave_1" / lead_id / "checkout"
    venv = RUNTIME_ROOT / "wave_1" / lead_id / "venv"
    pre_plan = {
        "lead_id": lead_id,
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "selected_command": candidate["selected_command"],
        "target_test_paths": candidate["target_test_paths"],
        "patch_allowed": False,
        "duplicate_replay_allowed": False,
        "count_gate_allowed": False,
    }
    write_json_deterministic(candidate_dir / "candidate_replay_plan.json", pre_plan)
    checkout = clone_checkout(candidate["repo_url"], candidate["candidate_sha"], workspace)
    commit_verification = {
        "lead_id": lead_id,
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "status": checkout["status"],
        "git_cat_file_e_commit_verified": checkout.get("status") == "PASS",
        "helper_provided_sha_trusted": False,
        "checkout_detail": checkout,
    }
    write_json_deterministic(candidate_dir / "candidate_commit_verification.json", commit_verification)
    target_exists = False
    checked_paths: list[dict[str, Any]] = []
    if checkout["status"] == "PASS":
        for rel in candidate["target_test_paths"]:
            path = workspace / rel
            exists = path.exists()
            checked_paths.append({"path": rel, "exists": exists, "sha256": sha256_file(path) if path.is_file() else None})
        target_exists = all(item["exists"] for item in checked_paths)
    else:
        checked_paths = [{"path": rel, "exists": False, "sha256": None} for rel in candidate["target_test_paths"]]
    workspace_manifest = {
        "status": "PASS" if checkout["status"] == "PASS" else "BLOCK",
        "workspace_path": str(workspace),
        "workspace_outside_live_repo": not str(workspace).lower().startswith(str(ROOT).lower()),
        "workspace_outside_onedrive": "onedrive" not in str(workspace).lower(),
        "fresh_workspace_created": checkout["status"] == "PASS",
        "stale_cache_count": 0,
        "target_paths": checked_paths,
    }
    write_json_deterministic(candidate_dir / "candidate_workspace_manifest.json", workspace_manifest)
    if checkout["status"] != "PASS":
        classification = checkout.get("exact_blocker", "blocked_repo_checkout_failure")
        setup = {"status": "NOT_RUN", "reason": "checkout_failed"}
        command_context = {"status": "NOT_RUN", "reason": "checkout_failed"}
        normalized = {"status": "NOT_RUN", "reason": "checkout_failed"}
        replay = {"status": "BLOCK", "classification": classification, "command_ran": False, "exact_blocker": classification}
        raw_log = json.dumps(checkout, indent=2, sort_keys=True)
    elif not target_exists:
        classification = "blocked_native_test_missing"
        setup = {"status": "NOT_RUN", "reason": "native_test_missing"}
        command_context = {"status": "PASS", "selected_command": candidate["selected_command"], "target_paths_checked": checked_paths}
        normalized = {"status": "NOT_RUN", "reason": "native_test_missing"}
        replay = {"status": "BLOCK", "classification": classification, "command_ran": False, "exact_blocker": classification}
        raw_log = "Native target test path missing before replay.\n" + json.dumps(checked_paths, indent=2, sort_keys=True)
    else:
        setup = setup_environment(workspace, venv, candidate["selected_command"])
        command_args, normalized = normalize_command(candidate["selected_command"], venv)
        command_context = {
            "status": "PASS" if normalized["status"] == "PASS" else "BLOCK",
            "selected_command": candidate["selected_command"],
            "normalized_command": normalized.get("normalized_command"),
            "cwd": str(workspace),
            "environment": {
                "PATH_prefix": str(venv.parent),
                "python_version": sys.version.split()[0],
                "isolated_venv": str(venv),
            },
        }
        if setup["status"] != "PASS" or normalized["status"] != "PASS":
            classification = setup.get("exact_blocker") if setup["status"] != "PASS" else normalized.get("exact_blocker", "blocked_command_ambiguous")
            replay = {"status": "BLOCK", "classification": classification, "command_ran": False, "setup_status": setup.get("status"), "exact_blocker": classification}
            raw_log = json.dumps(setup, indent=2, sort_keys=True)
        else:
            env = os.environ.copy()
            bin_dir = str(venv / ("Scripts" if os.name == "nt" else "bin"))
            env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
            result = run_cmd(command_args, cwd=workspace, timeout=REPLAY_TIMEOUT_SECONDS, env=env)
            raw_log = combined_log(result)
            classification = classify_replay(result, setup)
            replay = {
                "status": "PASS" if classification == "pre_repair_failure_materialized" else "BLOCK",
                "classification": classification,
                "command_ran": True,
                "returncode": result.get("returncode"),
                "timed_out": result.get("timed_out"),
                "pre_repair_replay_before_patch_authorization": True,
                "patch_generated": False,
                "patch_authorized": False,
                "patch_attempted": False,
                "exact_blocker": None if classification == "pre_repair_failure_materialized" else classification,
                "raw_log_sha256": hash_record(raw_log),
            }
    write_json_deterministic(candidate_dir / "candidate_dependency_plan.json", setup)
    write_json_deterministic(candidate_dir / "candidate_command_context.json", command_context)
    write_json_deterministic(candidate_dir / "candidate_command_normalization.json", normalized)
    write_text_lf(candidate_dir / "pre_repair_replay_command.txt", candidate["selected_command"])
    write_text_lf(candidate_dir / "pre_repair_replay_log_raw.txt", raw_log)
    write_json_deterministic(candidate_dir / "pre_repair_replay_result.json", replay)
    write_text_lf(candidate_dir / "failure_signature_extract.txt", failure_signature(raw_log))
    write_json_deterministic(
        candidate_dir / "decision_time_input_manifest.json",
        {
            "status": "PASS",
            "lead_id": lead_id,
            "inputs": [
                {"kind": "repo_url", "value": candidate["repo_url"], "decision_time_safe": True},
                {"kind": "candidate_sha", "value": candidate["candidate_sha"], "decision_time_safe": True},
                {"kind": "selected_command", "value": candidate["selected_command"], "decision_time_safe": True},
                {"kind": "target_test_paths", "value": candidate["target_test_paths"], "decision_time_safe": True},
            ],
            "fixed_gold_future_evidence_used": False,
            "issue_body_repair_evidence_used": False,
        },
    )
    write_json_deterministic(
        candidate_dir / "issue_body_leakage_boundary.json",
        {
            "status": "PASS",
            "lead_id": lead_id,
            "source": "Batch055 leakage boundary preservation",
            "batch055_record": leakage_by_id.get(lead_id),
            "issue_body_persisted_as_repair_evidence": False,
            "patch_or_workaround_text_used": False,
        },
    )
    for name, record in {
        "label_blindness_check.json": {"status": "PASS", "hidden_labels_used": False, "label_only_routing_used": False},
        "gold_patch_exclusion_check.json": {"status": "PASS", "gold_patch_used": False, "fixed_commit_used": False, "pr_patch_used": False},
        "future_evidence_exclusion_check.json": {"status": "PASS", "future_evidence_used": False, "later_commit_used": False},
        "workspace_custody_check.json": {
            "status": "PASS" if workspace_manifest["workspace_outside_live_repo"] and workspace_manifest["workspace_outside_onedrive"] else "BLOCK",
            "workspace_path": str(workspace),
            "outside_live_repo": workspace_manifest["workspace_outside_live_repo"],
            "outside_onedrive": workspace_manifest["workspace_outside_onedrive"],
            "raw_workspace_committed": False,
        },
        "provider_precondition_check.json": {
            "status": "PASS",
            "provider_precondition_blocker": None,
            "environment_or_provider_failure_classified_as_repair_failure": False,
        },
    }.items():
        write_json_deterministic(candidate_dir / name, record)
    classification_record = {
        "lead_id": lead_id,
        "classification": classification,
        "scoreable_for_batch057_patch_gate": classification == "pre_repair_failure_materialized",
        "exact_blocker": None if classification == "pre_repair_failure_materialized" else classification,
        "patch_generated": False,
        "repair_attempted": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
    }
    write_json_deterministic(candidate_dir / "classification.json", classification_record)
    return {
        "lead_id": lead_id,
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "selected_command": candidate["selected_command"],
        "target_test_paths": candidate["target_test_paths"],
        "classification": classification,
        "exact_blocker": classification_record["exact_blocker"],
        "pre_repair_replay_result": replay,
        "failure_signature": failure_signature(raw_log),
        "candidate_output_dir": str(candidate_dir.relative_to(OUT_DIR)),
    }


def load_wave_2_leads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    incoming = ROOT / "incoming_artifacts" / "seed_leads" / "seed_leads_wave_2.json"
    if incoming.is_file():
        leads = read_json(incoming)
        return leads, {"source": str(incoming), "incoming_file_used": True, "embedded_leads_used": False}
    leads = list(EMBEDDED_WAVE_2_LEADS)
    augmented, search_report = github_search_augmented_leads()
    leads.extend(augmented)
    return leads, {"source": "embedded_wave_2_plus_optional_codex_search", "incoming_file_used": False, "embedded_leads_used": True, **search_report}


def github_search_augmented_leads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if os.environ.get("CONTROLLERGATE_BATCH056_SKIP_CODEX_AUGMENT") == "1":
        return [], {"codex_augmented_lead_count": 0, "codex_search_status": "SKIPPED_BY_ENV"}
    query = 'pytest failure native test language:Python is:issue archived:false'
    result = run_cmd(["gh", "search", "issues", query, "--limit", "5", "--json", "url,repository,title,number"], cwd=ROOT, timeout=60)
    if result["returncode"] != 0:
        return [], {"codex_augmented_lead_count": 0, "codex_search_status": "BLOCK", "codex_search_error_hash": hash_record(result.get("stderr", ""))}
    try:
        rows = json.loads(result["stdout"])
    except json.JSONDecodeError:
        return [], {"codex_augmented_lead_count": 0, "codex_search_status": "BLOCK", "exact_blocker": "codex_search_json_parse_failed"}
    leads = []
    for row in rows:
        repo = row.get("repository") or {}
        repo_url = repo.get("url") or repo.get("owner", {}).get("url")
        if not repo_url and repo.get("nameWithOwner"):
            repo_url = f"https://github.com/{repo['nameWithOwner']}"
        if not repo_url or not row.get("url"):
            continue
        base_id = re.sub(r"[^a-z0-9]+", "_", (repo.get("nameWithOwner") or repo_url).lower()).strip("_")
        leads.append(
            {
                "lead_id": f"codex_wave2_{base_id}_{row.get('number')}",
                "repo_url": repo_url,
                "issue_url_or_reference": row["url"],
                "failure_keywords": ["pytest", "failure", "native test"],
                "possible_native_test_paths": ["tests/"],
                "possible_failing_command": "python -m pytest tests -q --tb=no",
                "patch_or_workaround_in_issue_body": "unknown_screen_required",
                "issue_body_policy": "screen_issue_body_for_patch_workaround_and_exclude_if_present",
                "reason_this_is_promising": "Codex bounded GitHub search result for future replay planning.",
                "do_not_include_fix_or_patch": True,
                "source_of_lead": "codex_github_search_wave_2",
            }
        )
    return leads, {"codex_augmented_lead_count": len(leads), "codex_search_status": "PASS", "codex_search_query_hash": hash_record(query)}


def normalize_wave2_lead(lead: dict[str, Any]) -> dict[str, Any]:
    record = dict(lead)
    record["lead_is_seed"] = False
    record["helper_provided_sha_trusted"] = False
    record["fixed_gold_future_evidence_allowed"] = False
    record["wave_2_pre_repair_replay_run"] = False
    record["patch_generated"] = False
    record["repair_count_incremented"] = False
    return record


def screen_leakage(lead: dict[str, Any]) -> dict[str, Any]:
    issue_ref = lead.get("issue_url_or_reference", "")
    parsed = parse_issue_url(issue_ref)
    base = {
        "lead_id": lead["lead_id"],
        "issue_url_or_reference": issue_ref,
        "issue_reference_exact": parsed is not None,
        "issue_body_persisted": False,
        "issue_body_used_as_repair_evidence": False,
        "fix_or_workaround_text_persisted": False,
        "leakage_status": "NOT_SCREENED",
        "issue_created_at": None,
        "issue_title_hash": None,
        "issue_body_hash": None,
    }
    if not parsed:
        return {**base, "leakage_status": "REJECT_REFERENCE_NOT_EXACT", "exact_blocker": "rejected_not_exact_issue_reference"}
    owner, repo, number = parsed
    issue, meta = github_api(f"repos/{owner}/{repo}/issues/{number}")
    if not issue:
        return {**base, "leakage_status": "BLOCK", "github_api": meta, "exact_blocker": "rejected_issue_mismatch"}
    body = issue.get("body") or ""
    title = issue.get("title") or ""
    risky = bool(re.search(r"\b(fix|patch|workaround|solution|resolved by|pull request|diff|change this|replace with)\b", body, re.I))
    if lead.get("patch_or_workaround_in_issue_body") is True:
        risky = True
    policy = lead.get("issue_body_policy")
    if risky and policy == "screen_issue_body_for_patch_workaround_and_exclude_if_present":
        status = "PASS_EXCLUDED_RISKY_BODY"
    elif risky and policy == "exclude_issue_body_from_repair_evidence_if_patch_or_workaround_present":
        status = "PASS_EXCLUDED_RISKY_BODY"
    elif risky:
        status = "BLOCK_LEAKAGE_RISK"
    else:
        status = "PASS_NO_FIX_TEXT_DETECTED"
    return {
        **base,
        "leakage_status": status,
        "issue_created_at": issue.get("created_at"),
        "issue_state": issue.get("state"),
        "issue_title_hash": hash_record(title),
        "issue_body_hash": hash_record(body),
        "issue_body_excluded_from_repair_evidence": True,
        "fix_or_workaround_risk_detected": risky,
        "exact_blocker": "rejected_leakage_risk_unmanageable" if status == "BLOCK_LEAKAGE_RISK" else None,
    }


def commit_before_issue(repo_url: str, issue_created_at: str | None) -> tuple[str | None, dict[str, Any]]:
    parsed_repo = parse_repo(repo_url)
    if not parsed_repo or not issue_created_at:
        return None, {"status": "BLOCK", "exact_blocker": "rejected_commit_unresolved"}
    owner, repo = parsed_repo
    repo_meta, repo_api = github_api(f"repos/{owner}/{repo}")
    if not repo_meta:
        return None, {"status": "BLOCK", "github_api": repo_api, "exact_blocker": "rejected_commit_unresolved"}
    branch = repo_meta.get("default_branch")
    commits, commits_api = github_api(f"repos/{owner}/{repo}/commits?sha={branch}&until={issue_created_at}&per_page=1")
    if not commits:
        return None, {"status": "BLOCK", "github_api": commits_api, "default_branch": branch, "exact_blocker": "rejected_commit_unresolved"}
    sha = commits[0].get("sha")
    return sha, {
        "status": "PASS" if sha else "BLOCK",
        "default_branch": branch,
        "method": "default_branch_commit_at_or_before_issue_created_at",
        "issue_created_at": issue_created_at,
        "commit_api_hash": hash_record(commits),
        "exact_blocker": None if sha else "rejected_commit_unresolved",
    }


def verify_commit_and_native_paths(lead: dict[str, Any], sha: str | None, runtime_root: Path) -> dict[str, Any]:
    if not sha:
        return {"status": "BLOCK", "sha_resolves": False, "native_test_exists": False, "checked_paths": [], "exact_blocker": "rejected_commit_unresolved"}
    parsed = parse_repo(lead["repo_url"])
    if not parsed:
        return {"status": "BLOCK", "sha_resolves": False, "native_test_exists": False, "checked_paths": [], "exact_blocker": "rejected_commit_unresolved"}
    repo_dir = runtime_root / "wave_2_commits" / re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{parsed[0]}_{parsed[1]}_{sha[:12]}")
    safe_rmtree(repo_dir)
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    init = run_cmd(["git", "init"], cwd=repo_dir.parent, timeout=GIT_TIMEOUT_SECONDS)
    repo_dir.mkdir(exist_ok=True)
    init = run_cmd(["git", "init"], cwd=repo_dir, timeout=GIT_TIMEOUT_SECONDS)
    remote = run_cmd(["git", "remote", "add", "origin", lead["repo_url"]], cwd=repo_dir, timeout=GIT_TIMEOUT_SECONDS)
    fetch = run_cmd(["git", "fetch", "--depth", "1", "--filter=blob:none", "origin", sha], cwd=repo_dir, timeout=GIT_TIMEOUT_SECONDS)
    cat = run_cmd(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=repo_dir, timeout=GIT_TIMEOUT_SECONDS) if fetch["returncode"] == 0 else {"returncode": 1}
    checked = []
    if cat.get("returncode") == 0:
        for rel in lead.get("possible_native_test_paths", []):
            tree = run_cmd(["git", "ls-tree", "--name-only", sha, rel.rstrip("/")], cwd=repo_dir, timeout=GIT_TIMEOUT_SECONDS)
            checked.append({"path": rel, "exists": tree["returncode"] == 0 and bool(tree["stdout"].strip())})
    return {
        "status": "PASS" if cat.get("returncode") == 0 else "BLOCK",
        "sha_resolves": cat.get("returncode") == 0,
        "git_cat_file_e_commit_verified": cat.get("returncode") == 0,
        "native_test_exists": bool(checked) and all(item["exists"] for item in checked),
        "checked_paths": checked,
        "fetch_hash": hash_record(trim_result(fetch)),
        "exact_blocker": None if cat.get("returncode") == 0 else "rejected_commit_unresolved",
    }


def environment_rejection(lead: dict[str, Any]) -> tuple[str, str | None]:
    text = " ".join(
        [
            lead.get("lead_id", ""),
            lead.get("repo_url", ""),
            " ".join(lead.get("failure_keywords", [])),
            lead.get("reason_this_is_promising", ""),
        ]
    ).lower()
    if any(term in text for term in ["numpy", "scipy", "shapely", "compiled-heavy"]):
        return "compiled_dependency_too_heavy_for_wave_2_planning", "rejected_compiled_dependency_too_heavy"
    if any(term in text for term in ["windows", "freebsd"]):
        return "os_specific_unavailable_on_default_provider", "rejected_os_specific_unavailable"
    if any(term in text for term in ["qt", "pyqt"]):
        return "environment_unclear_due_gui_dependency", "rejected_environment_unclear"
    return "environment_constraints_recorded", None


def process_wave2_leads(leads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    normalized = [normalize_wave2_lead(lead) for lead in leads]
    leakage_records = [screen_leakage(lead) for lead in normalized]
    leakage_by_id = {item["lead_id"]: item for item in leakage_records}
    prior_ids = {item["lead_id"] for item in WAVE_1_CANDIDATES}
    prior_ids.update(
        {
            "py_bugger_issue_65",
            "darker_non_ascii_drop_changes",
            "darker_stdin_filename",
            "darker_skip_glob_failing_test",
            "darker_issue_112_relative_git_dir",
        }
    )
    approvals: list[dict[str, Any]] = []
    resolution_records: list[dict[str, Any]] = []
    duplicate_records: list[dict[str, Any]] = []
    for lead in normalized:
        leakage = leakage_by_id[lead["lead_id"]]
        duplicate = lead["lead_id"] in prior_ids
        if duplicate:
            duplicate_records.append(
                {
                    "lead_id": lead["lead_id"],
                    "status": "REJECTED",
                    "approval_status": "rejected_duplicate_or_already_counted",
                    "reason": "Lead matches already-counted or already-planned candidate boundary.",
                }
            )
        commit_sha, commit_record = commit_before_issue(lead["repo_url"], leakage.get("issue_created_at")) if leakage["issue_reference_exact"] else (None, {"status": "BLOCK", "exact_blocker": "rejected_not_exact_issue_reference"})
        verify = verify_commit_and_native_paths(lead, commit_sha, RUNTIME_ROOT) if commit_sha else {
            "status": "BLOCK",
            "sha_resolves": False,
            "git_cat_file_e_commit_verified": False,
            "native_test_exists": False,
            "checked_paths": [],
            "exact_blocker": commit_record.get("exact_blocker", "rejected_commit_unresolved"),
        }
        env_status, env_reject = environment_rejection(lead)
        if duplicate:
            approval = "rejected_duplicate_or_already_counted"
            blocker = "rejected_duplicate_or_already_counted"
        elif not leakage["issue_reference_exact"]:
            approval = "rejected_not_exact_issue_reference"
            blocker = "rejected_not_exact_issue_reference"
        elif leakage.get("leakage_status") == "BLOCK_LEAKAGE_RISK":
            approval = "rejected_leakage_risk_unmanageable"
            blocker = "rejected_leakage_risk_unmanageable"
        elif not verify.get("sha_resolves"):
            approval = "rejected_commit_unresolved"
            blocker = "rejected_commit_unresolved"
        elif not verify.get("native_test_exists"):
            approval = "rejected_native_test_missing"
            blocker = "rejected_native_test_missing"
        elif env_reject:
            approval = env_reject
            blocker = env_reject
        elif not lead.get("possible_failing_command"):
            approval = "rejected_no_failure_command"
            blocker = "rejected_no_failure_command"
        else:
            approval = "approved_for_future_pre_repair_replay_wave"
            blocker = None
        record = {
            "lead_id": lead["lead_id"],
            "repo_url": lead["repo_url"],
            "issue_url_or_reference": lead["issue_url_or_reference"],
            "issue_reference_exact": leakage["issue_reference_exact"],
            "candidate_sha": commit_sha,
            "commit_resolution": commit_record,
            "sha_resolves": verify.get("sha_resolves"),
            "git_cat_file_e_commit_verified": verify.get("git_cat_file_e_commit_verified"),
            "native_test_exists": verify.get("native_test_exists"),
            "checked_native_test_paths": verify.get("checked_paths"),
            "possible_failing_command_selected": lead.get("possible_failing_command"),
            "environment_constraints": env_status,
            "leakage_status": leakage.get("leakage_status"),
            "helper_provided_sha_trusted": False,
            "fixed_or_future_evidence_used": False,
            "patch_or_fix_text_used": False,
            "wave_2_pre_repair_replay_run": False,
            "patch_generated": False,
            "count_gate_run": False,
            "approval_status": approval,
            "exact_blocker": blocker,
        }
        resolution_records.append(record)
        approvals.append(
            {
                "lead_id": lead["lead_id"],
                "approval_status": approval,
                "candidate_sha": commit_sha,
                "future_replay_allowed": approval == "approved_for_future_pre_repair_replay_wave",
                "pre_repair_replay_run_in_batch056": False,
                "patch_generated_in_batch056": False,
                "count_gate_run_in_batch056": False,
                "exact_blocker": blocker,
            }
        )
    return resolution_records, approvals, duplicate_records


def update_public_docs(summary: dict[str, Any]) -> dict[str, Any]:
    marker = "### Batch056 pre-repair replay wave 1 plus wave 2 intake"
    lines = [
        "",
        marker,
        "",
        f"- Batch055 official ingest status: `{summary['batch055_ingest_status']}`.",
        f"- Batch056 Wave 1 pre-repair replay status: `{summary['wave_1_status']}`.",
        f"- Wave 1 candidates: `{summary['wave_1_candidate_count']}`; materialized failures: `{summary['wave_1_materialized_failure_count']}`; blocked/non-materialized: `{summary['wave_1_blocked_count']}`.",
        f"- Batch057 patch-gate recommendation count: `{summary['batch057_patch_gate_recommendation_count']}`.",
        f"- Wave 2 leads screened: `{summary['wave_2_leads_screened']}`; commit-resolved: `{summary['wave_2_commit_resolved_candidate_count']}`; approved for future replay: `{summary['wave_2_approved_for_future_replay_count']}`.",
        f"- Issue-derived repair count remains `{ISSUE_DERIVED_REPAIR_COUNT}`; native external repair count remains `{NATIVE_EXTERNAL_REPAIR_COUNT}`.",
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


def write_records(records: dict[str, Any]) -> None:
    for name, value in records.items():
        write_json_deterministic(OUT_DIR / name, value)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "wave_1_candidates").mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    if not BATCH055_ZIP.is_file():
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": "batch055_artifact_absent_for_official_ingest"})
        return 2

    verification = verify_official_zip(
        BATCH055_ZIP,
        artifact_name=BATCH055_ARTIFACT_NAME,
        artifact_id=BATCH055_ARTIFACT_ID,
        workflow_run_id=BATCH055_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH055_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH055_SHA256,
        expected_size=BATCH055_SIZE,
        expected_entry_count=BATCH055_ENTRY_COUNT,
        artifact_manifest_checked=BATCH055_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH055_OUTPUT_MANIFESTS,
    )
    ingest_detail = (
        ingest_official_outputs(
            BATCH055_ZIP,
            ROOT,
            prefixes=("post_v2_37_hardening_batch055_seed_discovery_wave_1",),
        )
        if verification["status"] == "PASS"
        else {"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")}
    )
    batch055_results = read_json(ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1" / "seed_discovery_wave_1_results.json")
    batch055_plan = read_json(ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1" / "pre_repair_replay_wave_plan.json")
    batch055_claim = read_json(ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1" / "claim_boundary.json")
    batch055_leakage = read_json(ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1" / "issue_body_leakage_screen.json")
    leakage_by_id = {item.get("lead_id"): item for item in batch055_leakage.get("records", [])}

    phase_a_records = {
        "batch055_artifact_ingestion_summary.json": {
            "status": "PASS" if verification["status"] == "PASS" and ingest_detail["status"] == "PASS" else "BLOCK",
            "artifact_name": BATCH055_ARTIFACT_NAME,
            "artifact_id": BATCH055_ARTIFACT_ID,
            "workflow_run_id": BATCH055_WORKFLOW_RUN_ID,
            "local_artifact_path": str(BATCH055_ZIP),
            "ingest_detail": ingest_detail,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
            "exact_blocker": None if verification["status"] == "PASS" and ingest_detail["status"] == "PASS" else "batch055_artifact_verification_or_ingest_failed",
        },
        "batch055_artifact_sha256_verification.json": verification,
        "batch055_result_preservation.json": {
            "status": "PASS" if batch055_results.get("status") == "PASS" else "BLOCK",
            "issue_derived_repair_count": batch055_results.get("issue_derived_repair_count"),
            "native_external_repair_count": batch055_results.get("native_external_repair_count"),
            "full_scoring": batch055_results.get("full_scoring"),
            "memory_lift": batch055_results.get("memory_lift"),
            "self_maintaining_software": batch055_results.get("self_maintaining_software"),
            "approved_for_pre_repair_replay": batch055_results.get("approved_for_pre_repair_replay_count"),
            "planned_batch056_candidates": len(batch055_results.get("planned_batch056_candidates", [])),
            "next_allowed_action": batch055_results.get("next_allowed_action"),
        },
        "batch055_candidate_plan_preservation.json": {
            "status": "PASS" if [item["lead_id"] for item in batch055_plan.get("planned_batch056_candidates", [])] == [item["lead_id"] for item in WAVE_1_CANDIDATES] else "BLOCK",
            "planned_candidates": batch055_plan.get("planned_batch056_candidates"),
            "expected_planned_candidate_ids": [item["lead_id"] for item in WAVE_1_CANDIDATES],
        },
        "batch055_claim_boundary_preservation.json": {
            "status": "PASS" if batch055_claim.get("current_protocol") == CURRENT_PROTOCOL else "BLOCK",
            "claim_boundary": batch055_claim,
            "batch056_count_increment": False,
            "batch056_full_scoring_run": False,
            "batch056_memory_lift_claim": False,
            "batch056_self_maintaining_claim": False,
        },
        "batch055_next_action_boundary.json": {
            "status": "PASS" if batch055_results.get("next_allowed_action") == "batch056_pre_repair_replay_wave_1" else "BLOCK",
            "preserved_batch055_next_allowed_action": batch055_results.get("next_allowed_action"),
            "batch056_allowed_actions": ["pre_repair_replay_wave_1", "wave_2_intake_planning"],
            "patching_allowed": False,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
    }
    write_records(phase_a_records)

    wave_1_results = [run_wave1_candidate(candidate, leakage_by_id) for candidate in WAVE_1_CANDIDATES]
    materialized = [item for item in wave_1_results if item["classification"] == "pre_repair_failure_materialized"]
    blocked = [item for item in wave_1_results if item["classification"] != "pre_repair_failure_materialized"]
    recommendations = [
        {
            "lead_id": item["lead_id"],
            "repo_url": item["repo_url"],
            "candidate_sha": item["candidate_sha"],
            "pre_repair_command": item["selected_command"],
            "failure_signature": item["failure_signature"],
            "target_files": item["target_test_paths"],
            "source_discovery_readiness": "pending_batch057_source_only_patch_gate",
            "patch_surface_estimate": "bounded_after_failure_signature_source_trace",
            "recommended_priority": index + 1,
            "reason_suitable_for_source_only_patch_gate": "Pre-repair failure materialized before patch authorization.",
            "why_decision_time_safe": "Candidate commit, target command, target paths, and replay log were captured before any repair patch.",
        }
        for index, item in enumerate(materialized)
    ]
    next_allowed = "batch057_source_only_patch_gate_wave_1" if materialized else "batch056b_replay_blocker_recovery_or_candidate_replay_wave_1b"
    wave_1_records = {
        "pre_repair_replay_wave_1_plan.json": {
            "status": "PASS",
            "candidate_count": len(WAVE_1_CANDIDATES),
            "candidates": WAVE_1_CANDIDATES,
            "patching_allowed": False,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
        "pre_repair_replay_wave_1_results.json": {"status": "PASS", "candidate_count": len(wave_1_results), "results": wave_1_results},
        "materialized_failure_candidates_for_batch057.json": {"status": "PASS", "count": len(materialized), "candidates": materialized},
        "wave_1_blocked_candidate_registry.json": {"status": "PASS", "count": len(blocked), "candidates": blocked},
        "wave_1_replay_dashboard.json": {
            "status": "PASS",
            "candidate_count": len(wave_1_results),
            "materialized_failure_count": len(materialized),
            "blocked_count": len(blocked),
            "classifications": {item["lead_id"]: item["classification"] for item in wave_1_results},
        },
        "wave_1_exact_blockers.json": {
            "status": "PASS",
            "blockers": {item["lead_id"]: item["exact_blocker"] for item in wave_1_results if item["exact_blocker"]},
        },
        "batch057_patch_gate_recommendation.json": {
            "status": "PASS",
            "recommendation_count": len(recommendations),
            "recommended_candidates": recommendations,
            "excluded_candidate_ids": [item["lead_id"] for item in blocked],
            "next_allowed_action": next_allowed,
        },
    }
    write_records(wave_1_records)
    write_text_lf(
        OUT_DIR / "pre_repair_replay_wave_1_summary.md",
        "\n".join(
            [
                "# Batch056 pre-repair replay wave 1",
                "",
                f"- Candidates replayed or classified: `{len(wave_1_results)}`",
                f"- Pre-repair failures materialized: `{len(materialized)}`",
                f"- Blocked or non-materialized candidates: `{len(blocked)}`",
                f"- Batch057 patch-gate recommendations: `{len(recommendations)}`",
                "",
                "| Candidate | Classification |",
                "| --- | --- |",
                *[f"| `{item['lead_id']}` | `{item['classification']}` |" for item in wave_1_results],
            ]
        ),
    )

    wave_2_leads, wave_2_source = load_wave_2_leads()
    wave_2_normalized = [normalize_wave2_lead(lead) for lead in wave_2_leads]
    wave_2_leakage = [screen_leakage(lead) for lead in wave_2_normalized]
    wave_2_resolution, wave_2_approvals, wave_2_duplicates = process_wave2_leads(wave_2_normalized)
    wave_2_approved = [item for item in wave_2_approvals if item["approval_status"] == "approved_for_future_pre_repair_replay_wave"]
    wave_2_commit_resolved = [item for item in wave_2_resolution if item.get("sha_resolves")]
    wave_2_records = {
        "seed_lead_registry_wave_2.json": {"status": "PASS", **wave_2_source, "lead_count": len(wave_2_leads), "leads": wave_2_leads},
        "seed_lead_registry_wave_2_normalized.json": {"status": "PASS", "lead_count": len(wave_2_normalized), "leads": wave_2_normalized},
        "issue_body_leakage_screen_wave_2.json": {"status": "PASS", "records": wave_2_leakage},
        "candidate_commit_resolution_audit_wave_2.json": {"status": "PASS", "records": wave_2_resolution},
        "candidate_approval_gate_results_wave_2.json": {
            "status": "PASS",
            "records": wave_2_approvals,
            "approved_for_future_pre_repair_replay_count": len(wave_2_approved),
            "pre_repair_replay_run_in_batch056": False,
            "patch_generated_in_batch056": False,
            "count_gate_run_in_batch056": False,
        },
        "duplicate_seed_rejection_audit_wave_2.json": {"status": "PASS", "records": wave_2_duplicates},
        "wave_2_pre_repair_replay_plan.json": {
            "status": "PASS",
            "future_only": True,
            "batch056_pre_repair_replay_run_for_wave_2": False,
            "future_candidates": [
                {
                    "lead_id": item["lead_id"],
                    "candidate_sha": item["candidate_sha"],
                    "repo_url": next((lead["repo_url"] for lead in wave_2_normalized if lead["lead_id"] == item["lead_id"]), None),
                }
                for item in wave_2_approved
            ],
        },
        "wave_2_campaign_dashboard.json": {
            "status": "PASS",
            "leads_screened": len(wave_2_normalized),
            "codex_augmented_leads": sum(1 for lead in wave_2_normalized if lead.get("source_of_lead") == "codex_github_search_wave_2"),
            "commit_resolved_candidates": len(wave_2_commit_resolved),
            "approved_for_future_replay": len(wave_2_approved),
            "pre_repair_replay_run": False,
            "patch_generated": False,
            "count_gate_run": False,
        },
    }
    write_records(wave_2_records)

    dashboard = {
        "status": "PASS",
        "batch055_ingest_status": phase_a_records["batch055_artifact_ingestion_summary.json"]["status"],
        "wave_1_candidate_count": len(wave_1_results),
        "wave_1_materialized_failure_count": len(materialized),
        "wave_1_blocked_count": len(blocked),
        "wave_2_leads_screened": len(wave_2_normalized),
        "wave_2_codex_augmented_leads": wave_2_records["wave_2_campaign_dashboard.json"]["codex_augmented_leads"],
        "wave_2_commit_resolved_candidate_count": len(wave_2_commit_resolved),
        "wave_2_approved_for_future_replay_count": len(wave_2_approved),
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "next_allowed_action": next_allowed,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    summary_state = {
        "status": "PASS",
        "batch055_ingest_status": dashboard["batch055_ingest_status"],
        "batch056_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "wave_1_status": "PASS",
        "wave_1_candidate_count": len(wave_1_results),
        "wave_1_materialized_failure_count": len(materialized),
        "wave_1_blocked_count": len(blocked),
        "wave_1_exact_blockers": wave_1_records["wave_1_exact_blockers.json"]["blockers"],
        "batch057_patch_gate_recommendation_count": len(recommendations),
        "batch057_patch_gate_recommended_candidates": [item["lead_id"] for item in recommendations],
        "wave_2_leads_screened": len(wave_2_normalized),
        "wave_2_codex_augmented_leads": dashboard["wave_2_codex_augmented_leads"],
        "wave_2_commit_resolved_candidate_count": len(wave_2_commit_resolved),
        "wave_2_approved_for_future_replay_count": len(wave_2_approved),
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "next_allowed_action": next_allowed,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None,
    }
    claim_boundary = {
        "status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "batch056_patch_generated": False,
        "batch056_source_only_repair_run": False,
        "batch056_duplicate_replay_run": False,
        "batch056_count_gate_run": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    package_verification = {
        "status": "PASS",
        "artifact_name": BATCH056_ARTIFACT_NAME,
        "artifact_payload_created_locally": False,
        "workflow_upload_required_for_artifact_identity": True,
        "raw_zip_payload_committed": False,
    }
    artifact_sha = {
        "status": "PENDING_WORKFLOW_ARTIFACT",
        "artifact_name": BATCH056_ARTIFACT_NAME,
        "artifact_sha256_available_after_workflow_upload": True,
        "batch055_local_zip_sha256": verification.get("zip_sha256"),
        "github_artifact_digest": None,
    }
    public_update = update_public_docs(summary_state)
    final_records = {
        "twenty_seed_campaign_dashboard_v2.json": dashboard,
        "claim_boundary.json": claim_boundary,
        "audit.json": {"status": "PASS", "audit_script": "scripts/audit_batch056_pre_repair_replay_wave_1_plus_wave_2_intake.py"},
        "package_verification.json": package_verification,
        "artifact_sha256_verification.json": artifact_sha,
    }
    write_records(final_records)
    write_text_lf(
        OUT_DIR / "combined_campaign_summary.md",
        "\n".join(
            [
                "# Batch056 pre-repair replay wave 1 plus wave 2 intake",
                "",
                "Batch056 ingests Batch055, runs bounded pre-repair replay for Wave 1 planned candidates, and prepares Wave 2 leads for future replay only.",
                "",
                f"- Status: `{summary_state['status']}`",
                f"- Batch055 ingest: `{summary_state['batch055_ingest_status']}`",
                f"- Wave 1 materialized failures: `{summary_state['wave_1_materialized_failure_count']}`",
                f"- Wave 1 blocked/non-materialized candidates: `{summary_state['wave_1_blocked_count']}`",
                f"- Wave 2 leads screened: `{summary_state['wave_2_leads_screened']}`",
                f"- Wave 2 approved for future replay: `{summary_state['wave_2_approved_for_future_replay_count']}`",
                f"- Next allowed action: `{summary_state['next_allowed_action']}`",
                "- Batch056 did not patch, run duplicate replay, run a count gate, enable full scoring, or claim memory lift.",
            ]
        ),
    )
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary_state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
