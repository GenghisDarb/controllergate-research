from __future__ import annotations

import argparse, importlib, json, os, runpy, sys
from pathlib import Path


REQUIRED_MODULES=(
 "controllergate.amds.incident_outcome", "controllergate.amds.provider_orthology",
 "controllergate.core.evidence", "controllergate.execution.execution_broker",
 "controllergate.execution.local_service", "controllergate.runtime.runtime_root_attestation",
 "controllergate.topology.source_graph",
)


def main() -> int:
 parser=argparse.ArgumentParser(); parser.add_argument('--candidate',required=True); parser.add_argument('--runtime-root',required=True); parser.add_argument('--output',required=True); parser.add_argument('--provider-python')
 args=parser.parse_args(); repo=Path(__file__).resolve().parents[1]
 import controllergate
 origin=Path(controllergate.__file__).resolve()
 if repo in origin.parents: raise SystemExit('CHECKOUT_IMPORT_FORBIDDEN_EXACT')
 origins={"controllergate":str(origin)}
 for name in REQUIRED_MODULES:
  module=importlib.import_module(name); origins[name]=str(Path(module.__file__).resolve())
  if repo in Path(module.__file__).resolve().parents: raise SystemExit(f'CHECKOUT_IMPORT_FORBIDDEN_EXACT:{name}')
 out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
 (out/'installed_product_origins.json').write_text(json.dumps({'status':'PASS','origins':origins},indent=2,sort_keys=True)+'\n')
 os.environ['CONTROLLERGATE_INSTALLED_ONLY']='1'
 os.environ['CONTROLLERGATE_RUN_ID']=os.environ.get('GITHUB_RUN_ID','batch097:local')
 os.environ['CONTROLLERGATE_FRAME_ID']=os.environ.get('GITHUB_SHA','batch097:frozen-before-target')
 sys.argv=['run_batch095_candidate_lane.py','--candidate',args.candidate,'--runtime-root',args.runtime_root,'--output',args.output]
 if args.provider_python: sys.argv.extend(['--provider-python',args.provider_python])
 runpy.run_path(str(repo/'scripts/run_batch095_candidate_lane.py'),run_name='__main__')
 return 0

if __name__=='__main__': raise SystemExit(main())
