from controllergate.governance.builder_critic_gate import REQUIRED_COORDINATES, builder_critic_agreement


def test_builder_critic_agreement():
    record = {key: "same" for key in REQUIRED_COORDINATES}
    assert builder_critic_agreement(record, dict(record))["status"] == "PASS"


def test_builder_critic_disagreement_blocks():
    builder = {key: "same" for key in REQUIRED_COORDINATES}
    critic = dict(builder); critic["workflow_head"] = "different"
    assert builder_critic_agreement(builder, critic)["status"] == "CRITIC_VERIFICATION_DISAGREES_BUILDER_OUTPUT"
