from __future__ import annotations

import sys
from pathlib import Path

import pytest

from controllergate.amds.incident_outcome import (
    IncidentOutcomeContract,
    IncidentOutcomeFamily,
    verify_incident_outcome,
)
from controllergate.amds.provider_orthology import (
    ProviderRecipe,
    ProviderSourceClass,
    audit_provider_identity_uniqueness,
    verify_orthology_transfer,
)
from controllergate.execution.local_service import BrokeredLocalService


def recipe(candidate: str = "candidate-a", interpreter: str = "python-3.11") -> ProviderRecipe:
    return ProviderRecipe(
        candidate_id=candidate,
        source_commit="a" * 40,
        supported_runtime_range=">=3.10,<3.12",
        supported_platforms=("linux",),
        historical_provider_evidence=("sha256:" + "1" * 64,),
        provider_source_class=ProviderSourceClass.HISTORICAL_DECISION_TIME_SAFE,
        interpreter_identity=interpreter,
        abi_tags=("cp311",),
        platform_tags=("manylinux_2_28_x86_64",),
        dependency_lock_identity="sha256:" + "2" * 64,
        secondary_cofactor_lock_identity=None,
        install_argv=("python", "-m", "pip", "install", "."),
        working_directory_policy="source_root",
        environment_allowlist=("PATH",),
        network_acquisition_policy="bounded_read_only_acquisition",
        target_argv=("python", "-m", "pytest", "-q"),
        semantic_outcome_contract_id="contract-a",
        positive_control_id="positive-a",
        negative_control_id="negative-a",
        selection_evidence_hashes=("3" * 64,),
        selected_before_target_execution=True,
        orthology_source_environment="linux/cp311",
        orthology_target_environment="linux/cp311",
        preserved_invariants=("python_minor", "abi", "platform"),
        allowed_adaptations=("runtime_root",),
        forbidden_adaptations=("source_revision", "test_tree"),
        producer_identity="provider_recipe_selector",
        verifier_identity="provider_recipe_verifier",
    )


def test_provider_recipe_selected_before_target_and_unique() -> None:
    first = recipe()
    first.validate()
    assert verify_orthology_transfer(first, {
        "candidate_id": first.candidate_id,
        "source_commit": first.source_commit,
        "interpreter_identity": first.interpreter_identity,
        "abi_tags": list(first.abi_tags),
        "platform_tags": list(first.platform_tags),
        "dependency_lock_identity": first.dependency_lock_identity,
    })["status"] == "PASS"
    second = recipe("candidate-b", "python-3.10")
    assert audit_provider_identity_uniqueness([first, second])["status"] == "PASS"


def test_provider_relabel_and_after_outcome_are_rejected() -> None:
    item = recipe()
    result = verify_orthology_transfer(item, {
        "candidate_id": "candidate-b",
        "source_commit": item.source_commit,
        "interpreter_identity": item.interpreter_identity,
        "abi_tags": list(item.abi_tags),
        "platform_tags": list(item.platform_tags),
        "dependency_lock_identity": item.dependency_lock_identity,
        "selected_after_target_outcome": True,
    })
    assert result["status"] == "BLOCK"
    assert "candidate_relabeling_detected" in result["reasons"]
    assert "provider_selected_after_target_outcome" in result["reasons"]


def test_verified_platform_orthology_preserves_python_minor() -> None:
    item = recipe()
    result = verify_orthology_transfer(item, {
        "candidate_id": item.candidate_id,
        "source_commit": item.source_commit,
        "interpreter_identity": "cpython-3.11-linux-x86_64",
        "abi_tags": ["cp311"],
        "platform_tags": ["linux-x86_64"],
        "dependency_lock_identity": item.dependency_lock_identity,
        "orthology_invariants_verified": True,
    })
    assert result["status"] == "PASS"
    changed = dict(
        candidate_id=item.candidate_id, source_commit=item.source_commit,
        interpreter_identity="cpython-3.12-linux-x86_64", abi_tags=["cp312"],
        platform_tags=["linux-x86_64"], dependency_lock_identity=item.dependency_lock_identity,
        orthology_invariants_verified=True,
    )
    assert verify_orthology_transfer(item, changed)["status"] == "BLOCK"


