from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.governance.builder_critic_gate import builder_critic_agreement


def main() -> int:
    path = Path("outputs/post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot/batch081_builder_critic_agreement.json")
    if not path.is_file():
        print("builder/critic agreement: PENDING")
        return 1
    value = json.loads(path.read_text(encoding="utf-8"))
    result = builder_critic_agreement(value["builder"], value["critic"])
    print("builder/critic agreement:", result["status"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
