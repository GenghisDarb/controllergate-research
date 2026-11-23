"""Create a local pre-outcome hash freeze; no independent timestamp claim."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    if (ROOT / "FROZEN_DESIGN.json").exists() or (ROOT / "results.json").exists() or (ROOT / "legacy_witnesses.json").exists():
        raise SystemExit("Refusing to replace a freeze or freeze after an outcome file exists")
    paths = list(ROOT.glob("*.py")) + list((ROOT / "source_snapshot").rglob("*.py"))
    paths += [ROOT / name for name in ("experiment_spec.json", "token_contract.json", "reactome_event_contract.source.json", "DESIGN_PENDING_SOURCE.md")]
    frozen = {"schema": "local_preoutcome_freeze.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Local execution-order receipt. Not a trusted timestamp, preregistration service, or scientific-validity guarantee.",
              "files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
    (ROOT / "FROZEN_DESIGN.json").write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"files": len(paths), "sha256": hashlib.sha256((ROOT / "FROZEN_DESIGN.json").read_bytes()).hexdigest()}))
