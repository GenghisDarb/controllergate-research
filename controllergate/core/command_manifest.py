from __future__ import annotations

import hashlib
import json


def target_command_manifest_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "manifest_required_before_replay": True,
        "hidden_framework_state_allowed": False,
        "bugsinpy_command_maps_allowed": False,
        "required_fields": ["command", "cwd", "environment", "provenance_basis", "allowed_setup_commands"],
        "blockers": [
            "target_command_manifest_missing",
            "target_command_manifest_malformed",
            "target_command_manifest_untrusted",
            "target_command_manifest_forbidden_framework_state",
        ],
    }


def manifest_sha256(manifest: dict[str, object]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_target_command_manifest_summary(
    *,
    seed_present: bool,
    command: list[str] | None = None,
    cwd: str | None = None,
    environment: dict[str, str] | None = None,
    provenance_basis: str | None = None,
    allowed_setup_commands: list[str] | None = None,
) -> dict[str, object]:
    if not seed_present:
        return {
            "status": "PASS",
            "target_command_manifest_status": "READY_NO_SEED",
            "target_command_manifest_sha256": None,
            "command": None,
            "cwd": None,
            "environment": {},
            "provenance_basis": "seed_required_before_candidate_manifest",
            "allowed_setup_commands": [],
            "target_replay_allowed": False,
            "blocker": None,
        }
    manifest = {
        "command": command,
        "cwd": cwd,
        "environment": environment or {},
        "provenance_basis": provenance_basis,
        "allowed_setup_commands": allowed_setup_commands or [],
    }
    malformed = not command or not cwd or not provenance_basis
    return {
        "status": "BLOCK" if malformed else "PASS",
        "target_command_manifest_status": "MALFORMED" if malformed else "PASS",
        "target_command_manifest_sha256": manifest_sha256(manifest) if not malformed else None,
        **manifest,
        "target_replay_allowed": not malformed,
        "blocker": "target_command_manifest_malformed" if malformed else None,
    }


def target_replay_allowed(command_manifest: dict[str, object]) -> bool:
    return command_manifest.get("status") == "PASS" and command_manifest.get("target_replay_allowed") is True
