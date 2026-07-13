from __future__ import annotations

import hashlib
import inspect
from typing import Any

from controllergate.runtime.html_semantic_diff import compare_html_semantics
from controllergate.runtime.unified_diff_contract import parse_unified_diff


def verify_html_title_only_change(
    *, before: str, after: str, patch_text: str, expected_file: str
) -> dict[str, Any]:
    parsed = parse_unified_diff(patch_text)
    semantic = compare_html_semantics(before, after)
    exact_file = parsed["changed_files"] == [expected_file]
    passed = (
        parsed["status"] == "PASS"
        and parsed["hunk_count"] == 1
        and exact_file
        and semantic["status"] == "PASS"
    )
    verifier_source = inspect.getsource(verify_html_title_only_change)
    return {
        "status": "PASS" if passed else "BLOCK",
        "preimage_hash": hashlib.sha256(before.encode("utf-8")).hexdigest(),
        "postimage_hash": hashlib.sha256(after.encode("utf-8")).hexdigest(),
        "patch_hash": hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
        "verifier_hash": hashlib.sha256(verifier_source.encode("utf-8")).hexdigest(),
        "expected_file": expected_file,
        "actual_changed_files": parsed["changed_files"],
        "exact_file_match": exact_file,
        "diff_contract": parsed,
        "semantic_witness": semantic,
        "independent_recomputation_result": "PASS" if passed else "BLOCK",
    }
