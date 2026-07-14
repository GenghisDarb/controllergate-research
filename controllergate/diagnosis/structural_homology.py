from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def compare(left: dict[str, object], right: dict[str, object]) -> dict[str, object]:
    shared = sorted(set(left.get("motifs", [])) & set(right.get("motifs", [])))
    return {"shared_motifs": shared, "structural_hint_only": True, "patch_content_allowed": False,
            "comparison_hash": stable_hash({"left": left, "right": right, "shared": shared})}
