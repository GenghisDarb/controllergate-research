from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from controllergate.evidence.provider_capsule_v4 import verify_provider_capsule_v4
def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--capsule",type=Path,required=True); a=p.parse_args(); blockers=verify_provider_capsule_v4(json.loads(a.capsule.read_text(encoding="utf-8"))); print(json.dumps({"status":"PASS" if not blockers else "BLOCK","blockers":blockers},sort_keys=True)); return 0 if not blockers else 1
if __name__=="__main__": raise SystemExit(main())
