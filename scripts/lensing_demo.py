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
    k_com_mpc = k_hmpc * cosmo.h  # 1/Mpc
    k_com_si = k_com_mpc / MPC_TO_M  # 1/m
    return k_com_si / a  # physical 1/m


def a_char(a, k_hmpc, cosmo: Cosmo, beta=1.0):
    kp = k_phys(a, k_hmpc, cosmo)
    return beta * (a * H(a, cosmo))**2 / max(kp, 1e-30)


def compute_lambda_rec():
    HBAR = 1.054_571_817e-34  # J s
    G_SI = 6.674_30e-11       # m^3 kg^-1 s^-2
    C_SI = 299_792_458.0      # m s^-1
    return math.sqrt(HBAR * G_SI / (C_SI**3))


def compute_a0_from_kappa(kappa: float) -> float:
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


def mu_eff(a, k_hmpc, a0, cosmo: Cosmo, beta=1.0):
    ach = a_char(a, k_hmpc, cosmo, beta)
    x = a0 / max(ach, 1e-30)
    return 1.0 + x / (1.0 + x)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lensing Σ(a,k)=μ(a,k) with ILG (canonical schedule).')
    parser.add_argument('--kappa', type=float, default=None, help='Dimensionless geometric factor κ. If omitted, inferred from a0-target.')
    parser.add_argument('--a0-target', type=float, default=1.2e-10, help='Target a0 used to infer κ when --kappa is not provided.')
    parser.add_argument('--ks', type=str, default='0.01,0.1,0.2', help='Comma-separated k values in h/Mpc')
    parser.add_argument('--a', type=float, default=1.0, help='Scale factor at which to report Σ (default today).')
    parser.add_argument('--beta', type=float, default=None, help='Override scale proxy β in a_char. If omitted, uses gating-derived β_gates=(T*N_gates)/S.')
    parser.add_argument('--write-json', type=str, default=None, help='If set, write demo JSON to this path (e.g., ../docs/lensing_results.json).')
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

    cosmo = Cosmo()
    ks = [float(s) for s in args.ks.split(',') if s]
    rows = []
    for k in ks:
        mu = mu_eff(args.a, k, a0, cosmo, beta)
        Sigma = mu  # Σ(a,k)=μ(a,k) when Φ=Ψ
        z = (1.0 / args.a) - 1.0 if args.a > 0 else float('inf')
        rows.append({'k': k, 'a': args.a, 'z': z, 'Sigma': Sigma})

    print(f"κ = {kappa:.3e}  ({kappa_note});  a0 = {a0:.6e} m/s^2;  β = {beta:.3f} (gating default={beta_gates:.3f}) at a={args.a}")
    for r in rows:
        print(f"k={r['k']:5.2f}  Sigma={r['Sigma']:.6f}")

    if args.write_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.write_json)), exist_ok=True)
        # Also build a small grid over a and k to illustrate scale dependence
        grid = []
        for a in [0.5, 0.7, 1.0]:
            for k in [0.01, 0.05, 0.1, 0.2]:
                mu = mu_eff(a, k, a0, cosmo, beta)
                z = (1.0 / a) - 1.0 if a > 0 else float('inf')
                grid.append({'a': a, 'z': z, 'k': k, 'Sigma': mu})
        payload = {
            'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'ilg': {
                'blocked': 46,
                'S': 489/512,
                'beta': beta,
                'note': 'canonical schedule; κ note: ' + kappa_note,
            },
            'lensing': rows,
            'grid': grid
        }
        with open(args.write_json, 'w') as f:
            json.dump(payload, f, indent=2)
        print(f"Wrote lensing JSON to {args.write_json}")


