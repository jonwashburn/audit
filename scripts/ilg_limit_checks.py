#!/usr/bin/env python3
"""
Numerical limit checks for the ILG kernel μ(a,k) using the shared module.

Writes docs/ilg_limit_checks.json with small sanity tests:
- Newtonian limit: μ → 1 at high acceleration scale (a → 1, large k)
- Deep-MOND limit: μ - 1 ≈ x for x = a0/a_char when x ≪ 1 is false; instead we examine x ≫ 1 → μ → 2 from above capped form.
  To connect to empirical deep-MOND scaling, we also report x and 1 + x/(1+x) behaviour across a sweep.
"""
from __future__ import annotations

import json
from pathlib import Path

from ilg_common import Cosmo, mu_eff, compute_a0_from_kappa, kappa_for_target_a0, gating_beta, a_char


def run_checks():
    cosmo = Cosmo()
    beta = gating_beta()
    a0 = compute_a0_from_kappa(kappa_for_target_a0(1.2e-10))
    # Newtonian regime: a=1, large k
    mu_newt = mu_eff(a=1.0, k_hmpc=1.0, a0=a0, cosmo=cosmo, beta=beta)
    # Deep regime: a small, k small
    a_deep = 0.2
    k_deep = 0.005
    mu_deep = mu_eff(a=a_deep, k_hmpc=k_deep, a0=a0, cosmo=cosmo, beta=beta)
    x_deep = a0 / a_char(a_deep, k_deep, cosmo, beta)
    # Sweep a grid to see monotonic approach
    sweep = []
    for a in [0.3, 0.5, 0.7, 1.0]:
        for k in [0.01, 0.05, 0.1, 0.2]:
            x = a0 / a_char(a, k, cosmo, beta)
            sweep.append({'a': a, 'k': k, 'x': x, 'mu': mu_eff(a, k, a0, cosmo, beta)})
    return {
        'newtonian_limit': {'mu_at_a1_k1': mu_newt},
        'deep_limit_probe': {'a': a_deep, 'k': k_deep, 'x': x_deep, 'mu': mu_deep},
        'sweep': sweep,
        'beta': beta,
        'a0': a0,
    }


if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parents[1]
    DOCS = ROOT / 'docs'
    DOCS.mkdir(parents=True, exist_ok=True)
    out = run_checks()
    with open(DOCS / 'ilg_limit_checks.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {DOCS / 'ilg_limit_checks.json'}")


