from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path

EXPECTED='c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b'
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--bundle');ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 path=Path(a.bundle) if a.bundle else None
 if not path or not path.is_file():record={'status':'BLOCK','exact_blocker':'BATCH097_TLD_RAW_SOURCE_CI_REVERIFICATION_REQUIRED','expected_sha256':EXPECTED,'local_checkpoint_custody_record_is_not_raw_ci_reverification':True,'authority_allowed':'blocker propagation','authority_forbidden':['TLD execution authority','scientific closure']}
 else:
  data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
  with zipfile.ZipFile(path) as z:members=len(z.infolist());uncompressed=sum(x.file_size for x in z.infolist())
  record={'status':'PASS' if sha==EXPECTED and len(data)==5389984 and members==20 and uncompressed==22131530 else 'BLOCK','exact_blocker':None if sha==EXPECTED else 'historical_tld_source_bundle_identity_mismatch','observed_sha256':sha,'size':len(data),'members':members,'uncompressed_bytes':uncompressed}
 out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');print(record['status']);return 0
if __name__=='__main__':raise SystemExit(main())
