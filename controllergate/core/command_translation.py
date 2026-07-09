from __future__ import annotations

from dataclasses import dataclass

ALLOWED_COMMAND_SOURCES = {
    "pyproject.toml",
    "tox.ini",
    "noxfile.py",
    "setup.cfg",
    "setup.py",
    "requirements.txt",
    "requirements-dev.txt",
    "ci_workflow_in_buggy_checkout",
    "project_local_testing_docs_in_buggy_checkout",
    "verified_non_circular_benchmark_metadata",
}

FORBIDDEN_COMMAND_SHORTCUTS = {
    "blind --ignore",
    "blind --override",
    "blind --rootdir",
    "blind PYTHONPATH",
    "minversion suppression",
    "future docs",
    "issue workaround text",
}


@dataclass(frozen=True)
class CommandManifestValidation:
    status: str
    blocker: str | None
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "blocker": self.blocker, "errors": list(self.errors)}


def build_candidate_command_manifest(
    *,
    candidate_id: str,
    repo_url: str,
    candidate_sha: str,
    native_test_path: str | None,
    declared_command_source: str,
    declared_command_source_file: str,
    working_directory: str,
    python_version: str,
    runner_package: str,
    target_package: str,
    command_string: str,
    provider_setup_required: bool = True,
    collection_command: str | None = None,
) -> dict[str, object]:
    runner_target_split_required = runner_package == target_package
    return {
        "candidate_id": candidate_id,
        "repo_url": repo_url,
        "candidate_sha": candidate_sha,
        "native_test_path": native_test_path,
        "declared_command_source": declared_command_source,
        "declared_command_source_file": declared_command_source_file,
        "working_directory": working_directory,
        "python_version": python_version,
        "provider_setup_required": provider_setup_required,
        "runner_package": runner_package,
        "target_package": target_package,
        "runner_target_split_required": runner_target_split_required,
        "command_string": command_string,
        "collection_command": collection_command or command_string,
        "diagnostic_command_template": "{python} -m {runner} {target} --collect-only",
        "forbidden_command_shortcuts": sorted(FORBIDDEN_COMMAND_SHORTCUTS),
        "command_boundary_status": "runner_target_collision_unresolved_self_runner" if runner_target_split_required else "command_boundary_ready",
        "next_allowed_action": "prove_runner_target_import_origin" if runner_target_split_required else "pre_repair_replay_step",
    }


def validate_candidate_command_manifest(manifest: dict[str, object]) -> CommandManifestValidation:
    errors: list[str] = []
    required = [
        "candidate_id",
        "repo_url",
        "candidate_sha",
        "declared_command_source",
        "declared_command_source_file",
        "working_directory",
        "python_version",
        "runner_package",
        "target_package",
        "command_string",
        "collection_command",
        "forbidden_command_shortcuts",
        "command_boundary_status",
        "next_allowed_action",
    ]
    for key in required:
        value = manifest.get(key)
        if key not in manifest or value is None or value == "":
            errors.append(f"missing:{key}")
    source = str(manifest.get("declared_command_source_file", ""))
    if source not in ALLOWED_COMMAND_SOURCES:
        errors.append(f"untrusted_command_source:{source}")
    command = str(manifest.get("command_string", ""))
    forbidden_hits = [shortcut for shortcut in FORBIDDEN_COMMAND_SHORTCUTS if shortcut.split()[0] in command and "blind" in shortcut]
    if forbidden_hits:
        errors.append("forbidden_command_shortcut_detected")
    blocker = None
    if errors:
        blocker = "command_manifest_invalid"
    elif manifest.get("runner_package") == manifest.get("target_package") and manifest.get("command_boundary_status") != "runner_target_collision_unresolved_self_runner":
        blocker = "runner_target_collision_unclassified"
        errors.append(blocker)
    return CommandManifestValidation("PASS" if not errors else "FAIL", blocker, tuple(errors))
