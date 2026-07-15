from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path

from controllergate.reactome_ir.ingest import ingest_release


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest the frozen Reactome release 97 documentary source boundary.")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--glossary", required=True)
    parser.add_argument("--chapter-config", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    database = Path(args.database)
    if database.exists():
        os.chmod(database, stat.S_IWRITE | stat.S_IREAD)
        database.unlink()
    result = ingest_release(
        source_root=args.source_root,
        glossary=args.glossary,
        chapter_config=args.chapter_config,
        database=database,
        output=args.output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
