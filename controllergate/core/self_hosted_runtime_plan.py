from __future__ import annotations

from typing import Any


def self_hosted_runtime_plan(required_python: str) -> dict[str, Any]:
    return {
        "status": "PLAN_READY",
        "required_python_family": required_python,
        "plan_type": "self_hosted_runtime_required",
        "requirements": [
            "fresh workspace outside the live repository and outside OneDrive",
            "verified Python 3.7.x interpreter",
            "manual dependency lock installed exactly from reviewed lock evidence",
            "runtime provider custody record with interpreter SHA256 or package-manager evidence",
            "target replay only after provider and lock gates pass",
        ],
        "next_allowed_action": "provide_verified_python37_runtime_provider_or_self_hosted_runner",
    }

