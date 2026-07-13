from __future__ import annotations

from pathlib import Path
from typing import Any


def provider_artifact_handoff(provider_root: Path, main_evidence_root: Path) -> dict[str, Any]:
    separated = provider_root.resolve() != main_evidence_root.resolve() and main_evidence_root.resolve() not in provider_root.resolve().parents
    return {"status": "PASS" if separated else "BLOCK", "provider_root": str(provider_root), "main_evidence_root": str(main_evidence_root), "separate_artifact_required": True, "provider_bytes_in_main_artifact": False}
