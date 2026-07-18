from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any


EXPECTED_SHA='c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b'; EXPECTED_SIZE=5_389_984; EXPECTED_MEMBERS=20; EXPECTED_UNCOMPRESSED=22_131_530
RANGES=((1,11,'Detailed Breakdown of Notebooks 1–11'),(12,14,'Detailed Breakdown of Notebooks 12-14'),(15,24,'Detailed Breakdown of Notebooks 15-24'),(25,30,'Detailed Breakdown of Notebooks 25-30'),(31,33,'Detailed Breakdown of Notebooks 31-33'),(34,37,'Detailed Breakdown of Notebooks 34-37'),(38,44,'Detailed Breakdown of Notebooks 38-44'))


def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def lines(path: Path, values: list[dict[str,Any]]) -> None: path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in values),encoding='utf-8',newline='\n')
def dump(path: Path, value: Any) -> None: path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')


def engineering_law(text: str) -> str:
    value=text.lower()
    if any(x in value for x in ('null','baseline','control')): return 'Bind each observed trace to a frozen parent and matched deterministic control before comparison.'
    if any(x in value for x in ('threshold','onset','persistence')): return 'Freeze thresholds and distinguish onset, persistence, and closure before evaluating outcomes.'
    if any(x in value for x in ('provenance','registry','lineage')): return 'Preserve registry-first provenance, parent lineage, and immutable source identity.'
    if any(x in value for x in ('perturb','survival','ablation')): return 'Evaluate deterministic perturbations and retain negative and mixed outcomes.'
    if any(x in value for x in ('operator','transform','window','metric')): return 'Freeze operators, transforms, windows, and metric identities before execution.'
    return 'Preserve this source-bound requirement as a read-only diagnostic constraint with no repair authority.'


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--bundle',required=True); ap.add_argument('--output',required=True); a=ap.parse_args(); bundle=Path(a.bundle); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    data=bundle.read_bytes(); observed_sha=sha(data); findings=[]; requirements=[]; source_records=[]
    with zipfile.ZipFile(bundle) as archive:
        infos=archive.infolist(); unsafe=[i.filename for i in infos if Path(i.filename).is_absolute() or '..' in Path(i.filename).parts]; duplicate=sorted({i.filename for i in infos if sum(x.filename==i.filename for x in infos)>1})
        blobs={i.filename:archive.read(i) for i in infos if not i.is_dir()}
    for name,blob in sorted(blobs.items()): source_records.append({'path':name,'sha256':sha(blob),'size':len(blob)})
    for start,end,prefix in RANGES:
        matches=[name for name in blobs if prefix in Path(name).name]
        if len(matches)!=1:
            findings.append({'range':f'{start}-{end}','blocker':'source_file_missing_or_ambiguous','matches':matches}); continue
        name=matches[0]; text=blobs[name].decode('utf-8',errors='replace'); source_lines=text.splitlines()
        headings=[]
        for index,line in enumerate(source_lines,1):
            for match in re.finditer(r'(?i)notebook\s*(?:no\.?\s*)?(\d{1,2})\b',line):
                n=int(match.group(1))
                if start<=n<=end: headings.append((n,index))
        for number in range(start,end+1):
            occurrences=[line_no for n,line_no in headings if n==number]
            if occurrences:
                line_start=occurrences[0]; next_lines=[line_no for n,line_no in headings if line_no>line_start]; line_end=min((min(next_lines)-1) if next_lines else len(source_lines),line_start+80)
            else:
                line_start=1; line_end=min(len(source_lines),80); findings.append({'notebook':number,'warning':'notebook heading not isolated; file-level source identity retained'})
            excerpt='\n'.join(source_lines[line_start-1:line_end]); content_id=sha(excerpt.encode('utf-8'))
            requirements.append({'requirement_id':f'TLD-NB-{number:02d}-SOURCE-BOUNDARY','notebook':number,'source_file':name,'source_range':{'line_start':line_start,'line_end':line_end},'stable_content_identity':content_id,'plain_engineering_law':engineering_law(excerpt),'canonical_component':'controllergate.topology evidence compiler and AMDS decision frame','test':'candidate trace projection and matched-parent null audit','execution_depth':'source parsed; candidate execution required separately','authority_allowed':'read-only diagnostic constraint','authority_forbidden':['source ownership','repair','count','release'],'status':'PARSED','blocker':None})
    auxiliary=(('Formal Lexicon','formal_lexicon'),('Errata Map','errata_map'),('Technical Standards','technical_standard'))
    for token,kind in auxiliary:
        matches=[name for name in blobs if token.lower() in Path(name).name.lower()]
        if len(matches)==1:
            name=matches[0]; requirements.append({'requirement_id':f'TLD-{kind.upper()}','notebook':None,'source_file':name,'source_range':{'line_start':1,'line_end':None},'stable_content_identity':sha(blobs[name]),'plain_engineering_law':'Freeze terminology, corrections, and input protocol identities before candidate execution.','canonical_component':'controllergate.topology evidence compiler','test':'source identity and frame binding audit','execution_depth':'source parsed','authority_allowed':'documentation and diagnostic constraint','authority_forbidden':['source ownership','repair','count','release'],'status':'PARSED','blocker':None})
        else: findings.append({'auxiliary':kind,'blocker':'source_file_missing_or_ambiguous','matches':matches})
    notebook_count=len({x['notebook'] for x in requirements if x['notebook'] is not None}); passed=observed_sha==EXPECTED_SHA and len(data)==EXPECTED_SIZE and len(blobs)==EXPECTED_MEMBERS and sum(len(x) for x in blobs.values())==EXPECTED_UNCOMPRESSED and not unsafe and not duplicate and notebook_count==44 and all(x['status']=='PARSED' for x in requirements)
    custody={'status':'PASS' if passed else 'BLOCK','path_recorded_as_non_authoritative_runtime_input':str(bundle),'observed_sha256':observed_sha,'expected_sha256':EXPECTED_SHA,'observed_size':len(data),'expected_size':EXPECTED_SIZE,'archive_member_count':len(blobs),'expected_archive_member_count':EXPECTED_MEMBERS,'uncompressed_bytes':sum(len(x) for x in blobs.values()),'expected_uncompressed_bytes':EXPECTED_UNCOMPRESSED,'unsafe_paths':unsafe,'duplicate_paths':duplicate,'source_records':source_records,'authority_allowed':'source requirement parsing','authority_forbidden':['commit raw source','repair','release']}
    dump(out/'batch097_tld_source_bundle_custody.json',custody); lines(out/'tld_1_44_requirement_ledger_v2.jsonl',requirements); dump(out/'tld_source_parse_audit_v2.json',{'status':'PASS' if passed else 'BLOCK','notebook_count':notebook_count,'requirement_count':len(requirements),'findings':findings,'source_bundle_sha256':observed_sha,'workflow_raw_bundle_reverification':'REQUIRED'}); dump(out/'tld_operator_metric_registry_v2.json',{'status':'PASS','frozen_before_candidate_execution':True,'operators':['parent_bound_identity','deterministic_hash_projection','matched_parent_null'],'authority_forbidden':['source ownership','repair','count']})
    print('BATCH097_TLD_SOURCE_PARSE_'+('PASS' if passed else 'BLOCK')); return 0


if __name__=='__main__': raise SystemExit(main())
