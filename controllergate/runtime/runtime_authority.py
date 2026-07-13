from __future__ import annotations


AUTHORITY_ORDER = ("issue_evidence", "ci_log", "ci_matrix", "tox_nox", "requires_python", "classifiers", "documentation")
WEAK_SOURCES = {"commit_date", "latest_runtime", "host_default"}


def runtime_authorized(source: str) -> bool:
    return source in AUTHORITY_ORDER
