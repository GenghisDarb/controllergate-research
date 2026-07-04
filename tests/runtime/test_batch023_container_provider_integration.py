import json
from pathlib import Path


def test_batch023_container_provider_integration_boundary():
    state = json.loads(Path("outputs/clean_replication_batch_023/consolidated_state_clean_replication_batch_023.json").read_text(encoding="utf-8"))
    assert state["selected_provider"] in {"self_hosted_runtime_plan", "docker_run_provider"}
    assert state["full_scoring"] == "NOT_RUN/disallowed"
    assert state["self_maintaining_software"] == "false/not_demonstrated"
    assert state["target_intent_alignment_status"] in {"NOT_RUN", "BLOCK"}
