"""Exact rational checks of a review-triggered projected reference candidate.

The mathematical oracle is written directly with Fractions. Source parity uses
only the archived _relax function extracted through AST, with no other code run.
Original source and parent experiment are not changed.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime,timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import random
import sys

HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exact_step(x,p,a):
    e=[v-r for v,r in zip(x,p)];n=len(x)
    d=F(79,100)-F(21,100)*a;c=F(21,200)*(1-a)
    return [p[i]+d*e[i]+c*(e[i-1]+e[(i+1)%n]) for i in range(n)]
def project(x):return [max(F(0),v) for v in x]
def sq(x):return sum((v*v for v in x),F(0))
def diff(x,y):return [a-b for a,b in zip(x,y)]
def energy(x,p,a):
    e=diff(x,p)
    return a*sq(e)/2+(1-a)*sum(((e[i]-e[(i+1)%len(e)])**2 for i in range(len(e))),F(0))/8
def source_function():
    tree=ast.parse((HERE/'source_snapshot/kernels.py').read_text())
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='LadderKernel')
    fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='_relax')
    fn.decorator_list=[]
    module=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(module)
    namespace={};exec(compile(module,'archived_relax_only','exec'),namespace)
    return namespace['_relax']
def encoded(x):return [str(v) for v in x]
def cases(n,a):
    zero=[F(0)]*n;one=[F(1)]*n
    unit=zero.copy();unit[0]=F(1)
    opposite=zero.copy();opposite[n//2]=F(1)
    alternating=[F(i%2) for i in range(n)]
    reversed_alt=alternating[::-1]
    sparse=unit.copy();sparse[n//2]=F(2)
    yield 'sparse_counterexample',unit,zero,[2*v for v in unit]
    yield 'zero_parent',zero,unit,opposite
    yield 'uniform_mode',one,zero,[F(2)]*n
    yield 'alternating_boundary',alternating,reversed_alt,[2*v for v in reversed_alt]
    yield 'two_sparse_peaks',sparse,zero,opposite
    rng=random.Random(20261123+n*1000+int(a*100))
    for k in range(15):
        parent=[F(0) if rng.random()<0.25 else F(rng.randrange(41),20) for _ in range(n)]
        x=[F(0) if rng.random()<0.35 else F(rng.randrange(41),20) for _ in range(n)]
        y=[F(0) if rng.random()<0.35 else F(rng.randrange(41),20) for _ in range(n)]
        yield 'rational_random_'+str(k),parent,x,y

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path);args=ap.parse_args()
    output=args.output_dir or HERE
    if args.output_dir:
        if output.exists():raise RuntimeError('Use a new output directory')
        output.mkdir(parents=True)
    if (output/'RESULTS.json').exists():raise RuntimeError('Preserve original results')
    frozen=json.loads((HERE/'FROZEN_EXTENSION.json').read_text())
    for path,digest in frozen['files'].items():assert sha(HERE/path)==digest,path
    relax=source_function()
    records=[];failure=[];max_source_error=0.0
    unprojected_negative_cases=0;nontrivial_projection_cases=0
    for n in (12,13,14,15,28):
      for a in map(F,('0','1/5','1/2','1')):
        q=1-F(21,50)*a
        for name,p,x,y in cases(n,a):
          u=exact_step(x,p,a);v=exact_step(y,p,a);fx=project(u);fy=project(v)
          unprojected_negative_cases+=min(u)<0 or min(v)<0
          nontrivial_projection_cases+=(u!=fx or v!=fy)
          srcx=[float(r)+s for r,s in zip(p,relax([float(t-r) for t,r in zip(x,p)],[0.0]*n,float(a)))]
          srcy=[float(r)+s for r,s in zip(p,relax([float(t-r) for t,r in zip(y,p)],[0.0]*n,float(a)))]
          discrepancy=max([abs(a-b) for a,b in zip(srcx,map(float,u))]+[abs(a-b) for a,b in zip(srcy,map(float,v))])
          max_source_error=max(max_source_error,discrepancy)
          checks={
            'projected_nonnegative':min(fx+fy)>=0,
            'parent_fixedpoint':project(exact_step(p,p,a))==p,
            'distance_x_bound':sq(diff(fx,p))<=q*q*sq(diff(x,p)),
            'distance_y_bound':sq(diff(fy,p))<=q*q*sq(diff(y,p)),
            'pairwise_bound':sq(diff(fx,fy))<=q*q*sq(diff(x,y)),
            'energy_x_bound':energy(fx,p,a)-energy(x,p,a)<=-F(79,42)*sq(diff(fx,x)),
            'energy_y_bound':energy(fy,p,a)-energy(y,p,a)<=-F(79,42)*sq(diff(fy,y)),
            'source_parity':discrepancy<=1e-12}
          row={'N':n,'a':str(a),'case':name,'parent':encoded(p),'x':encoded(x),'y':encoded(y),
               'unprojected_x':encoded(u),'projected_x':encoded(fx),'projected_y':encoded(fy),
               'checks':checks,'pairwise_squared_margin':str(q*q*sq(diff(x,y))-sq(diff(fx,fy))),
               'energy_x_margin':str(-F(79,42)*sq(diff(fx,x))-(energy(fx,p,a)-energy(x,p,a))),
               'source_error':discrepancy}
          records.append(row)
          if not all(checks.values()):failure.append({k:row[k] for k in ['N','a','case','checks']})
    witness=next(r for r in records if r['N']==14 and r['a']=='1/2' and r['case']=='sparse_counterexample')
    assert witness['unprojected_x'][1]=='-21/400' and witness['unprojected_x'][-1]=='-21/400'
    summary={'schema':'projected_reference_admissibility_results.v1','executed_utc':datetime.now(timezone.utc).isoformat(),
      'status':'PASS_WITH_STATED_SCOPE' if not failure else 'FAIL','pairs':len(records),'single_inputs':2*len(records),
      'exact_checks_per_pair':7,'floating_source_parity_checks':len(records),
      'unprojected_negative_pairs':unprojected_negative_cases,'nontrivial_projection_pairs':nontrivial_projection_cases,
      'maximum_source_absolute_difference':max_source_error,'failures':failure,
      'counterexample':witness,'frozen_record_sha256':sha(HERE/'FROZEN_EXTENSION.json'),
      'python':sys.version.split()[0],
      'scope':'400 predeclared exact-rational pairs; supplied nonnegative parent, nonnegative-orthant projection, fixed a. No reaction-semantic equivalence or physical validation.'}
    (output/'RESULTS.json').write_text(json.dumps({**summary,'cases':records},indent=2)+'\n')
    (output/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='counterexample'},indent=2))

if __name__=='__main__':main()
