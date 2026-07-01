from controllergate.core.gate_chain import audit_gate_dependency, batch013_gate_chain_policy, gate_entry


def test_batch013_gate_chain_blocks_downstream_after_seed_gate():
    policy = batch013_gate_chain_policy()
    entries = [
        gate_entry(index=index, gate_id=gate_id, status="PASS", inputs={}, outputs={})
        for index, gate_id in enumerate(policy["gate_order"][:4], start=1)
    ]
    entries.append(gate_entry(index=5, gate_id=policy["gate_order"][4], status="BLOCK", inputs={}, outputs={}, blocker=policy["blocker_if_seed_missing"]))
    for index, gate_id in enumerate(policy["gate_order"][5:], start=6):
        entries.append(gate_entry(index=index, gate_id=gate_id, status="NOT_RUN", inputs={}, outputs={}, blocked_by_gate=policy["gate_order"][4]))

    assert audit_gate_dependency(entries)["status"] == "PASS"
