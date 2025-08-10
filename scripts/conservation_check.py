#!/usr/bin/env python3
"""
Toy discrete conservation check for ILG modified Poisson in the constant-w limit.

We verify on a 2D grid with unit spacing that the central-difference Laplacian
of Phi(i,j) = i^2 + j^2 is constant (4) at interior nodes when w=1, i.e.
  div( w * grad Phi ) = laplacian Phi = 4.

Outputs a small JSON file with pass/fail and max absolute error across interior nodes.
"""
import json
from datetime import datetime


def laplacian_central(phi):
    """Return central-difference Laplacian on interior nodes of phi (2D list)."""
    ny = len(phi)
    nx = len(phi[0])
    lap = [[0.0]*nx for _ in range(ny)]
    for j in range(1, ny-1):
        for i in range(1, nx-1):
            lap[j][i] = (
                phi[j][i+1] - 2.0*phi[j][i] + phi[j][i-1]
                + phi[j+1][i] - 2.0*phi[j][i] + phi[j-1][i]
            )
    return lap


def run_check(nx=33, ny=33, spacing=1.0, expected=4.0, tol=1e-12):
    # Build Phi(i,j) = i^2 + j^2 with unit spacing
    phi = [[(i*spacing)**2 + (j*spacing)**2 for i in range(nx)] for j in range(ny)]
    lap = laplacian_central(phi)
    max_abs_err = 0.0
    count = 0
    for j in range(1, ny-1):
        for i in range(1, nx-1):
            err = abs(lap[j][i] - expected)
            if err > max_abs_err:
                max_abs_err = err
            count += 1
    passed = max_abs_err <= tol
    return {
        'grid': f'{nx}x{ny}',
        'spacing': spacing,
        'expected': expected,
        'max_abs_err': max_abs_err,
        'count_interior': count,
        'passed': passed,
        'note': 'Central-difference Laplacian of i^2+j^2 with w=1 equals 4 on interior nodes.'
    }


if __name__ == '__main__':
    result = run_check()
    payload = {
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'conservation_check': result,
    }
    # Write alongside other demo artifacts
    out_path = 'docs/conservation_check.json'
    with open(out_path, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f'Wrote {out_path}: passed={result["passed"]}, max_abs_err={result["max_abs_err"]:.3e}')


