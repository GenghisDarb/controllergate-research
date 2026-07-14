from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from controllergate.batch083.orchestrator import candidate_adjudication, conditional_stage, connectors, finalize, historical, network, openapi, prepare, product, provider, reproduce, verify_prior_artifacts


def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("stage"); p.add_argument("--out",required=True); p.add_argument("--runtime",required=True); p.add_argument("--store"); p.add_argument("--verified"); p.add_argument("--provider-payload"); p.add_argument("--input-payload"); args=p.parse_args()
    out=Path(args.out); runtime=Path(args.runtime); out.mkdir(parents=True,exist_ok=True); runtime.mkdir(parents=True,exist_ok=True)
    if str(runtime.resolve()).upper().startswith("E:\\"): raise SystemExit("E runtime prohibited")
    if args.stage=="prepare": prepare(out,runtime)
    elif args.stage=="artifacts": verify_prior_artifacts(Path(args.store),Path(args.verified),out)
    elif args.stage in {"provider-openbb","provider-poetry"}: provider(args.stage.split("-")[1],Path(args.verified),out,runtime)
    elif args.stage in {"reproduce-openbb","reproduce-poetry"}: reproduce(args.stage.split("-")[1],Path(args.provider_payload),out,runtime,Path(args.input_payload) if args.input_payload else None)
    elif args.stage=="openapi": openapi(Path(args.verified),out,runtime)
    elif args.stage=="historical": historical(out,runtime)
    elif args.stage=="network": network(out)
    elif args.stage=="candidate": candidate_adjudication(out)
    elif args.stage in {"diagnostic","matched-nulls","ground-truth","authorization","repair","count"}: conditional_stage(out,args.stage)
    elif args.stage=="connectors": connectors(out)
    elif args.stage=="public-connector": connectors(out,public=True)
    elif args.stage=="product": product(out,runtime)
    elif args.stage=="finalize": finalize(out,runtime)
    else: raise SystemExit(f"unknown stage: {args.stage}")
    return 0


if __name__=="__main__": raise SystemExit(main())
