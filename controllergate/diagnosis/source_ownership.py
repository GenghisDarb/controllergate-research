from __future__ import annotations

from pathlib import Path


def classify_frames(frames: list[dict[str, object]], source_root: Path) -> dict[str, object]:
    root = str(source_root.resolve())
    rows = [{**frame, "owner": "candidate_source" if str(Path(str(frame["path"])).resolve()).startswith(root) else "provider_or_harness"}
            for frame in frames]
    owned = [row for row in rows if row["owner"] == "candidate_source"]
    return {"status": "PASS" if owned else "BLOCK", "frames": rows, "direct_source_ownership": bool(owned)}
