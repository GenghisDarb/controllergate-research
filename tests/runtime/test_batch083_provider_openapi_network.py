from __future__ import annotations

import zipfile
import json
from pathlib import Path

from controllergate.inputs.openapi_reference_resolver import resolve_closure
from controllergate.inputs.openapi_reference_verifier import verify_hashes
from controllergate.runtime.loopback_transport_verifier import verify_loopback
from controllergate.runtime.provider_dependency_graph import graph_from_wheels
from controllergate.batch083.orchestrator import reproduce


def wheel(path: Path, name: str, requires: list[str]) -> None:
    metadata=f"Metadata-Version: 2.1\nName: {name}\nVersion: 1\n"+"".join(f"Requires-Dist: {item}\n" for item in requires)
    with zipfile.ZipFile(path,"w") as archive: archive.writestr(f"{name}-1.dist-info/METADATA",metadata)


def test_provider_graph_requires_transitive_closure(tmp_path: Path) -> None:
    wheel(tmp_path/"root-1-py3-none-any.whl","root",["dependency"])
    assert graph_from_wheels(tmp_path)["state"]=="BLOCKED_REQUIRED_INPUT_ABSENT"
    wheel(tmp_path/"dependency-1-py3-none-any.whl","dependency",[])
    assert graph_from_wheels(tmp_path)["state"]=="PROVIDER_DEPENDENCY_GRAPH_CLOSED"


def test_provider_graph_excludes_inactive_markers_and_preserves_versions(tmp_path: Path) -> None:
    wheel(tmp_path/"root-1-py3-none-any.whl","root",["dependency>=2", "platform-only; sys_platform == 'plan9'", "test-only; extra == 'test'"])
    wheel(tmp_path/"dependency-2-py3-none-any.whl","dependency",[])
    result = graph_from_wheels(tmp_path)
    assert result["state"] == "PROVIDER_DEPENDENCY_GRAPH_CLOSED"
    assert result["nodes"]["root"]["requires"] == ["dependency"]
    assert len(result["nodes"]["root"]["requirements_skipped_by_environment_marker"]) == 2


def test_openapi_rooted_reachable_closure(tmp_path: Path) -> None:
    (tmp_path/"parts").mkdir();(tmp_path/"openapi.yaml").write_text("openapi: 3.0.0\ncomponents:\n  $ref: parts/a.yaml#/A\n",encoding="utf-8")
    (tmp_path/"parts/a.yaml").write_text("A:\n  type: string\n",encoding="utf-8");(tmp_path/"unused.yaml").write_text("unused: true\n",encoding="utf-8")
    result=resolve_closure(tmp_path)
    assert result["status"]=="PASS" and "parts/a.yaml" in result["reachable_files"] and "unused.yaml" in result["unreachable_yaml_files"]
    assert verify_hashes(tmp_path,result)["status"]=="PASS"


def test_openapi_rejects_missing_and_external_refs(tmp_path: Path) -> None:
    (tmp_path/"openapi.yaml").write_text("a: {$ref: missing.yaml}\nb: {$ref: https://example.com/x.yaml}\n",encoding="utf-8")
    result=resolve_closure(tmp_path);assert result["status"]=="BLOCK" and result["missing_references"] and result["external_references"]


def test_loopback_transport_executes() -> None:
    assert verify_loopback()["status"]=="PASS"


def test_reproducer_blocks_before_execution_when_provider_is_not_ready(tmp_path: Path) -> None:
    provider = tmp_path / "provider"
    provider.mkdir()
    (provider / "provider_v4_result.json").write_text(
        json.dumps({"provider_execution_ready": False, "exact_blocker": "provider_dependency_missing"}),
        encoding="utf-8",
    )
    result = reproduce("openbb", provider, tmp_path / "evidence", tmp_path / "runtime")
    assert result["status"] == "BLOCKED_EXACT_WITH_NEW_EVIDENCE"
    assert result["exact_blocker"] == "provider_dependency_missing"
    assert result["replays"] == []
