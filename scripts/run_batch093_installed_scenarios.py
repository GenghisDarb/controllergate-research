from __future__ import annotations

import argparse
import json
from pathlib import Path

from controllergate.isomorphism.runtime import execute_structured_scenario


def _load(path: Path) -> list[dict[str, object]]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [json.loads(path.read_text(encoding="utf-8"))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", required=True)
    parser.add_argument("--integrated", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    scenarios = [*_load(Path(args.scenarios)), *_load(Path(args.integrated))]
    results = [execute_structured_scenario(scenario, args.database, platform=args.platform) for scenario in scenarios]
    target = Path(args.output); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in results), encoding="utf-8", newline="\n")
    print(json.dumps({"platform": args.platform, "scenario_count": len(results), "pass_count": sum(row["status"] == "PASS" for row in results), "database": args.database}, sort_keys=True))
    return 0 if results and all(row["status"] == "PASS" for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
