#!/usr/bin/env python3
"""Build Batch100 incident/provider separation and supersession registries."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.incident_identity_v2 import (
    IncidentProviderIdentityV2,
    IssueEpisodeIdentityV2,
    canonical_hash,
    validate_supersession,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


ISSUES = [
    dict(candidate_id="darker_issue_112_relative_git_dir", repository="https://github.com/akaihola/darker", issue_number=112,
         issue_created_at="2021-01-02T23:49:34Z", frozen_source_commit="a2d13656adfaa010fb6c7339087f3347ad2b815a",
         command=["darker", "--check", "src"], input={"GIT_DIR": ".git", "path": "src"},
         expected={"not_a_git_repository": False}, actual={"not_a_git_repository": True}, nodes=[], secondary=None,
         execution_provider="Python 3.7 series", execution_platform="linux", reported_provider="Python 3.7 series", reported_platform="linux",
         parity="PROVIDER_SERIES_ONLY", failures=["exact Python 3.7 microrelease is not identified by decision-time issue evidence"],
         old="darker --check src with relative GIT_DIR; incident not causally paired", new="darker-112-relative-absolute-git-dir-v2"),
    dict(candidate_id="py_bugger_issue_65", repository="https://github.com/ehmatthes/py-bugger", issue_number=65,
         issue_created_at="2025-07-10T16:05:15Z", frozen_source_commit="67cf214f2d619848e90280fd4469377123e81b94",
         command=["py-bugger", "--target-file", "<frozen-target>", "-n", "10"], input={"requested_mutations": 10, "deterministic_seed": 10065},
         expected={"reported_inserted_count_basis": "successful_or_persisted_mutations"}, actual={"reported_inserted_count": 35, "reported_target": "src/PIL/Image.py"}, nodes=[], secondary=None,
         execution_provider="Python 3.11", execution_platform="linux", reported_provider="Python 3 series", reported_platform="unspecified",
         parity="COMMAND_MISMATCH", failures=["Batch098 used a pytest node instead of the reported CLI operation"],
         old="tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys", new="py-bugger-65-cli-accounting-v2"),
    dict(candidate_id="cloudpickle_507_py313_typevar_distutils", repository="https://github.com/cloudpipe/cloudpickle", issue_number=507,
         issue_created_at="2023-07-03T14:28:38Z", frozen_source_commit="a76f0812ccdbbd1397f36d536dc4d57b6d0557d6",
         command=["python", "-m", "pytest", "<registered-cloudpickle-507-nodes>", "-q"], input={"sub_incidents": ["typevar_weakref", "distutils_removed"]},
         expected={"Python_3_12_supported": True}, actual={"typevar_weakref_type_error": True, "distutils_import_error": True},
         nodes=[
             "tests/cloudpickle_test.py::CloudPickleTest::test_generic_subclass",
             "tests/cloudpickle_test.py::CloudPickleTest::test_generic_type",
             "tests/cloudpickle_test.py::CloudPickleTest::test_locally_defined_class_with_type_hints",
             "tests/cloudpickle_test.py::CloudPickleTest::test_pickle_dynamic_typevar",
             "tests/cloudpickle_test.py::CloudPickleTest::test_pickle_dynamic_typevar_memoization",
             "tests/cloudpickle_test.py::CloudPickleTest::test_pickle_dynamic_typevar_tracking",
             "tests/cloudpickle_test.py::CloudPickleTest::test_module_importability",
         ], secondary=None, execution_provider="Python 3.13", execution_platform="linux", reported_provider="Python 3.12", reported_platform="linux",
         parity="TARGET_NODE_MISMATCH", failures=["Batch098 target test_extract_class_dict is not an issue 507 node", "Batch098 execution provider differs from incident series"],
         old="tests/cloudpickle_test.py::test_extract_class_dict", new="cloudpickle-507-split-sub-incidents-v2"),
    dict(candidate_id="freezegun_547_py313_datetimes_assertion", repository="https://github.com/spulec/freezegun", issue_number=547,
         issue_created_at="2024-05-08T18:36:04Z", frozen_source_commit="df263dcec48f43154a5873eb0dff2d4ba94374da",
         command=["python", "-m", "pytest", "<three-exact-nodes>", "-q"], input={"timezone": "UTC", "fixture_date": "2013-04-09"},
         expected={"frozen_time_today": "2013-04-09"}, actual={"actual": "2013-04-09T02:00:00", "relation": "FakeDate != datetime"},
         nodes=[
             "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time",
             "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time_with_func",
             "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_hello",
         ], secondary=None, execution_provider="Python 3.13 series", execution_platform="linux", reported_provider="Python 3.13.0b1", reported_platform="linux",
         parity="PROVIDER_MICRO_UNRESOLVED", failures=["authenticated Python 3.13.0b1 provider is not frozen"],
         old="whole tests/test_datetimes.py", new="freezegun-547-exact-three-nodes-v2"),
    dict(candidate_id="audioread_144_py313_aifc_removed", repository="https://github.com/beetbox/audioread", issue_number=144,
         issue_created_at="2024-06-13T15:58:05Z", frozen_source_commit="577f8e2cbe99f33dd7d236deb1626e372f4762e9",
         command=["python", "-m", "pytest", "<four-exact-audioread-nodes>", "-q"], input={"imports": ["aifc", "audioread.rawread"]},
         expected={"aifc_available": True}, actual={"exception": "ModuleNotFoundError", "module": "aifc"},
         nodes=["test/test_audioread.py::test_audioread_early_exit[test-1]", "test/test_audioread.py::test_audioread_early_exit[test-2]", "test/test_audioread.py::test_audioread_full[test-1]", "test/test_audioread.py::test_audioread_full[test-2]"],
         secondary=None, execution_provider="Python 3.13 series", execution_platform="linux", reported_provider="Python 3.13.0b2", reported_platform="linux",
         parity="PROVIDER_MICRO_UNRESOLVED", failures=["authenticated Python 3.13.0b2 provider is not frozen"],
         old="tox -e py313 whole environment", new="audioread-144-provider-source-route-factorial-v2"),
    dict(candidate_id="pytest_13480_wdefault_unraisable_threadexception", repository="https://github.com/pytest-dev/pytest", issue_number=13480,
         issue_created_at="2025-06-03T08:58:15Z", frozen_source_commit="592c27ca4bf1db4abe62bf86be422a143aad0984",
         command=["python", "-m", "pytest", "<three-exact-nodes>", "-Wdefault", "-q"], input={"warning_mode": "default"},
         expected={"nested_exit_code": 0}, actual={"nested_exit_code": 3, "collection_exit_code_4_is_issue": False},
         nodes=["testing/test_threadexception.py::test_unhandled_thread_exception_after_teardown", "testing/test_unraisableexception.py::test_refcycle_unraisable", "testing/test_warnings.py::test_works_with_filterwarnings"],
         secondary=None, execution_provider="Python 3.13 series", execution_platform="linux", reported_provider="Python 3.13.3", reported_platform="linux",
         parity="TARGET_NODE_MISMATCH", failures=["Batch098 primary command used whole files", "prior return-code 4 was a collection mismatch, not the issue"],
         old="three whole test files with -Wdefault", new="pytest-13480-exact-warning-nodes-v2"),
    dict(candidate_id="incident_openbb_7585_modular_openapi_reproducer", repository="https://github.com/OpenBB-finance/OpenBB.git", issue_number=7585,
         issue_created_at="2026-07-13T18:15:59Z", frozen_source_commit="1c74893140292944e71ff5cdd9536edf12f05483",
         command=["openbb", "--generate-spec", "--server", "<loopback>", "--openapi-path", "/openapi.yaml", "--output", "eodhd.spec"], input={"topology": "modular-$ref"},
         expected={"command_count": ">0"}, actual={"command_count": 0, "silent_failure": True}, nodes=[],
         secondary={"repository": "https://github.com/EodHistoricalData/EODHD-openapi.git", "commit": "901d6209e5738b0cbb42d48553c51fdc5f98bd7e"},
         execution_provider="Python 3.11 Ubuntu-compatible", execution_platform="linux", reported_provider="Python 3.11", reported_platform="Debian 12",
         parity="INCIDENT_NOT_MATERIALIZED", failures=["Batch098 target operation did not run", "exact Debian 12 parity not yet executed"],
         old="registered target not run", new="openbb-7585-modular-flattened-v2"),
    dict(candidate_id="incident_poetry_10974_init_duplicate_name", repository="https://github.com/python-poetry/poetry.git", issue_number=10974,
         issue_created_at="2026-07-08T23:23:39Z", frozen_source_commit="811a12dae0fe81f199e3f1b88b8b8be9eed543c2",
         command=["poetry", "init", "-n"], input={"working_directory": "my project with spaces", "project_name_mode": "inferred"},
         expected={"project_name": "my-project-with-spaces"}, actual={"project_name": "my project with spaces"}, nodes=[], secondary=None,
         execution_provider="Python 3.11", execution_platform="linux", reported_provider="Python 3.13 / Poetry 2.4.1", reported_platform="windows",
         parity="PLATFORM_MISMATCH", failures=["Batch098 used Linux and Python 3.11", "authoritative incident is Windows/Python 3.13"],
         old="Linux/Python 3.11 target not run", new="poetry-10974-windows-path-name-factorial-v2"),
]


def main() -> int:
    contracts = {row["candidate_id"]: row for row in (json.loads(line) for line in (ROOT / "configs/candidate_execution_contracts_v2.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
    issue_rows: list[dict] = []
    provider_rows: list[dict] = []
    supersessions: list[dict] = []
    for item in ISSUES:
        issue = IssueEpisodeIdentityV2(
            candidate_id=item["candidate_id"], repository=item["repository"], issue_number=item["issue_number"],
            issue_created_at=item["issue_created_at"], issue_snapshot_cutoff=item["issue_created_at"],
            frozen_source_commit=item["frozen_source_commit"], issue_reported_command=item["command"],
            issue_reported_input=item["input"], issue_reported_expected_behavior=item["expected"],
            issue_reported_actual_behavior=item["actual"], issue_reported_exact_nodes=item["nodes"],
            issue_reported_secondary_source=item["secondary"],
        ).record()
        issue_rows.append(issue)
        provider_rows.append(IncidentProviderIdentityV2(
            candidate_id=item["candidate_id"], batch098_execution_provider=item["execution_provider"],
            batch098_execution_platform=item["execution_platform"], issue_reported_provider=item["reported_provider"],
            issue_reported_platform=item["reported_platform"], parity_status=item["parity"],
            parity_failures=item["failures"], superseded_target_contract=item["old"], new_incident_contract=item["new"],
        ).record())
        old = contracts[item["candidate_id"]]
        supersession = {
            "candidate_id": item["candidate_id"], "historical_contract_hash": old["contract_hash"],
            "historical_contract_preserved": True, "supersession_reason": item["failures"],
            "incident_contract": {"contract_id": item["new"], "exact_command": item["command"], "exact_nodes": item["nodes"], "input": item["input"], "source_commit": item["frozen_source_commit"]},
            "provenance": {"issue_number": item["issue_number"], "issue_snapshot_cutoff": item["issue_created_at"], "identity_hash": issue["identity_hash"]},
            "authority_allowed": "Batch100 incident rematerialization only",
            "authority_forbidden": ["rewrite historical Batch098 contract", "ownership without matched execution", "patch", "count", "release"],
        }
        validate_supersession(supersession)
        supersession["supersession_hash"] = canonical_hash(supersession)
        supersessions.append(supersession)
    write_jsonl(ROOT / "configs/batch100_incident_identity_registry_v2.jsonl", issue_rows)
    write_jsonl(ROOT / "configs/batch100_incident_provider_registry_v2.jsonl", provider_rows)
    write_jsonl(ROOT / "configs/batch100_candidate_contract_supersession_registry_v1.jsonl", supersessions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
