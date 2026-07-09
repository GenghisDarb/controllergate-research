from __future__ import annotations

from pathlib import Path

VERSION_ORIGIN_CLASSES = {
    "version_origin_ok",
    "version_origin_missing_tags",
    "version_origin_dirty_workspace",
    "version_origin_not_git_checkout",
    "version_origin_untrusted_future_tag_exposure",
    "version_origin_unknown",
}


def classify_version_origin(
    *,
    is_git_checkout: bool,
    has_reachable_tags: bool,
    dirty_workspace: bool,
    future_tag_exposure_detected: bool = False,
) -> str:
    if not is_git_checkout:
        return "version_origin_not_git_checkout"
    if future_tag_exposure_detected:
        return "version_origin_untrusted_future_tag_exposure"
    if dirty_workspace:
        return "version_origin_dirty_workspace"
    if not has_reachable_tags:
        return "version_origin_missing_tags"
    return "version_origin_ok"


def safe_git_tag_acquisition_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "do_not_fetch_tags_blindly": True,
        "requires_predeclared_acquisition_plan": True,
        "plan_must_distinguish_ancestor_tags_from_future_tag_exposure": True,
        "allowed_classifications": sorted(VERSION_ORIGIN_CLASSES),
    }


def classify_path_version_origin(path: str | Path) -> str:
    root = Path(path)
    return "version_origin_not_git_checkout" if not (root / ".git").exists() else "version_origin_unknown"