def incident_contract(family: IncidentOutcomeFamily = IncidentOutcomeFamily.SUCCESS_WITH_INVALID_PRODUCT) -> IncidentOutcomeContract:
    return IncidentOutcomeContract(
        contract_id="openapi-invalid-product-v1",
        candidate_id="openapi-candidate",
        run_id="run-1",
        frame_id="frame-1",
        command_identity="command-hash",
        family=family,
        expected_return_codes=(0,),
        required_product_paths=("generated.spec",),
        product_schema={"type": "object"},
        product_semantic_invariants={"product_exists": True, "product_parses": True, "command_count": 0, "fetcher_count": 0},
        positive_control_id="positive",
        negative_control_id="negative",
        allowed_output_fields=("product_exists", "product_parses", "command_count", "fetcher_count", "producer_operation_hash"),
        exact_output_identities=("generated_product_structure",),
        producer_identity="target_executor",
        verifier_identity="typed_product_verifier",
        failure_terminal="typed_incident_not_materialized",
        reopen_condition="run the registered command and controls from fresh source",
    )


def test_exit_zero_invalid_product_is_semantically_verified() -> None:
    contract = incident_contract()
    process = {"candidate_id": "openapi-candidate", "run_id": "run-1", "command_identity": "command-hash", "return_code": 0, "record_hash": "op-1"}
    product = {"product_exists": True, "product_parses": True, "command_count": 0, "fetcher_count": 0, "producer_operation_hash": "op-1"}
    controls = {"positive": {"status": "PASS"}, "negative": {"status": "PASS"}}
    assert verify_incident_outcome(contract, process=process, product=product, controls=controls)["status"] == "PASS"


def test_transport_failure_is_not_target_incident() -> None:
    contract = incident_contract()
    process = {"candidate_id": "openapi-candidate", "run_id": "run-1", "command_identity": "command-hash", "return_code": 0, "record_hash": "op-1", "transport_failure": True}
    product = {"product_exists": True, "product_parses": True, "command_count": 0, "fetcher_count": 0, "producer_operation_hash": "op-1"}
    controls = {"positive": {"status": "PASS"}, "negative": {"status": "PASS"}}
    result = verify_incident_outcome(contract, process=process, product=product, controls=controls)
    assert result["status"] == "BLOCK"
    assert "transport_failure_is_not_target_incident" in result["reasons"]


def test_broad_marker_contract_is_rejected() -> None:
    value = incident_contract()
    object.__setattr__(value, "exact_output_identities", ("warning",))
    with pytest.raises(ValueError, match="broad markers"):
        value.validate()


def test_brokered_loopback_service_closes_port(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("ready", encoding="utf-8")
    service = BrokeredLocalService(
        service_id="test-service",
        candidate_id="candidate",
        run_id="run",
        frame_id="frame",
        argv_template=(sys.executable, "-m", "http.server", "{PORT}", "--bind", "127.0.0.1"),
        cwd=tmp_path,
        runtime_root=tmp_path,
    )
    service.start()
    payload, _ = service.request("/index.html")
    assert payload == b"ready"
    service.stop()
    result = service.lifecycle_record()
    assert result["status"] == "PASS"
    assert result["orphan_process"] is False


def test_non_loopback_service_binding_is_rejected(tmp_path: Path) -> None:
    service = BrokeredLocalService(
        service_id="bad",
        candidate_id="candidate",
        run_id="run",
        frame_id="frame",
        argv_template=(sys.executable, "-m", "http.server", "{PORT}"),
        cwd=tmp_path,
        runtime_root=tmp_path,
        host="0.0.0.0",
    )
    with pytest.raises(ValueError, match="loopback"):
        service.start()
