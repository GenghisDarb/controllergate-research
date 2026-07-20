from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
FORBIDDEN={".zip",".tar",".gz",".pyc",".pyd",".so",".dll"}
MANIFESTS={"ARTIFACT_SHA256SUMS.txt","PORTABLE_ARTIFACT_SHA256SUMS.txt","SHA256SUMS.txt"}

def rows(root:Path,excluded:set[str])->list[str]:
 return [f"{hashlib.sha256(x.read_bytes()).hexdigest()}  {x.relative_to(root).as_posix()}" for x in sorted(root.rglob("*")) if x.is_file() and x.relative_to(root).as_posix() not in excluded]

def write_manifests(root:Path)->dict[str,int]:
 artifact_rows=rows(root,MANIFESTS)
 for name in ["ARTIFACT_SHA256SUMS.txt","PORTABLE_ARTIFACT_SHA256SUMS.txt"]:
  (root/name).write_text("\n".join(artifact_rows)+"\n",encoding="utf-8",newline="\n")
 portable_rows=rows(root,{"SHA256SUMS.txt"})
 (root/"SHA256SUMS.txt").write_text("\n".join(portable_rows)+"\n",encoding="utf-8",newline="\n")
 return {"artifact":len(artifact_rows),"portable":len(artifact_rows),"sha256sums":len(portable_rows)}

def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--destination",type=Path,required=True);p.add_argument("--write-source-manifests",action="store_true");a=p.parse_args();
 if a.write_source_manifests:write_manifests(a.source)
 shutil.rmtree(a.destination,ignore_errors=True);shutil.copytree(a.source,a.destination,ignore=shutil.ignore_patterns("__pycache__","*.pyc","*.pyd"));bad=[x for x in a.destination.rglob("*") if x.is_file() and x.suffix.lower() in FORBIDDEN]
 if bad:raise SystemExit("forbidden artifact payload: "+str(bad[0]))
 counts=write_manifests(a.destination)
 print(json.dumps({"status":"PASS","manifest_counts":counts,"manifest_self_entries":0},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
