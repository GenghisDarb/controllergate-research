from __future__ import annotations


ALLOWED = {
    "SOURCE_OWNED_OUTPUT_DIVERGENCE", "PROVIDER_OWNED_OUTPUT_DIVERGENCE", "ENVIRONMENT_OWNED_OUTPUT_DIVERGENCE",
    "HARNESS_OWNED_OUTPUT_DIVERGENCE", "EXPECTATION_DIVERGENCE", "MIXED_DIVERGENCE", "DIVERGENCE_NOT_LOCALIZED",
}


def adjudicate_divergence(direct_frames: dict[str, list[str]], mixed_source_adjudicated: bool = False) -> dict[str, object]:
    populated = {owner for owner, frames in direct_frames.items() if frames}
    if populated == {"source"}:
        terminal = "SOURCE_OWNED_OUTPUT_DIVERGENCE"
    elif populated == {"provider"}:
        terminal = "PROVIDER_OWNED_OUTPUT_DIVERGENCE"
    elif populated == {"environment"}:
        terminal = "ENVIRONMENT_OWNED_OUTPUT_DIVERGENCE"
    elif populated == {"harness"}:
        terminal = "HARNESS_OWNED_OUTPUT_DIVERGENCE"
    elif len(populated) > 1:
        terminal = "MIXED_DIVERGENCE"
    else:
        terminal = "DIVERGENCE_NOT_LOCALIZED"
    return {
        "terminal_divergence_class": terminal,
        "patch_authorized": terminal == "SOURCE_OWNED_OUTPUT_DIVERGENCE" or (terminal == "MIXED_DIVERGENCE" and mixed_source_adjudicated),
        "direct_frames": direct_frames,
    }
