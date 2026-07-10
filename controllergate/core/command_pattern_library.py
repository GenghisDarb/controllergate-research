from __future__ import annotations

from typing import Any


def native_command_pattern_library() -> dict[str, Any]:
    families = [
        ("pytest", ["pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg"], ["tests/", "test_*.py"], ["python -m pytest <target>", "pytest <target>"]),
        ("unittest", ["setup.py", "pyproject.toml"], ["tests/", "test*.py"], ["python -m unittest <module>"]),
        ("tox", ["tox.ini"], ["tests/"], ["tox -e <env> -- <target>"]),
        ("nox", ["noxfile.py"], ["tests/"], ["nox -s <session> -- <target>"]),
        ("hatch", ["pyproject.toml"], ["tests/"], ["hatch run test"]),
        ("poetry", ["pyproject.toml", "poetry.lock"], ["tests/"], ["poetry run pytest <target>"]),
        ("pdm", ["pyproject.toml", "pdm.lock"], ["tests/"], ["pdm run pytest <target>"]),
        ("uv", ["pyproject.toml", "uv.lock"], ["tests/"], ["uv run pytest <target>"]),
        ("make", ["Makefile"], ["tests/"], ["make test"]),
        ("npm_yarn_pnpm", ["package.json"], ["test/", "tests/"], ["npm test", "yarn test", "pnpm test"]),
        ("cargo", ["Cargo.toml"], ["tests/"], ["cargo test <target>"]),
        ("go_test", ["go.mod"], ["*_test.go"], ["go test ./..."]),
        ("maven_gradle", ["pom.xml", "build.gradle", "build.gradle.kts"], ["src/test"], ["mvn test", "gradle test"]),
        ("project_specific_ci_script", [".github/workflows/", ".gitlab-ci.yml"], ["project-specific"], ["project-local CI command only if exact declaration is verified"]),
        ("benchmark_harness", ["benchmark/", "benchmarks/"], ["benchmark harness"], ["manual approval required"]),
        ("manual_artifact_required", [], [], ["manual artifact required"]),
        ("runtime_connector_required", [], [], ["runtime connector required"]),
    ]
    return {
        "status": "PASS",
        "records": [
            {
                "pattern_id": name,
                "source_files": source_files,
                "metadata_signatures": source_files,
                "test_tree_signatures": test_tree,
                "runner_dependency_signatures": [name],
                "allowed_command_templates": commands,
                "forbidden_command_templates": ["commands that skip tests", "commands that mutate config", "commands derived from fix text"],
                "confidence_rules": {
                    "exact_declared_command": "candidate-era command text is explicitly declared with target",
                    "high_confidence_project_local_inference": "project-local metadata and test tree agree without fix/gold/future evidence",
                    "medium_confidence_requires_manual_artifact": "framework family present but target is ambiguous",
                    "low_confidence_routing_only": "only weak metadata hints exist",
                    "blocked_forbidden_or_untrusted": "forbidden evidence or unsafe source boundary",
                },
                "decision_time_safe_inputs": ["candidate-era source metadata", "tracked test tree", "declared dependency metadata", "CI config before fix"],
                "forbidden_inputs": ["fixed commits", "gold patches", "future docs", "issue-comment fix text", "hidden benchmark labels"],
                "harness_origin_requirements": "candidate-local or approved external source only",
                "runner_target_requirements": "target path or node must be decision-time safe",
                "provider_capsule_requirements": "isolated provider/runtime capsule when nontrivial dependencies exist",
                "minimum_confidence_for_probe": "high_confidence_project_local_inference",
                "audit_status": "PASS",
            }
            for name, source_files, test_tree, commands in families
        ],
    }
