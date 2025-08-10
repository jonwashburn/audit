#!/usr/bin/env python3
import math
import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Cosmo:
    H0: float = 70.0  # km/s/Mpc
    Omega_m0: float = 0.3
    Omega_L0: float = 0.7
    h: float = 0.7

KM_S_MPC_TO_SI = 1000.0 / (3.085677581e22)
MPC_TO_M = 3.085677581e22

def E(a, cosmo: Cosmo):
    return math.sqrt(cosmo.Omega_m0 / a**3 + cosmo.Omega_L0)

def H(a, cosmo: Cosmo):
    return cosmo.H0 * KM_S_MPC_TO_SI * E(a, cosmo)

def k_phys(a, k_hmpc, cosmo: Cosmo):
    # k in h/Mpc -> comoving 1/m, then physical 1/m
    k_com_mpc = k_hmpc * cosmo.h  # 1/Mpc
    k_com_si = k_com_mpc / MPC_TO_M  # 1/m
    return k_com_si / a  # physical 1/m

def a_char(a, k_hmpc, cosmo: Cosmo, beta=1.0):
    # dimensionally: a_char ~ (a H)^2 / k_phys  [m/s^2]
    kp = k_phys(a, k_hmpc, cosmo)
    return beta * (a * H(a, cosmo))**2 / max(kp, 1e-30)

def mu_eff(a, k_hmpc, a0, cosmo: Cosmo, beta=1.0):
    ach = a_char(a, k_hmpc, cosmo, beta)
    x = a0 / max(ach, 1e-30)
    # capped enhancement: μ = 1 + x/(1+x) ∈ (1,2)
    return 1.0 + x / (1.0 + x)

def growth_rhs(ln_a, y, k_hmpc, a0, cosmo: Cosmo, beta: float):
    a = math.exp(ln_a)
    D, G = y
    dlnH_dlnA = -1.5 * cosmo.Omega_m0 / (cosmo.Omega_m0 + cosmo.Omega_L0 * a**3)
    coeff = 2.0 + dlnH_dlnA
    mu = mu_eff(a, k_hmpc, a0, cosmo, beta)
    Om_a = cosmo.Omega_m0 / (cosmo.Omega_m0 + cosmo.Omega_L0 * a**3)
    Dp = G
    Gp = -coeff * G + 1.5 * Om_a * mu * D
    return (Dp, Gp)

def integrate_growth(a_start=1e-3, a_end=1.0, k_hmpc=0.1, a0=1.2e-10, N=400, beta: float = 1.0):
    cosmo = Cosmo()
    ln_a0 = math.log(a_start)
    ln_a1 = math.log(a_end)
    h = (ln_a1 - ln_a0) / N
    D = a_start
    G = D
    ln_a = ln_a0
    for _ in range(N):
        k1 = growth_rhs(ln_a, (D,G), k_hmpc, a0, cosmo, beta)
        k2 = growth_rhs(ln_a + 0.5*h, (D+0.5*h*k1[0], G+0.5*h*k1[1]), k_hmpc, a0, cosmo, beta)
        k3 = growth_rhs(ln_a + 0.5*h, (D+0.5*h*k2[0], G+0.5*h*k2[1]), k_hmpc, a0, cosmo, beta)
        k4 = growth_rhs(ln_a + h, (D+h*k3[0], G+h*k3[1]), k_hmpc, a0, cosmo, beta)
        D += (h/6.0) * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0])
        G += (h/6.0) * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1])
        ln_a += h
    return D


# ------------------- ILG a0 from canonical schedule -------------------

def compute_lambda_rec():
    # Planck length (recognition length) λ_rec = sqrt(ħ G / c^3)
    HBAR = 1.054_571_817e-34  # J s
    G_SI = 6.674_30e-11       # m^3 kg^-1 s^-2
    C_SI = 299_792_458.0      # m s^-1
    return math.sqrt(HBAR * G_SI / (C_SI**3))


def compute_a0_from_kappa(kappa: float) -> float:
    # a0 = κ * (c^2/λ_rec) * (S / (T_breath * N_gates)), with S = 489/512, T=1024, N_gates=9
    C_SI = 299_792_458.0
    lam_rec = compute_lambda_rec()
    S = 489.0 / 512.0
    T = 1024.0
    N_gates = 9.0
    return kappa * (C_SI**2 / lam_rec) * (S / (T * N_gates))


