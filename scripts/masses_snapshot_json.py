#!/usr/bin/env python3
"""
Write docs/masses_snapshot.json with the current parameter-free snapshot
memorialized from the AI v21 TeX note (particle-masses-ai.tex).

This is a static, explicit snapshot to make the website render predictable,
and to let CI validate presence/shape without requiring TeX parsing.
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def main():
    data = {
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'charged_leptons': {
            'rungs': {'e': 0, 'mu': 11, 'tau': 17},
            'deltas_pct': {
                'mu_over_e': +0.278,
                'tau_over_mu': -0.278,
                'tau_over_e': +0.006,
            },
            'version': 'v21',
        },
        'quarks': {
            'down': {
                'deltas_pct': {
                    's_over_d': +0.320,
                    'b_over_s': -0.081,
                    'b_over_d': +0.249,
                },
            },
            'up': {
                'deltas_pct': {
                    'c_over_u': -0.211,
                    't_over_c': +0.003,
                    't_over_u': -0.205,
                },
            },
            'version': 'v15',
        },
        'bosons': {
            'deltas_pct': {
                'Z_over_W': -0.104,
                'H_over_Z': +0.020,
                'H_over_W': -0.090,
            },
            'version': 'v16b',
        },
        'ckm': {
            'V': [
                [0.9743, 0.2254, 0.0036],
                [0.2253, 0.9734, 0.0412],
                [0.0086, 0.0404, 0.9991],
            ],
            'lambda': 0.225368,
            'A': 0.812,
            'rho_bar': 0.120,
            'eta_bar': 0.371,
            'alpha_deg': 85.1,
            'beta_deg': 23.1,
            'gamma_deg': 71.8,
            'J': 3.179339e-5,
            'version': 'v19',
        },
        'pmns': {
            'theta12_deg': 33.24,
            'theta23_deg': 47.16,
            'theta13_deg': 7.72,
            'delta_CP_deg': -89.7,
            'J_CP': -3.20e-2,
            'version': 'v18',
        },
        'neutrinos': {
            'ordering': 'NO',
            'rungs': [7, 9, 12],
            'masses_meV': [2.0806, 9.0225, 49.427],
            'sum_mnu_meV': 60.530,
            'delta_m21_sq_eV2': 7.71e-5,
            'delta_m31_sq_eV2': 2.44e-3,
            'm_beta_meV': 8.461,
            'dirac': True,
            'version': 'v21',
        },
        'notes': 'Parameter-free phi-sheet and ledger-locked rungs; no sector-specific knobs (AI snapshot v21).',
    }

    DOCS.mkdir(parents=True, exist_ok=True)
    out_path = DOCS / 'masses_snapshot.json'
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'Wrote {out_path}')


if __name__ == '__main__':
    main()


