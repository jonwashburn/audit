#!/usr/bin/env python3
"""
Common ILG utilities shared by cosmology demo scripts.

Provides a single source for:
- Cosmology container and background functions E(a), H(a)
- k conversion and a_char proxy
- μ(a,k) = 1 + x/(1+x) with x = a0 / a_char
- a0 from κ (and κ from target a0) using canonical gating geometry
- gating-derived β factor
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Cosmo:
    H0: float = 70.0  # km/s/Mpc
    Omega_m0: float = 0.3
    Omega_L0: float = 0.7
    h: float = 0.7


# Unit helpers
KM_S_MPC_TO_SI = 1000.0 / (3.085677581e22)
MPC_TO_M = 3.085677581e22


def E(a: float, cosmo: Cosmo) -> float:
    return math.sqrt(cosmo.Omega_m0 / a**3 + cosmo.Omega_L0)


def H(a: float, cosmo: Cosmo) -> float:
    return cosmo.H0 * KM_S_MPC_TO_SI * E(a, cosmo)


def k_phys(a: float, k_hmpc: float, cosmo: Cosmo) -> float:
    """k (h/Mpc) → physical wavenumber 1/m at scale factor a."""
    k_com_mpc = k_hmpc * cosmo.h  # 1/Mpc
    k_com_si = k_com_mpc / MPC_TO_M  # 1/m
    return k_com_si / a


def a_char(a: float, k_hmpc: float, cosmo: Cosmo, beta: float = 1.0) -> float:
    """Acceleration scale proxy with gating-derived factor β.

    Dimensionally, a_char ~ (a H)^2 / k_phys.
    """
    kp = k_phys(a, k_hmpc, cosmo)
    return beta * (a * H(a, cosmo))**2 / max(kp, 1e-30)


def mu_eff(a: float, k_hmpc: float, a0: float, cosmo: Cosmo, beta: float = 1.0) -> float:
    ach = a_char(a, k_hmpc, cosmo, beta)
    x = a0 / max(ach, 1e-30)
    # Saturating enhancement in (1,2): 1 + x/(1+x)
    return 1.0 + x / (1.0 + x)


def compute_lambda_rec() -> float:
    """Planck/recognition length λ_rec = sqrt(ħ G / c^3)."""
    HBAR = 1.054_571_817e-34  # J s
    G_SI = 6.674_30e-11       # m^3 kg^-1 s^-2
    C_SI = 299_792_458.0      # m s^-1
    return math.sqrt(HBAR * G_SI / (C_SI**3))


def gating_beta() -> float:
    """β from canonical gating: β = (T_breath * N_gates) / S with T=1024, N=9, S=489/512."""
    S = 489.0 / 512.0
    T = 1024.0
    N_gates = 9.0
    return (T * N_gates) / S


def compute_a0_from_kappa(kappa: float) -> float:
    """a0 from geometric factor κ via canonical capacity scaling."""
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


