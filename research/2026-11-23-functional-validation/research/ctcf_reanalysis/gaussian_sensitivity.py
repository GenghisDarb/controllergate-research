"""Analytic, post-result generous Gaussian null; original outputs unchanged."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import numpy as np
from analyze_ctcf import ROOT, LAGS, ingest, partition, track_weights, log_density, sha, save, verify_seal


def freeze():
    verify_seal()
    if (ROOT/'GAUSSIAN_SENSITIVITY_SEAL.json').exists() or (ROOT/'gaussian_sensitivity_results.json').exists():
        raise RuntimeError('Refusing to overwrite sensitivity seal/results')
    names=['gaussian_sensitivity.py','gaussian_null_spec.json','results.json','FROZEN_ANALYSIS.json']
    save('GAUSSIAN_SENSITIVITY_SEAL.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
        'hashes':{n:sha(ROOT/n) for n in names},'scope':'Post-result sensitivity; frozen before its own execution.'})
    print('Sensitivity sealed; not executed.')


def verify():
    verify_seal();s=json.loads((ROOT/'GAUSSIAN_SENSITIVITY_SEAL.json').read_text())
    for n,h in s['hashes'].items():assert sha(ROOT/n)==h


def fit_gaussians(train):
    weights=track_weights(train);models={}
    for lag in LAGS:
        use=train[:,1]==lag; x=train[use,2:4]; w=weights[use]
        mean=np.sum(w[:,None]*x,axis=0)/w.sum(); centered=x-mean
        cov=(centered*w[:,None]).T@centered/w.sum()
        eigen=np.linalg.eigvalsh(cov);assert np.all(eigen>0)
        models[str(lag)]={'mean_um':mean.tolist(),'covariance_um2':cov.tolist(),
                         'covariance_eigenvalues_um2':eigen.tolist(),'training_trajectories':int(use.sum())}
    return models


def gaussian_scores(data,models):
    scores=np.empty(len(data))
    for lag in LAGS:
        use=data[:,1]==lag;m=models[str(lag)]
        centered=data[use,2:4]-np.asarray(m['mean_um'])
        cov=np.asarray(m['covariance_um2']);sign,logdet=np.linalg.slogdet(cov);assert sign>0
        scores[use]=-math.log(2*math.pi)-.5*logdet-.5*np.einsum('ij,ij->i',centered,np.linalg.solve(cov,centered.T).T)
    return scores


def compare(data,models,theta,seed):
    null=gaussian_scores(data,models);mix=log_density(theta,data,2)
    ids,inv,counts=np.unique(data[:,0].astype(int),return_inverse=True,return_counts=True)
    n=np.bincount(inv,weights=null)/counts;m=np.bincount(inv,weights=mix)/counts;d=m-n
    rng=np.random.default_rng(seed)
    boot=np.array([d[rng.integers(0,len(d),len(d))].mean() for _ in range(1000)])
    return {'eligible_trajectories':len(ids),'mean_track_averaged_log_score_free_Gaussian':float(n.mean()),
        'mean_track_averaged_log_score_original_M2':float(m.mean()),
        'paired_gain_M2_minus_free_Gaussian':float(d.mean()),
        'conditional_trajectory_bootstrap_95pct_interval':np.quantile(boot,[.025,.975]).tolist(),
        'by_lag':{str(l):{'mean_score_free_Gaussian':float(null[data[:,1]==l].mean()),
                        'mean_score_original_M2':float(mix[data[:,1]==l].mean())} for l in LAGS}}


def execute():
    verify()
    if (ROOT/'gaussian_sensitivity_results.json').exists():raise RuntimeError('Existing sensitivity results')
    rep1,_=ingest('ctcf_rep1_cell01.mat');rep3,_=ingest('ctcf_rep3_cell01.mat')
    use=np.array([partition(int(i))=='train' for i in rep1[:,0]]);train,held=rep1[use],rep1[~use]
    models=fit_gaussians(train);original=json.loads((ROOT/'results.json').read_text())
    theta=np.asarray(original['model_M2']['theta']);primary=compare(held,models,theta,20261123)
    secondary=compare(rep3,models,theta,20261124)
    assert abs(primary['mean_track_averaged_log_score_original_M2']-original['primary_heldout_rep1']['mean_track_averaged_log_score_M2'])<1e-12
    assert abs(secondary['mean_track_averaged_log_score_original_M2']-original['secondary_rep3_no_refit']['mean_track_averaged_log_score_M2'])<1e-12
    receipt={'status':'PASS','completed_utc':datetime.now(timezone.utc).isoformat(),
        'seal_sha256':sha(ROOT/'GAUSSIAN_SENSITIVITY_SEAL.json'),
        'scope':'Post-result analytic Gaussian sensitivity on same splits, not independent validation.',
        'fitted_gaussian_models':models,'primary_heldout_rep1':primary,'secondary_rep3_no_refit':secondary,
        'original_outputs_unchanged':True,'limits':['Free Gaussians are descriptive and do not identify physical diffusion rates.',
        'M2 still omits defocalization/tracking selection and does not identify bound fractions.',
        'Paired bootstrap is conditional on fitted parameters and within-record trajectory exchangeability.']}
    save('gaussian_sensitivity_results.json',receipt);verify();print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--freeze',action='store_true');g.add_argument('--execute',action='store_true')
    args=parser.parse_args();freeze() if args.freeze else execute()
