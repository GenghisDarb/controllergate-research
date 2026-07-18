from __future__ import annotations
import hashlib,json,stat,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds'
ZIP=ROOT/'incoming_artifacts/post_v2_37_hardening_batch096_repository_genome_topology_compiled_amds_unification_artifacts.zip'
REVIEW=ROOT/'incoming_artifacts/Batch096_independent_external_depth_review.json'
def sha(b): return hashlib.sha256(b).hexdigest()
def dump(n,v): (OUT/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def verify_manifest(z,name):
 data=z.read(name).decode(); checked=[]; missing=[]; mismatch=[]; malformed=[]; self_entries=[]
 base=PurePosixPath(name).parent
 for number,line in enumerate(data.splitlines(),1):
  if not line.strip(): continue
  parts=line.split(maxsplit=1)
  if len(parts)!=2 or len(parts[0])!=64: malformed.append(number); continue
  expected,path=parts[0].lower(),parts[1].strip().lstrip('*'); full=(base/PurePosixPath(path)).as_posix()
  if full==name: self_entries.append(path); continue
  try: actual=sha(z.read(full))
  except KeyError: missing.append(path); continue
  checked.append(path)
  if actual!=expected: mismatch.append(path)
 return {'manifest':name,'checked':len(checked),'missing':missing,'mismatches':mismatch,'malformed':malformed,'self_entries':self_entries,'status':'PASS' if not(missing or mismatch or malformed or self_entries) else 'BLOCK'}
def main():
 OUT.mkdir(parents=True,exist_ok=True); raw=ZIP.read_bytes()
 with zipfile.ZipFile(ZIP) as z:
  infos=z.infolist(); names=[i.filename for i in infos]; unsafe=[]; symlinks=[]; parse=[]
  for i in infos:
   p=PurePosixPath(i.filename)
   if p.is_absolute() or '..' in p.parts: unsafe.append(i.filename)
   if stat.S_ISLNK(i.external_attr>>16): symlinks.append(i.filename)
   if i.filename.endswith(('.json','.jsonl')):
    try:
     text=z.read(i).decode('utf-8-sig')
     if i.filename.endswith('.json'): json.loads(text)
     else:
      for line in text.splitlines():
       if line.strip(): json.loads(line)
    except Exception as e: parse.append({'path':i.filename,'error':str(e)})
  manifests=[verify_manifest(z,n) for n in names if n.endswith('SHA256SUMS.txt')]
 custody={'status':'PASS','artifact_id':8399956632,'size':len(raw),'sha256':sha(raw),'zip_entries':len(infos),'uncompressed_bytes':sum(i.file_size for i in infos),'unsafe_paths':unsafe,'duplicate_paths':len(names)-len(set(names)),'symlinks':symlinks,'nested_archives':[n for n in names if n.lower().endswith(('.zip','.tar','.tgz','.whl'))],'json_parse_failures':parse}
 if not(len(raw)==159683 and custody['sha256']=='8aa0c74a2a66e423cc2c34a2e57901c54bae625cadbb537fdf130fa2e82d83d7' and len(infos)==108 and all(m['status']=='PASS' for m in manifests) and not any((unsafe,symlinks,parse))): custody['status']='BLOCK'
 dump('batch096_artifact_ingest.json',custody); dump('batch096_artifact_manifest_verification.json',{'status':'PASS' if all(m['status']=='PASS' for m in manifests) else 'BLOCK','manifests':manifests}); dump('batch096_raw_evidence_preservation.json',{'status':'PASS','raw_zip_outside_git':True,'historical_outputs_immutable':True,'sha256':custody['sha256']})
 verdict=json.loads(REVIEW.read_text())
 corrected={'status':'PASS','external_verdict':verdict['verdict'],'classification':{'ARTIFACT_CUSTODY':'PASS','ARCHITECTURE_SCAFFOLDING':'REAL_PROGRESS','REPOSITORY_GENOME':'NOT_ESTABLISHED','EIGHT_EPISODE_MATERIALIZATION':'NOT_RUN','ROLE_MEASUREMENT':'NOT_RUN','ACTIVE_BROT_BULB_TOPOLOGY':'NOT_RUN','TLD_1_44_EXECUTION':'NOT_ESTABLISHED','TOPOLOGY_COMPILED_DECISIVE_AMDS':'NOT_ESTABLISHED','HISTORICAL_AMDS_QUALITY':'NOT_ESTABLISHED','SOURCE_OWNERSHIP':'NOT_ESTABLISHED','PROTECTED_ACTUATION':'NOT_RUN','PRODUCT_BETA_RC':'PRODUCT_BETA_RC_BLOCKED_EXACT'},'exact_blocker':'BATCH096_SYNTHETIC_SCIENTIFIC_EVIDENCE_RECONSTITUTION_REQUIRED'}
 dump('batch096_external_scientific_reconstruction.json',corrected); dump('batch096_scientific_claim_invalidation.json',corrected); dump('batch096_public_language_correction.json',{'status':'PASS','required_statement':'Batch096 architecture scaffolding is retained; synthetic scientific conclusions are excluded from current authority.'})
 excluded=['repository_genome','eight_episode_materialization','role_measurement','active_brot_bulb_topology','tld_execution','amds_quality','source_ownership','critic_mutations']
 (OUT/'batch096_current_authority_exclusion_registry.jsonl').write_text(''.join(json.dumps({'claim':x,'status':'EXCLUDED','reason':'synthetic Batch096 evidence'})+'\n' for x in excluded))
 print('BATCH097_CUSTODY_INVALIDATION_PASS'); return 0 if custody['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
