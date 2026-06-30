from controllergate.core.precondition_resolution import declared_dependency_specs, declared_optional_group


def test_declared_dependency_group_supplies_bounded_target_test_tools() -> None:
    metadata = {
        "optional_dependency_groups": ["black", "isort"],
        "dependency_groups": {"dev": ["pytest>=6.2.0", "pytest-kwparametrize>=0.0.3", "mypy>=1.15"]},
        "declared_dependency_strings": ["black>=24.10.0", "isort>=5.1.0"],
    }
    assert declared_optional_group(metadata, "black") is True
    assert declared_dependency_specs(metadata, ["pytest", "pytest-kwparametrize"]) == [
        "pytest>=6.2.0",
        "pytest-kwparametrize>=0.0.3",
    ]


def test_undeclared_dependency_is_not_implicitly_authorized() -> None:
    metadata = {"declared_dependency_strings": ["black>=24.10.0"], "dependency_groups": {}}
    assert declared_dependency_specs(metadata, ["pytest"]) == []
