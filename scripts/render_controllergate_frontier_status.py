from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import write_text_lf

STATE = ROOT / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
TARGET = ROOT / "docs" / "CURRENT_FRONTIER_STATUS.md"


def render(state: dict[str, object]) -> str:
    return "\n".join([
        "# ControllerGate Frontier Status", "",
        "This file is generated from `outputs/frontier/CURRENT_FRONTIER_STATE.json`.", "",
        f"- Validated current protocol: {state['validated_current_protocol']} ({state['validated_current_protocol_status']})",
        f"- Frontier engine: {state['frontier_engine_status']}",
        f"- Frontier protocol promoted: {str(state['frontier_engine_protocol_promoted']).lower()}",
        f"- Tier-2 candidates: {state['tier2_candidate_count']}",
        f"- Tier-3 static probe authorizations: {state['tier3_candidate_count']}",
        f"- Issue-derived repair episodes: {state['issue_derived_repair_count']}",
        f"- Native external repair episodes: {state['native_external_repair_count']}",
        f"- Runtime activation allowed: {str(state['runtime_wrapper_activation_allowed']).lower()}",
        f"- Full scoring: {state['full_scoring']}",
        f"- Memory lift: {state['memory_lift']}",
        f"- Self-maintaining software: {state['self_maintaining_software']}",
        f"- Next safe action: {state['next_safe_action']}",
    ])


def main() -> int:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    write_text_lf(TARGET, render(state))
    print(TARGET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
