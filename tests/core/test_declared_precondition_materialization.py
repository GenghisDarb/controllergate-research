from controllergate.core.precondition_resolution import declared_optional_group, declared_extra_install_commands


def test_declared_extra_is_detected_before_final_precondition_block() -> None:
    metadata = {"optional_dependency_groups": ["black", "isort"]}
    assert declared_optional_group(metadata, "black") is True
    assert declared_optional_group(metadata, "isort") is True


def test_declared_black_extra_install_command_is_not_skipped_without_committed_runtime() -> None:
    commands = declared_extra_install_commands("<venv_python>", ["black"])
    assert commands == [["<venv_python>", "-m", "pip", "install", "-e", ".[black]"]]
