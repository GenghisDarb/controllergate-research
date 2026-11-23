"""Replay the sealed causal experiment in a temporary copy, preserving originals.

Only execution timestamps and the resulting hash of regenerated results.json
are normalized for comparison. All mathematical/model outcome fields and all
source/specification identities must match. This is a portability/replay gate,
not external peer review or independent biological evidence.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,platform,shutil,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parent
SOURCE_FILES=[
    'EXPERIMENT_SPEC.json','FROZEN_DESIGN.json','causal_history.py',
    'model/token_contract.json','model/prior_seed_spec.json',
    'independent_review.py','FOLLOWUP_SPEC.json','derive_witnesses.py',
    'export_policies.py',
]
OUTPUT_FILES=['results.json','summary.json','INDEPENDENT_REVIEW.json',
              'FOLLOWUP_RESULTS.json','POLICY_EXAMPLES.json']
STEPS=['causal_history.py','independent_review.py','derive_witnesses.py','export_policies.py']
HASH_FIELDS={
    'INDEPENDENT_REVIEW.json':'source_hashes',
    'FOLLOWUP_RESULTS.json':'input_hashes',
    'POLICY_EXAMPLES.json':'hashes',
}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def comparable(name,value):
    value=copy.deepcopy(value)
    value.pop('executed_utc',None)
    if name in HASH_FIELDS:
        value[HASH_FIELDS[name]].pop('results.json')
    return value

def verify_bound_hashes(base,name,value):
    if name in HASH_FIELDS:
        for path,digest in value[HASH_FIELDS[name]].items():
            assert sha(base/path)==digest,(name,'invalid recorded hash',path)
    if name=='results.json':
        assert value['frozen_design_sha256']==sha(base/'FROZEN_DESIGN.json')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',type=Path,help='Optional NEW receipt path. Existing files are refused.')
    args=parser.parse_args()
    if args.receipt is not None and args.receipt.exists():raise SystemExit('Receipt path already exists; choose a new path.')
    names=SOURCE_FILES+OUTPUT_FILES
    before={name:sha(ROOT/name) for name in names}
    frozen=json.loads((ROOT/'FROZEN_DESIGN.json').read_text())
    assert all(before[name]==digest for name,digest in frozen['files'].items()),'Frozen source mismatch'
    originals={name:json.loads((ROOT/name).read_text()) for name in OUTPUT_FILES}
    for name,value in originals.items():verify_bound_hashes(ROOT,name,value)
    checks={}
    with tempfile.TemporaryDirectory(prefix='causal-history-replay-') as td:
        work=Path(td)
        for name in names:
            target=work/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,target)
        for name in OUTPUT_FILES:(work/name).unlink()
        for script in STEPS:
            subprocess.run([sys.executable,str(work/script)],cwd=work,check=True,capture_output=True,text=True)
        for name in OUTPUT_FILES:
            replay=json.loads((work/name).read_text())
            verify_bound_hashes(work,name,replay)
            assert comparable(name,replay)==comparable(name,originals[name]),('Scientific outcome mismatch',name)
            checks[name]='PASS: all scientific fields and source identities identical'
        assert json.loads((work/'INDEPENDENT_REVIEW.json').read_text())['result']=='PASS'
    assert before=={name:sha(ROOT/name) for name in names},'Original artifacts changed during replay'
    receipt={
        'schema':'causal_portable_replay.v1','status':'PASS',
        'executed_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
        'mode':'Fresh temporary copy; no network or nonstandard dependencies',
        'scripts_executed':STEPS,'checks':checks,
        'normalization':['Top-level executed_utc','Recorded results.json hashes caused by its new timestamp, checked against the actual new bytes before normalization'],
        'original_artifacts_unchanged':True,'frozen_source_match':True,
        'independent_implementation_cases':originals['INDEPENDENT_REVIEW.json']['case_count'],
        'policy_initial_states_replayed':sum(len(p['all_initial_state_replays']) for p in originals['POLICY_EXAMPLES.json']['policies']),
        'original_hashes':before,'verifier_sha256':sha(Path(__file__)),
        'scope':'Portability and exact deterministic replay; not external peer review or empirical biology.'
    }
    serialized=json.dumps(receipt,indent=2)+'\n'
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        with args.receipt.open('x') as f:f.write(serialized)
    print(serialized,end='')

if __name__=='__main__':main()
