from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];REGISTRY=ROOT/'configs/batch084_historical_episode_registry.json'
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,v:object)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--manifest-output',required=True);a=ap.parse_args();runtime=Path(a.runtime);runtime.mkdir(parents=True,exist_ok=True);registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
 truth=[{'candidate_id':x['candidate_id'],'terminal':x['terminal_class'],'episode_kind':x['episode_kind'],'truth_provenance':str(REGISTRY.relative_to(ROOT)).replace('\\','/')} for x in registry['episodes']];capsule=runtime/'batch097_amds_sealed_truth.json';dump(capsule,truth)
 dump(Path(a.manifest_output),{'status':'PASS','truth_capsule_path':str(capsule),'truth_capsule_sha256':sha(capsule),'truth_registry_sha256':sha(REGISTRY),'episode_count':len(truth),'builder_access':False,'available_only_after_terminal_commitment':True,'authority_allowed':'post-terminal retrospective quality join','authority_forbidden':['probe planning','terminal writing','repair','count']});return 0
if __name__=='__main__':raise SystemExit(main())
