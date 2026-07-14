from __future__ import annotations


def propose(*_args, enabled: bool = False, credentials_configured: bool = False, **_kwargs):
    if not enabled or not credentials_configured:
        return {"status": "BLOCK", "blocker": "external_agent_adapter_disabled"}
    return {"status": "BLOCK", "blocker": "external_agent_adapter_not_implemented"}
