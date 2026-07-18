from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


KINDS = {
    "contact_edge",
    "boundary_dimension",
    "projection_pair",
    "harness_variation",
    "runner_variation",
    "provider_variation",
    "service_variation",
    "expectation_relation",
    "modality_conflict",
    "recovery_region",
}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def inspect_subject(kind: str, subject: str, source_root: Path | None) -> dict[str, object]:
    if kind not in KINDS:
        raise ValueError(f"unsupported probe kind: {kind}")
    result: dict[str, object] = {
        "kind": kind,
        "subject": subject,
        "subject_hash": _hash([kind, subject]),
        "diagnosis_label_present": False,
    }
    if source_root is not None and source_root.is_dir() and kind in {"contact_edge", "recovery_region"}:
        parsed: list[dict[str, object]] = []
        for path in sorted(source_root.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            names = sorted(
                node.name for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            )
            if names:
                parsed.append({"path": path.relative_to(source_root).as_posix(), "symbols": names})
        result["source_contacts"] = parsed
        result["source_contact_count"] = sum(len(row["symbols"]) for row in parsed)
    elif kind == "boundary_dimension":
        result["boundary_value_present"] = bool(subject.strip())
    elif kind == "projection_pair":
        sides = subject.split("|", 1)
        result["side_count"] = len(sides)
        result["sides_distinct"] = len(sides) == 2 and sides[0] != sides[1]
    elif kind.endswith("variation"):
        result["variation_identity"] = _hash([kind, subject, "bounded-variation"])
    elif kind == "expectation_relation":
        result["expectation_identity"] = _hash([subject, "expectation"])
    elif kind == "modality_conflict":
        result["modalities"] = sorted(set(part for part in subject.split("|") if part))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True, choices=sorted(KINDS))
    parser.add_argument("--subject", required=True)
    parser.add_argument("--source-root")
    args = parser.parse_args(argv)
    value = inspect_subject(args.kind, args.subject, Path(args.source_root) if args.source_root else None)
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
