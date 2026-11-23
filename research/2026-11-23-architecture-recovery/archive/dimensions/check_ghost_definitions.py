"""Recompute archive definitions without tuning their arguments or normalizations.

This is a new arithmetic audit, not an original TORUS notebook rerun and not
evidence of physical prediction. Definitions frozen from Symposium 1748,
1837, 2131-2149, 5987-5990 before execution on 2026-11-23.

Independent eta methods: 100-term Euler product and DLMF 23.17.3 gamma value.
Igusa zero: exact odd-odd characteristic argument in accompanying report;
the numerical genus-2 theta product is supplementary. We report the raw
product P10, avoiding any ambiguity in conventional chi10 normalization.
For real z, Omega(z)=[[i,z],[z,i]] always has positive definite imaginary part.
Nonzero z examples are a repaired mathematical toy, not the archive's point.
"""
from pathlib import Path
import hashlib
import itertools
import json
import platform
import mpmath as mp

mp.mp.dps = 100
OUT = Path(__file__).parent


def s(x):
    return mp.nstr(x, 85)


def genus2_theta(a, b, z, radius=8):
    terms = []
    for n, m in itertools.product(range(-radius, radius + 1), repeat=2):
        u = mp.mpf(n) + mp.mpf(a[0]) / 2
        v = mp.mpf(m) + mp.mpf(a[1]) / 2
        exponent = -mp.pi*(u*u + v*v) + 2j*mp.pi*(z*u*v + u*b[0]/2 + v*b[1]/2)
        terms.append(mp.exp(exponent))
    return mp.fsum(terms)


Q = mp.exp(-2*mp.pi)  # Number theoretic nome; theta nome is its square root.
q = mp.exp(-mp.pi)
eta_product = Q**(mp.mpf(1)/24) * mp.fprod(1 - Q**n for n in range(1, 101))
eta_gamma = mp.gamma(mp.mpf(1)/4)/(2*mp.pi**(mp.mpf(3)/4))
eta24 = eta_product**24
theta2, theta3, theta4 = [mp.jtheta(n, 0, q) for n in (2, 3, 4)]
eta_theta = (theta2*theta3*theta4/2)**(mp.mpf(1)/3)
lam = (theta2/theta3)**4
j_value = 256*(1-lam+lam**2)**3/(lam**2*(1-lam)**2)
arch_eta = mp.mpf('0.003917')
arch_chi = mp.mpf('0.001867')
arch_mid = mp.sqrt(arch_eta*arch_chi)
arch_25 = mp.sqrt(arch_mid*arch_chi)
arch_3 = mp.sqrt(arch_25*arch_chi)
assert abs(eta_product-eta_gamma) < mp.mpf('1e-95')
assert abs(eta_product-eta_theta) < mp.mpf('1e-95')
assert abs(j_value-1728) < mp.mpf('1e-90')
even = [(a,b) for a in itertools.product((0,1), repeat=2)
              for b in itertools.product((0,1), repeat=2)
              if sum(x*y for x,y in zip(a,b)) % 2 == 0]
assert len(even) == 10
assert ((1,1),(1,1)) in even  # even genus-2, odd in both genus-1 factors
coupled = []
for zstr in ('0', '0.001', '0.01', '0.05', '0.1'):
    z = mp.mpf(zstr)
    theta = [genus2_theta(a,b,z) for a,b in even]
    P10 = mp.fprod(x*x for x in theta)
    rec = {'real_offdiagonal_z':zstr, 'abs_raw_product_squared_P10':s(abs(P10)),
           'abs_P10_over_4096':s(abs(P10)/4096),
           'odd_odd_theta_absolute':s(abs(genus2_theta((1,1),(1,1),z)))}
    if z:
        rec['abs_P10_over_z_squared'] = s(abs(P10)/(z*z))
    coupled.append(rec)

# Recheck a nonzero case with a larger summation square. This addresses an
# actual remaining numerical risk (theta-tail truncation), not a broad test suite.
zcheck=mp.mpf('0.01')
p8=mp.fprod(genus2_theta(a,b,zcheck,8)**2 for a,b in even)
p9=mp.fprod(genus2_theta(a,b,zcheck,9)**2 for a,b in even)
assert abs(p8-p9) < mp.mpf('1e-85')

# A later explicit archived recipe really is reconstructible. Preserve this
# positive result separately from unsupported interpretations of its plateau.
weight = lambda n: 1 + mp.mpf('.5')*mp.cos(mp.log(n)) + mp.mpf('.1')*mp.log(n)
increment = lambda n: -weight(n)*mp.log1p(-mp.exp(-n))
partition = lambda N: mp.mpf(1)/24 + mp.fsum(increment(n) for n in range(1,N+1))
partition_rows = [{'N':n,'partial_sum':s(partition(n)),'forward_increment_at_N':s(increment(n))}
                  for n in [5,6,10,11,13,14,15,17,20,50,200]]

