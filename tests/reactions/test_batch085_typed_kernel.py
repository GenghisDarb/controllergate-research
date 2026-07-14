from __future__ import annotations

import pytest

from controllergate.reactions.token_kernel import ReactionToken, require_tokens
from controllergate.runtime.maintenance_dispatcher import dispatch_typed_stage


def token(kind="CANDIDATE_IDENTITY_VERIFIED_TOKEN"):
    return ReactionToken.mint(token_type=kind, candidate_id="candidate", run_id="run", producer_event="event", input_tokens=(), payload={"ok": True}, independent_verifier="test")


def test_token_is_hashed_and_required():
    value = token()
    assert len(value.token_hash) == 64
    require_tokens((value,), (value.token_type,), candidate_id="candidate", run_id="run")


def test_missing_token_blocks():
    with pytest.raises(ValueError, match="missing"):
        require_tokens((token(),), ("SOURCE_ACQUIRED_TOKEN",), candidate_id="candidate", run_id="run")


def test_failed_reaction_cannot_mint():
    with pytest.raises(ValueError, match="failed reaction"):
        ReactionToken.mint(token_type="SOURCE_ACQUIRED_TOKEN", candidate_id="candidate", run_id="run", producer_event="event", input_tokens=(), payload={}, independent_verifier="test", reaction_status="BLOCK")


def test_duplicate_token_cycle_rejected():
    value = token()
    with pytest.raises(ValueError, match="cycle"):
        require_tokens((value, value), (value.token_type,), candidate_id="candidate", run_id="run")


def test_dispatcher_consumes_tokens_not_manifest_pass_fields():
    source = token("SOURCE_ACQUIRED_TOKEN")
    provider = dispatch_typed_stage(stage="provider_execution_ready", candidate_id="candidate", run_id="run", input_tokens=[source], output_token_type="PROVIDER_EXECUTION_READY_TOKEN", payload={"seal": "x"}, reaction_status="PASS", independent_verifier="test")
    assert provider.input_token_hashes == (source.token_hash,)
    with pytest.raises(ValueError, match="missing"):
        dispatch_typed_stage(stage="target_verified", candidate_id="candidate", run_id="run", input_tokens=[], output_token_type="TARGET_OR_REPRODUCER_VERIFIED_TOKEN", payload={}, reaction_status="PASS", independent_verifier="test")
