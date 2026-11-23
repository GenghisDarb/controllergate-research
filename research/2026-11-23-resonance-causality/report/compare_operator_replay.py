"""Compare a fresh public-layout operator replay with preserved evidence."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, hashlib, json

ROOT = Path(__file__).resolve().parent.parent
FILES = ['dynamics/results.json','dynamics/summary.json',
         'dynamics/independent_operator_review_receipt.json',
         'dynamics/admissibility/RESULTS.json','dynamics/admissibility/SUMMARY.json']
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def normalize(value):
    data=copy.deepcopy(value)
    for key in ['executed_utc','reviewed_utc']: data.pop(key,None)
    if 'files' in data and 'results.json' in data['files']:
        data['files']['results.json']='TIMESTAMP_DEPENDENT_HASH_VERIFIED_SEPARATELY'
    return data
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--replay-dir',required=True,type=Path)
    parser.add_argument('--receipt',required=True,type=Path)
    args=parser.parse_args()
    if args.receipt.exists(): raise RuntimeError('Preserve existing receipts')
    for folder in [ROOT,args.replay_dir]:
        record=json.loads((folder/FILES[2]).read_text())
        assert record['files']['results.json']==digest(folder/FILES[0])
    rows=[]
    for relative in FILES:
        a=ROOT/relative;b=args.replay_dir/relative
        original=json.loads(a.read_text());replayed=json.loads(b.read_text())
        assert normalize(original)==normalize(replayed),relative
        rows.append({'path':relative,'status':'ALL_SCIENTIFIC_FIELDS_IDENTICAL',
                     'archived_sha256':digest(a),'replayed_sha256':digest(b)})
    receipt={'schema':'public_operator_replay_comparison.v1',
             'executed_utc':datetime.now(timezone.utc).isoformat(),
             'status':'PASS','files':rows,
             'executed_scripts':['run_operator_audit.py','independent_operator_review.py',
                                 'admissibility/run_admissibility.py'],
             'normalization':['Top-level execution/review UTC timestamps',
                              'Result SHA256 caused by changed execution timestamp; both bindings checked against actual bytes'],
             'scope':'Fresh public-layout execution plus exact result comparison; same runtime, not external empirical replication',
             'reviewer_sha256':digest(Path(__file__))}
    args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'compared_artifacts':len(rows),
                      'all_scientific_fields_identical':True},indent=2))
if __name__=='__main__':main()