result = {
 'status':'new deterministic audit of exact archived definitions; not physical validation',
 'precision_decimal_digits':mp.mp.dps,
 'python':platform.python_version(), 'mpmath':mp.__version__,
 'definitions':{
   'eta_tau':'i', 'eta_Q':'exp(-2*pi)', 'eta_product_terms':100,
   'eta_gamma_formula':'Gamma(1/4)/(2*pi^(3/4))',
   'theta_nome':'exp(-pi)',
   'archive_Omega0':'[[i,0],[0,i]]',
   'raw_P10':'product over 10 even characteristics of theta[a,b](0,Omega)^2',
   'theta_characteristics':'a,b each length 2 in {0,1}; theta uses halves a/2,b/2',
   'normalization_note':'Any nonzero normalization leaves chi10(Omega0)=0. P10/4096 is reported only as a declared scale, not unique convention.',
 },
 'eta':{
   'eta_i_product':s(eta_product), 'eta_i_gamma':s(eta_gamma),
   'eta_i_theta_identity':s(eta_theta), 'product_gamma_abs_error':s(abs(eta_product-eta_gamma)),
   'eta_i_power24':s(eta24), 'archived_power24':'0.003917',
   'archived_over_true_ratio':s(arch_eta/eta24),
   'relative_error_percent':s(100*(arch_eta/eta24-1)),
   'theta4_power4':s(theta4**4), 'eta_squared_over_theta4_squared':s((eta_product/theta4)**2),
 },
 'j':{'j_i_lambda_formula':s(j_value),'normalized_J_i':s(mp.kleinj(1j)),
      'archive_j_i':'1728','normalization':'j=1728*J; mpmath.kleinj returns J'},
 'chi10':{'archive_value':'0.001867', 'archive_approximation':'exp(-2*pi)',
   'exp_minus_2pi':s(Q), 'exact_value_at_archived_Omega0':'0',
   'proof':'At block diagonal Omega, even genus-2 characteristic (a,b)=((1,1),(1,1)) factors into two odd genus-1 theta constants at zero, each zero; it is a factor in chi10.'},
 'dependent_geometric_means':{
   'archive_base_values':{'C_eta':str(arch_eta),'C_chi10':str(arch_chi)},
   'C_mid_from_archived_rounded_bases':s(arch_mid),
   'C_2_5_from_archived_rounded_bases':s(arch_25),
   'C_3_from_archived_rounded_bases':s(arch_3),
   'with_definitions_corrected_at_archived_point':{'C_mid':'0','C_2_5':'0','C_3':'0'},
   'independence':'Geometric-mean descendants contain no additional free information beyond the chosen two bases.'},
 'new_coupling_toy':{
   'interpretation':'Mathematical example of zero at uncoupled point and nonzero response under coupling; it does not select 14 layers or establish biology/physics.',
   'family':'Omega(z)=[[i,z],[z,i]], z real', 'values':coupled,
   'small_z_raw_product_absolute_coefficient':'2^14*pi^2*eta(i)^48',
   'small_z_coefficient_numeric':s(2**14*mp.pi**2*eta24**2),
   'radius8_vs9_abs_error_at_z_0_01':s(abs(p8-p9))},
 'ghost_score_example':{'formula':'kappa/min_delta','eta_table_delta':'0.009',
   'eta_table_kappa':'1.12','derived_score':s(mp.mpf('1.12')/mp.mpf('.009')),
   'unresolved':'Coordinate/normalization and derivative prescription for kappa, candidate reference list, and uncertainty-aware occupancy rule are not specified by the recovered formula.'},
 'partition_reconstruction':{
   'source_lines':'P04 2847-2852;2876-2888',
   'formula':'S_N=1/24-sum_{n=1}^N (1+0.5*cos(log(n))+0.1*log(n))*log(1-exp(-n))',
   'archived_plateau':'1.0439352679994645',
   'N50_absolute_difference_from_archive':s(abs(partition(50)-mp.mpf('1.0439352679994645'))),
   'values':partition_rows,
   'scope':'Reconstruction of displayed mathematical recipe, not a rerun of unavailable Wolfram call payload; no independent physical data.'},
 'source_definition_sha256':hashlib.sha256(Path('project_sources/04-TORUS-Inter-GPT-Symposium-Seed-Constant-Meta-Recursion-Expansion.txt').read_bytes()).hexdigest(),
 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(OUT/'ghost_definition_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
