from __future__ import annotations


def build_branch_goal(evidence: dict) -> dict:
    checks={"wheel_produced":bool(evidence.get("wheel_produced")),"wheel_identity_verified":evidence.get("wheel_identity_verified") is True,"wheel_metadata_verified":evidence.get("wheel_metadata_verified") is True,"wheel_tags_compatible":evidence.get("wheel_tags_compatible") is True,"record_verified":evidence.get("record_verified") is True,"fresh_runtime_install_pass":evidence.get("fresh_runtime_install_pass") is True,"minimal_import_pass":evidence.get("minimal_import_pass") is True,"required_providers_resolved":not evidence.get("unresolved_required_providers")}
    return {"status":"PASS" if all(checks.values()) else "BLOCK","checks":checks,"goal_passed":all(checks.values())}
