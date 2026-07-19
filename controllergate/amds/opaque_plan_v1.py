from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


ARMS = tuple("ABCDEFGHIJ")
AUTHORITY_FORBIDDEN = ("causal fact", "terminal", "truth", "source ownership", "repair", "count", "release")


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compile_opaque_plans(
    frames: Iterable[Mapping[str, Any]], *, bundle_sha256: str, requirement_registry_sha256: str,
    created_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    created = created_at_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    rows: list[dict[str, Any]] = []
    for frame in sorted(frames, key=lambda row: str(row["candidate_id"])):
        if frame.get("tld_join_state") != "PENDING_PRIVATE_DIRECT_SOURCE_JOIN":
            raise ValueError("opaque plans require verified pre-TLD frames")
        probes = list(frame.get("legal_probes", ()))
        probe_ids = [str(row["probe_id"]) for row in probes]
        if not probe_ids:
            raise ValueError(f"pre-TLD frame has no legal probes: {frame['candidate_id']}")
        for arm_id in ARMS:
            if arm_id in {"E", "F"}:
                ordered = sorted(
                    probe_ids,
                    key=lambda value: canonical_hash(
                        [bundle_sha256, requirement_registry_sha256, frame["candidate_id"], arm_id, value]
                    ),
                )
            else:
                ordered = sorted(probe_ids)
            plan: dict[str, Any] = {
                "plan_id": "opaque-plan:" + canonical_hash([frame["candidate_id"], arm_id, ordered])[:32],
                "candidate_id": frame["candidate_id"],
                "pre_tld_frame_hash": frame["pre_tld_frame_hash"],
                "arm_id": arm_id,
                "ordered_opaque_probe_ids": ordered,
                "budget": frame["budgets"],
                "planner_identity": "controllergate.amds.opaque_plan_v1.compile_opaque_plans",
                "tld_bundle_identity_hash": bundle_sha256,
                "tld_requirement_registry_hash": requirement_registry_sha256,
                "created_at_utc": created,
                "creation_before_execution_assertion": True,
                "authority_allowed": "ordering of already legal public probes and nonauthorizing metrology warnings",
                "authority_forbidden": list(AUTHORITY_FORBIDDEN),
            }
            plan["plan_hash"] = canonical_hash(plan)
            rows.append(plan)
    if len(rows) != 80:
        raise ValueError("opaque plan cohort must contain eight candidates and ten arms")
    return rows


def verify_opaque_plans(plans: Iterable[Mapping[str, Any]], frames: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(plans)
    frame_by_candidate = {str(row["candidate_id"]): row for row in frames}
    failures = []
    for row in rows:
        unsigned = {key: value for key, value in row.items() if key != "plan_hash"}
        frame = frame_by_candidate.get(str(row.get("candidate_id")))
        legal = {str(item["probe_id"]) for item in frame.get("legal_probes", ())} if frame else set()
        ordered = list(row.get("ordered_opaque_probe_ids", ()))
        checks = {
            "hash": row.get("plan_hash") == canonical_hash(unsigned),
            "frame": bool(frame) and row.get("pre_tld_frame_hash") == frame.get("pre_tld_frame_hash"),
            "only_legal_probes": bool(ordered) and set(ordered) == legal and len(ordered) == len(set(ordered)),
            "creation_before_execution": row.get("creation_before_execution_assertion") is True,
            "forbidden_authority": set(row.get("authority_forbidden", ())) == set(AUTHORITY_FORBIDDEN),
        }
        if not all(checks.values()):
            failures.append({"plan_id": row.get("plan_id"), "checks": checks})
    candidate_arm_pairs = {(row.get("candidate_id"), row.get("arm_id")) for row in rows}
    return {
        "status": "PASS" if len(rows) == 80 and len(candidate_arm_pairs) == 80 and not failures else "BLOCK",
        "plan_count": len(rows),
        "candidate_arm_pair_count": len(candidate_arm_pairs),
        "failures": failures,
    }
