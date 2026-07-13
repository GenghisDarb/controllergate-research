from __future__ import annotations

import hashlib
from typing import Any

from .contamination_section_parser import solution_sections
from .repair_recipe_detector import detect_repair_recipe


def classify_contamination_v2(text: str) -> dict[str, Any]:
    sections = solution_sections(text)
    recipes = detect_repair_recipe(text)
    hard = bool(sections or recipes)
    return {
        "classification": "HARD_REJECT_SOLUTION_CONTAMINATION" if hard else "CLEAN",
        "solution_section_count": len(sections),
        "repair_recipe_hits": recipes,
        "solution_section_hashes": [hashlib.sha256(item.encode()).hexdigest() for item in sections],
        "complete_reproducer_alone_is_contamination": False,
        "traceback_alone_is_contamination": False,
        "hard_reject": hard,
    }
