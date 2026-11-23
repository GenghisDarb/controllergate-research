"""Verify saved bytes; optionally replay observers in a disposable copy."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--rerun-observers',action='store_true');args=p.parse_args()
    manifest=json.loads((ROOT/'MANIFEST.json').read_text())
    for row in manifest['files']:
        b=(ROOT/row['path']).read_bytes()
        assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],row['path']
    receipt={'hashes':'PASS','payloads_checked':len(manifest['files'])}
    if args.rerun_observers:
        with tempfile.TemporaryDirectory(prefix='controllergate-observer-') as d:
            run=Path(d)/'experiments';shutil.copytree(ROOT/'experiments',run,ignore=shutil.ignore_patterns('__pycache__'))
            original=json.loads((run/'results.json').read_text())
            for name in ['results.json','summary.json','INDEPENDENT_OBSERVER_REVIEW.json']:(run/name).unlink(missing_ok=True)
            for name in ['observer_interlock.py','independent_observer_review.py']:
                subprocess.run([sys.executable,str(run/name)],check=True,capture_output=True,text=True)
            replay=json.loads((run/'results.json').read_text())
            original.pop('executed_utc');replay.pop('executed_utc')
            assert original==replay,'Scientific outputs differ'
            review=json.loads((run/'INDEPENDENT_OBSERVER_REVIEW.json').read_text())
            assert review['result']=='PASS_WITH_STATED_SCOPE'
            receipt['observer_replay']='PASS: all scientific fields identical; independent reconstruction passed'
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
