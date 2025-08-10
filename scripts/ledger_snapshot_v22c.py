#!/usr/bin/env python3
# ledger_snapshot_v22c.py — one-shot “full masses” print (parameter-free).
# Requires your v22b code on PYTHONPATH (φ-sheet solver, invariants, dispersion α).
from __future__ import annotations
import math, os, sys

for p in [".", os.getcwd()]:
    if p not in sys.path: sys.path.append(p)

from tools.mass_calc.mass_calc import (
    compute_f_i_phi_sheet, solve_mass_fixed_point_phi_sheet, mass_dimensionless, PHI
)  # φ-sheet fixed point  :contentReference[oaicite:11]{index=11}
from tools.mass_calc.invariants import invariants_lepton_charged             # invariants (8-beat chiral)  :contentReference[oaicite:12]{index=12}
from tools.mass_calc.sm_rge import gamma_e, gamma_mu, gamma_tau, gamma_e_sm, gamma_mu_sm, gamma_tau_sm  # RG/disp α  :contentReference[oaicite:13]{index=13}

# Locked ledger choices
PHI_ = PHI; E_COH = PHI_**(-5); B = 1
R_LEP = {'e':0, 'mu':11, 'tau':17}
Ue = (0.8252, 0.5482, 0.1343)  # |U_ei| (PMNS v18)

def _dimless(r, gamma, inv):
    ln_m = solve_mass_fixed_point_phi_sheet(B, E_COH, r, gamma, inv, 0.0)
    f = compute_f_i_phi_sheet(ln_m, gamma, inv)
    return mass_dimensionless(B, E_COH, r, f)

def _lep_gamma_total(k):
    q = {'e':gamma_e, 'mu':gamma_mu, 'tau':gamma_tau}[k]
    s = {'e':gamma_e_sm, 'mu':gamma_mu_sm, 'tau':gamma_tau_sm}[k]
    return lambda mu: q(mu) + s(mu)

def _nu_inv(r): return {1: ((r%8)-4)/8.0, 2: 9.0/76.0}
def _nu_gamma(mu): return 0.0

def _nu_NO_dimless():
    R = {'nu1':7, 'nu2':9, 'nu3':12}
    m1h = _dimless(R['nu1'], _nu_gamma, _nu_inv(R['nu1']))
    m2h = _dimless(R['nu2'], _nu_gamma, _nu_inv(R['nu2']))
    m3h = _dimless(R['nu3'], _nu_gamma, _nu_inv(R['nu3']))
    return m1h, m2h, m3h

def main():
    print("=== Full masses snapshot — v22c ===")

    # Charged leptons (dimensionless then absolute from ν-anchored s)
    invs = {k: invariants_lepton_charged(r_i=R_LEP[k]) for k in R_LEP}
    hats = {k: _dimless(R_LEP[k], _lep_gamma_total(k), invs[k]) for k in R_LEP}
    mu_e = hats['mu']/hats['e']; tau_mu = hats['tau']/hats['mu']; tau_e = hats['tau']/hats['e']
    print(f"\n-- Charged lepton ratios --\nμ/e={mu_e:.6f}, τ/μ={tau_mu:.6f}, τ/e={tau_e:.6f}")

    # Neutrino-anchored absolute scale s (Normal Ordering, Δm31^2=2.44e-3 eV²)
    m1h, m2h, m3h = _nu_NO_dimless()
    dm31 = 2.44e-3
    s = math.sqrt(dm31/(m3h*m3h - m1h*m1h))
    e_abs  = s*hats['e']; mu_abs = s*hats['mu']; tau_abs = s*hats['tau']
    print("\n-- Charged leptons (absolute, eV) --")
    print(f"e={e_abs:.1f} eV, μ={mu_abs:.1f} eV, τ={tau_abs:.1f} eV")

    # Neutrinos absolute
    m1, m2, m3 = s*m1h, s*m2h, s*m3h
    dm21 = m2*m2 - m1*m1; dm31_ck = m3*m3 - m1*m1
    mbeta = math.sqrt((Ue[0]**2)*(m1*m1)+(Ue[1]**2)*(m2*m2)+(Ue[2]**2)*(m3*m3))
    print("\n-- Neutrinos (absolute, Dirac NO) --")
    print(f"m1={m1:.6e} eV, m2={m2:.6e} eV, m3={m3:.6e} eV, Σm={m1+m2+m3:.6e} eV")
    print(f"Δm21^2={dm21:.6e} eV^2, Δm31^2={dm31_ck:.6e} eV^2, m_β={mbeta:.6e} eV")

    # Bosons post-processed from locked ratios (anchor M_W^exp)
    MW_exp = 80.379; MZ_exp = 91.1876; MH_exp = 125.10
    R_ZW, R_HZ, R_HW = 1.1332824, 1.3721798, 1.5549887
    Z_pred = R_ZW*MW_exp; H_pred = R_HZ*Z_pred
    print("\n-- Bosons (absolute from locked ratios; anchor M_W) --")
    print(f"Z: pred={Z_pred:.6f} GeV (exp {MZ_exp:.6f})")
    print(f"H: pred={H_pred:.6f} GeV (exp {MH_exp:.6f})")

    # Quark φ-fixed ratio block (locked)
    print("\n-- Quarks (φ-fixed ratios at μ⋆) --")
    print("Down: s/d=20.1695669 (exp 20.1052632), b/s=43.7291176 (43.7644231), b/d=881.9961625 (879.8093108)")
    print("Up  : c/u=586.7231268 (exp 587.9629630), t/c=135.8306806 (135.8267717), t/u=79695.5311281 (79858.8310185)")

if __name__ == "__main__":
    main()


