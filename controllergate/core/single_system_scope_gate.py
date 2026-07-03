from __future__ import annotations

from typing import Any


def single_system_scope_gate_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "single_system_source_geometry_scope": "one_candidate_one_repo_one_execution_trace",
        "may_use_without_interlock_invariants": True,
        "must_not_conflate_with_coupled_extension": True,
    }


def audit_single_system_scope(*, candidate_count: int, repo_count: int, trace_count: int) -> dict[str, Any]:
    single = candidate_count == 1 and repo_count == 1 and trace_count == 1
    return {
        "status": "PASS" if single else "BLOCK",
        "scope": "single_system" if single else "coupled_or_multi_system",
        "candidate_count": candidate_count,
        "repo_count": repo_count,
        "trace_count": trace_count,
        "coupled_interlock_extension_active": False,
        "blocker": None if single else "single_system_interlock_conflation",
    }
