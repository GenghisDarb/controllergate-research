from __future__ import annotations

import argparse
import json

from controllergate.reactome_ir.mysql_dump import extract_core_tables
from controllergate.reactome_ir.structured import build_structured_rpir


def main() -> int:
    parser = argparse.ArgumentParser(description="Build RPIR v2 from exact Reactome release-97 structured sources.")
    parser.add_argument("--mysql-dump", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--reaction-occurrences", required=True)
    parser.add_argument("--pathway-occurrences", required=True)
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--reuse-database", action="store_true")
    args = parser.parse_args()
    if not args.reuse_database:
        extracted = extract_core_tables(args.mysql_dump, args.database)
        print(json.dumps({"extracted_tables": extracted}, sort_keys=True))
    result = build_structured_rpir(
        database=args.database,
        reaction_occurrences=args.reaction_occurrences,
        pathway_occurrences=args.pathway_occurrences,
        source_manifest=args.source_manifest,
        output=args.output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
