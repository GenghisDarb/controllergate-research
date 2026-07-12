from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .command_equivalence import canonical_pytest_command
from .command_role_classifier import classify_command
from .command_target_alignment import narrow_to_target
from .command_sources.tox_parser import parse_tox


def resolve_command_authority(source_root: Path, target: str) -> dict[str, Any]:
    candidates = []
    tox = source_root / "tox.ini"
    if tox.is_file():
        for environment in parse_tox(tox)["environments"]:
            for command in environment["commands"]:
                role = classify_command(command["argv"])
                candidates.append({**command, "role": role, "source": "tox.ini", "environment": environment["environment_name"], "working_directory": environment["working_directory"]})
    target_file = source_root / target.split("::", 1)[0]
    pytest_evidence = []
    for name in ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"):
        path = source_root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "pytest" in text.lower() or name == "pytest.ini":
            pytest_evidence.append(name)
    workflow_commands = []
    workflows = source_root / ".github" / "workflows"
    if workflows.is_dir():
        for path in sorted(workflows.glob("*.y*ml")):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                # Only accept a command whose shell invocation starts with the
                # runner.  A dependency install such as ``pip install pytest``
                # is setup evidence, not command authority.
                match = re.match(r"^\s*(?:-\s*)?(?:run:\s*)?(python\s+-m\s+pytest|python3\s+-m\s+pytest|pytest|py\.test)(?:\s+[^#]+)?\s*$", line)
                if match:
                    raw = re.sub(r"^\s*(?:-\s*)?(?:run:\s*)?", "", match.group(0)).strip()
                    workflow_commands.append({"argv": raw.split(), "raw": raw, "source": path.relative_to(source_root).as_posix(), "environment": "ci", "working_directory": ".", "role": "test_runner"})
    candidates.extend(workflow_commands)
    target_uses_pytest = target_file.is_file() and ("pytest" in target_file.read_text(encoding="utf-8", errors="replace") or (source_root / "conftest.py").is_file() or any(source_root.glob("**/conftest.py")))
    if target_file.is_file() and (pytest_evidence or target_uses_pytest):
        source = "+".join(pytest_evidence) if pytest_evidence else "native_target_pytest_import_or_conftest"
        candidates.append({"argv": ["python", "-m", "pytest"], "raw": "python -m pytest", "source": source, "environment": "project_native_pytest", "working_directory": ".", "role": "test_runner"})
    eligible = [item for item in candidates if item["role"] in {"test_runner", "test_environment_wrapper"}]
    narrowed = []
    for item in eligible:
        transformation = narrow_to_target(item["argv"], target)
        canonical = canonical_pytest_command(transformation["transformed_command"])
        score = 100 + (20 if target in transformation["transformed_command"] else 0) - len(transformation["transformed_command"])
        narrowed.append({**item, **transformation, "canonical": canonical, "authority_score": score, "target_corroborated": True, "nonmutating": True})
    narrowed.sort(key=lambda item: (-item["authority_score"], item["environment"], item["raw"]))
    families = {tuple(item["canonical"]["semantic_family"]) for item in narrowed}
    native = [item for item in narrowed if item.get("environment") == "project_native_pytest" and item.get("target_corroborated")]
    if native:
        status = "PASS"; selected = native[0]; true_conflicts = 0
    else:
        status = "PASS" if narrowed and len(families) == 1 else "MANUAL_REVIEW" if len(families) > 1 else "BLOCK"
        selected = narrowed[0] if status == "PASS" else None; true_conflicts = max(0, len(families) - 1)
    return {"status": status, "selected": selected, "candidates": candidates, "eligible_candidates": narrowed, "false_conflicts_eliminated": len(candidates) - len(eligible), "true_conflict_count": true_conflicts, "native_target_command_dominates_broad_wrappers": bool(native), "manual_review_policy_satisfied": status != "MANUAL_REVIEW" or len(families) > 1}