def kappa_for_target_a0(a0_target: float) -> float:
    C_SI = 299_792_458.0
    lam_rec = compute_lambda_rec()
    S = 489.0 / 512.0
    T = 1024.0
    N_gates = 9.0
    denom = (C_SI**2 / lam_rec) * (S / (T * N_gates))
    return a0_target / denom if denom > 0 else 0.0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Linear growth with ILG kernel (canonical schedule).')
    parser.add_argument('--kappa', type=float, default=None, help='Dimensionless geometric factor κ. If omitted, chosen to give a0≈1.2e-10 m/s^2.')
    parser.add_argument('--a0-target', type=float, default=1.2e-10, help='Target a0 used to infer κ when --kappa is not provided.')
    parser.add_argument('--ks', type=str, default='0.01,0.1,0.2', help='Comma-separated k values in h/Mpc')
    parser.add_argument('--a-start', type=float, default=1e-3)
    parser.add_argument('--a-end', type=float, default=1.0)
    parser.add_argument('--steps', type=int, default=400)
    parser.add_argument('--beta', type=float, default=None, help='Override scale proxy factor in a_char. If omitted, uses gating-derived β_gates=(T*N_gates)/S.')
    parser.add_argument('--write-json', type=str, default=None, help='If set, write demo JSON to this path (e.g., ../docs/demo_results.json).')
    parser.add_argument('--normalise', action='store_true', help='Report growth normalised to LCDM at a_end (ratios ~1).')
    args = parser.parse_args()

    if args.kappa is None:
        kappa = kappa_for_target_a0(args.a0_target)
        kappa_note = f'inferred κ for a0_target={args.a0_target:g}'
    else:
        kappa = args.kappa
        kappa_note = 'user κ'

    a0 = compute_a0_from_kappa(kappa)
    # gating-derived beta: β_gates = (T * N_gates) / S
    S = 489.0/512.0
    T = 1024.0
    N_gates = 9.0
    beta_gates = (T * N_gates) / S
    beta = args.beta if args.beta is not None else beta_gates

    ks = [float(s) for s in args.ks.split(',') if s]
    results = []
    for k in ks:
        D_std = integrate_growth(a_start=args.a_start, a_end=args.a_end, k_hmpc=k, a0=0.0, N=args.steps, beta=beta)
        D_ilg = integrate_growth(a_start=args.a_start, a_end=args.a_end, k_hmpc=k, a0=a0, N=args.steps, beta=beta)
        if args.normalise and D_std != 0.0:
            Dn_std = 1.0
            Dn_ilg = D_ilg / D_std
        else:
            Dn_std = D_std
            Dn_ilg = D_ilg
        results.append({
            'k': k,
            'D_LCDM': Dn_std,
            'D_ILG': Dn_ilg,
            'ratio': (Dn_ilg / Dn_std) if Dn_std != 0 else float('nan')
        })

    print(f"κ = {kappa:.3e}  ({kappa_note});  a0 = {a0:.6e} m/s^2;  β = {beta:.3f} (gating default={beta_gates:.3f})")
    for r in results:
        print(f"k={r['k']:5.2f}  D_LCDM={r['D_LCDM']:.6f}  D_ILG={r['D_ILG']:.6f}  ratio={r['ratio']:.5f}")

    if args.write_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.write_json)), exist_ok=True)
        # Also compute a small grid over (a,k) for ILG/LCDM growth ratio
        grid = []
        for a in [0.5, 0.7, 1.0]:
            for k in [0.01, 0.05, 0.1, 0.2]:
                D_std = integrate_growth(a_start=1e-3, a_end=a, k_hmpc=k, a0=0.0, N=args.steps, beta=beta)
                D_ilg = integrate_growth(a_start=1e-3, a_end=a, k_hmpc=k, a0=a0, N=args.steps, beta=beta)
                ratio = (D_ilg / D_std) if D_std != 0 else float('nan')
                z = (1.0 / a) - 1.0 if a > 0 else float('inf')
                grid.append({'a': a, 'z': z, 'k': k, 'ratio': ratio})
        payload = {
            'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'ilg': {
                'blocked': 46,
                'S': 489/512,
                'beta': beta,
                'note': 'canonical schedule; κ note: ' + kappa_note,
            },
            'growth': results,
            'grid': grid
        }
        with open(args.write_json, 'w') as f:
            json.dump(payload, f, indent=2)
        print(f"Wrote demo JSON to {args.write_json}")
