from __future__ import annotations

CURRENT_PROTOCOL = "v2.19"
CURRENT_PATHWAY = "authorized_amds_active_maintenance_lane"


def current_pathway() -> dict[str, str]:
    return {"protocol": CURRENT_PROTOCOL, "pathway": CURRENT_PATHWAY}
