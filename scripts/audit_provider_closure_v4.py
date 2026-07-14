from __future__ import annotations

import argparse,json
from pathlib import Path


def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args();o=Path(a.out);errors=[];records=[]
 for name in ("openbb","poetry"):
  path=o/f"batch083_{name}_provider_v4_result.json"
  if not path.is_file():errors.append(f"missing:{name}");continue
  row=json.loads(path.read_text(encoding="utf-8"));records.append(row)
  if row.get("provider_execution_ready") and (row["dependency_graph"].get("missing_runtime_dependencies") or len(row.get("offline_installs",[]))!=2):errors.append(f"false_ready:{name}")
 print(json.dumps({"status":"PASS" if not errors else "FAIL","records":len(records),"errors":errors},sort_keys=True));return 0 if not errors else 1
if __name__=="__main__":raise SystemExit(main())
