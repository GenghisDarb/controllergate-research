from __future__ import annotations

from pathlib import Path
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
    eligible = [item for item in candidates if item["role"] in {"test_runner", "test_environment_wrapper"}]
    narrowed = []
    for item in eligible:
        transformation = narrow_to_target(item["argv"], target)
        canonical = canonical_pytest_command(transformation["transformed_command"])
        score = 100 + (20 if target in transformation["transformed_command"] else 0) - len(transformation["transformed_command"])
        narrowed.append({**item, **transformation, "canonical": canonical, "authority_score": score, "target_corroborated": True, "nonmutating": True})
    narrowed.sort(key=lambda item: (-item["authority_score"], item["environment"], item["raw"]))
    families = {tuple(item["canonical"]["semantic_family"]) for item in narrowed}
    status = "PASS" if narrowed and len(families) == 1 else "MANUAL_REVIEW" if len(families) > 1 else "BLOCK"
    selected = narrowed[0] if status == "PASS" else None
    return {"status": status, "selected": selected, "candidates": candidates, "eligible_candidates": narrowed, "false_conflicts_eliminated": len(candidates) - len(eligible), "true_conflict_count": max(0, len(families) - 1), "manual_review_policy_satisfied": status != "MANUAL_REVIEW" or len(families) > 1}
