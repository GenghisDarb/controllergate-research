from __future__ import annotations

import json
from pathlib import Path

from controllergate.evidence.contracts import load_contracts, seal_contracts


root = Path(__file__).resolve().parents[2]
contracts = load_contracts(root / "configs" / "candidate_execution_contracts_v2.jsonl")
sealed = seal_contracts(contracts)
print(json.dumps({"status": sealed["status"], "candidate_count": len(contracts), "bundle_hash": sealed["bundle_hash"], "read_only": True}, sort_keys=True))
