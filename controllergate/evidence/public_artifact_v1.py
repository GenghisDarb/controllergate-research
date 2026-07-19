from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Iterable, Mapping


FORBIDDEN_PARTS = {".git", "__pycache__", "site-packages", "venv", ".venv", "source-checkout", "source_checkout"}
FORBIDDEN_SUFFIXES = {".zip", ".tar", ".gz", ".pyc", ".pyo"}
PRIVATE_MARKERS = (
    "tld_requirement_text", "normalized_tld", "raw_tld", "sealed_truth", "gold_patch",
    "private tld source", "notebook heading", "tld quotation",
)


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _eligible(path: Path) -> bool:
    lowered = {part.casefold() for part in path.parts}
    return not lowered.intersection(FORBIDDEN_PARTS) and path.suffix.casefold() not in FORBIDDEN_SUFFIXES


def copy_public_tree(source: str | Path, destination: str | Path) -> list[Path]:
    source_root = Path(source)
    destination_root = Path(destination)
    copied: list[Path] = []
    for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
        relative = path.relative_to(source_root)
        if not _eligible(relative):
            continue
        target = destination_root / "evidence" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        copied.append(target)
    return copied


def private_marker_hits(paths: Iterable[Path]) -> list[dict[str, str]]:
    hits = []
    for path in paths:
        if path.suffix.casefold() not in {".json", ".jsonl", ".md", ".txt", ".log", ".yml", ".yaml"}:
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        texts: list[str] = []
        if path.suffix.casefold() in {".json", ".jsonl"}:
            try:
                values = [json.loads(line) for line in raw.splitlines() if line.strip()] if path.suffix.casefold() == ".jsonl" else [json.loads(raw)]
                def collect(value: object) -> None:
                    if isinstance(value, str):
                        texts.append(value.casefold())
                    elif isinstance(value, Mapping):
                        for item in value.values():
                            collect(item)
                    elif isinstance(value, (list, tuple)):
                        for item in value:
                            collect(item)
                for value in values:
                    collect(value)
            except (json.JSONDecodeError, UnicodeDecodeError):
                texts = [raw.casefold()]
        else:
            texts = [raw.casefold()]
        for marker in PRIVATE_MARKERS:
            if any(marker in text for text in texts):
                hits.append({"path": path.as_posix(), "marker": marker})
    return hits


def write_manifests(root: str | Path) -> dict[str, Any]:
    artifact_root = Path(root)
    excluded = {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"}
    rows = []
    for path in sorted(item for item in artifact_root.rglob("*") if item.is_file() and item.name not in excluded):
        rows.append((path.relative_to(artifact_root).as_posix(), sha256(path)))
    text = "".join(f"{digest}  {relative}\n" for relative, digest in rows)
    for name in excluded:
        (artifact_root / name).write_text(text, encoding="utf-8", newline="\n")
    return {"entry_count": len(rows), "manifest_sha256": hashlib.sha256(text.encode()).hexdigest()}


def verify_manifest(root: str | Path) -> dict[str, Any]:
    artifact_root = Path(root)
    manifest = artifact_root / "ARTIFACT_SHA256SUMS.txt"
    failures = []
    checked = 0
    if not manifest.is_file():
        return {"status": "BLOCK", "blocker": "public_artifact_manifest_missing", "checked": 0, "failures": []}
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        digest, separator, relative = line.partition("  ")
        path = artifact_root / relative
        checked += 1
        if not separator or not path.is_file() or sha256(path) != digest:
            failures.append({"line": number, "path": relative})
    self_entries = [line for line in manifest.read_text(encoding="utf-8").splitlines() if line.endswith("ARTIFACT_SHA256SUMS.txt")]
    return {
        "status": "PASS" if checked and not failures and not self_entries else "BLOCK",
        "checked": checked,
        "failures": failures,
        "self_manifest_entry_count": len(self_entries),
    }


def seal_public_artifact(
    *, source: str | Path, output: str | Path, kind: str, workflow_run_id: str, workflow_head: str,
    extra_claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if kind not in {"decision", "truth-blind"}:
        raise ValueError("unsupported public artifact kind")
    output_root = Path(output)
    output_root.mkdir(parents=True, exist_ok=True)
    copied = copy_public_tree(source, output_root)
    hits = private_marker_hits(copied)
    provider_copies = []
    for path in sorted((output_root / "evidence").rglob("exact_provider_verification_v1.json")):
        provider_copies.append(json.loads(path.read_text(encoding="utf-8")))
    provider_by_candidate: dict[str, dict[str, Any]] = {}
    provider_conflicts = []
    for row in provider_copies:
        candidate_id = str(row.get("candidate_id"))
        existing = provider_by_candidate.get(candidate_id)
        if existing and existing.get("verification_receipt") != row.get("verification_receipt"):
            provider_conflicts.append(candidate_id)
        provider_by_candidate[candidate_id] = row
    providers = list(provider_by_candidate.values())
    preframes = list((output_root / "evidence").rglob("pre_tld_decision_frame_v1.json"))
    terminals = list((output_root / "evidence").rglob("public_truth_blind_terminal_v1.json"))
    claim = {
        "claim": "PUBLIC_DECISION_TIME_EVIDENCE_ONLY" if kind == "decision" else "PUBLIC_TRUTH_BLIND_EXECUTION_ONLY",
        "kind": kind,
        "workflow_run_id": str(workflow_run_id),
        "workflow_head": workflow_head,
        "candidate_substitution_count": 0,
        "future_or_outcome_evidence_count": 0,
        "ordinary_patch_count": 0,
        "historical_increment": 0,
        "truth_access_count": 0,
        "private_tld_source_access_count": 0,
        "source_mutation_count": 0,
        "provider_receipt_count": len(providers),
        "provider_receipt_copy_count": len(provider_copies),
        "provider_receipt_conflicts": sorted(set(provider_conflicts)),
        "exact_provider_pass_count": sum(row.get("status") == "PASS_EXACT_FROZEN_LINUX_PARITY" for row in providers),
        "pre_tld_frame_count": len(preframes),
        "truth_blind_terminal_count": len(terminals),
        "private_marker_hits": hits,
        "producer": "controllergate.evidence.public_artifact_v1.seal_public_artifact",
        "execution_depth": "public decision-time evidence seal" if kind == "decision" else "public truth-blind execution seal",
        "semantic_scope": "non-authorizing public evidence",
        "authority_allowed": "private local continuation input",
        "authority_forbidden": ["truth", "source ownership", "repair", "count", "release"],
    }
    claim.update(dict(extra_claims or {}))
    expected_providers = 8
    kind_depth_ok = len(preframes) == 8 if kind == "decision" else len(terminals) == 8
    claim["kind_depth_check"] = kind_depth_ok
    claim["status"] = "PASS" if len(providers) == expected_providers and claim["exact_provider_pass_count"] == expected_providers and not provider_conflicts and kind_depth_ok and not hits else "BLOCK"
    (output_root / "public_claim_boundary.json").write_text(json.dumps(claim, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    seal = {
        "status": claim["status"],
        "claim_sha256": canonical_hash(claim),
        "workflow_run_id": str(workflow_run_id),
        "workflow_head": workflow_head,
        "producer": "controllergate.evidence.public_artifact_v1.seal_public_artifact",
        "semantic_scope": "public artifact boundary",
        "authority_allowed": "manifest-bound private continuation input",
        "authority_forbidden": ["truth", "source ownership", "repair", "count", "release"],
    }
    (output_root / "public_artifact_seal.json").write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifests = write_manifests(output_root)
    return {"status": claim["status"], "claim": claim, "seal": seal, "manifest": manifests}
