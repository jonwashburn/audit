#!/usr/bin/env python3
"""
Toy discrete divergence theorem check with spatially varying w on a 2D grid.

We define Phi(i,j) = i^2 + j^2 and w(i,j) = 1 / (1 + a * (i^2 + j^2)).
Using a finite-volume style stencil, we compute the discrete divergence
  div( w * grad Phi )
in conservative form via face fluxes, and verify that the sum over interior
cells equals the net flux through the domain boundary (discrete divergence theorem).

Outputs JSON with pass/fail and max absolute residual between interior sum
and boundary flux.
"""
import json
from datetime import datetime


def build_fields(nx=33, ny=33, spacing=1.0, a=1e-4):
    phi = [[(i*spacing)**2 + (j*spacing)**2 for i in range(nx)] for j in range(ny)]
    w = [[1.0 / (1.0 + a * ((i*spacing)**2 + (j*spacing)**2)) for i in range(nx)] for j in range(ny)]
    return phi, w


def face_avg(a, b):
    return 0.5 * (a + b)


def divergence_and_boundary_flux(phi, w, spacing=1.0):
    ny = len(phi)
    nx = len(phi[0])
    h = spacing

    # Fluxes at faces (centered)
    def grad_x(i_half, j):
        # i_half is between i and i+1; i in [0, nx-2]
        i = i_half
        return (phi[j][i+1] - phi[j][i]) / h

    def grad_y(i, j_half):
        # j_half is between j and j+1; j in [0, ny-2]
        j = j_half
        return (phi[j+1][i] - phi[j][i]) / h

    def w_x(i_half, j):
        i = i_half
        return face_avg(w[j][i], w[j][i+1])

    def w_y(i, j_half):
        j = j_half
        return face_avg(w[j][i], w[j+1][i])

    # Interior sum of divergence via flux differences
    sum_div = 0.0
    for j in range(1, ny-1):
        for i in range(1, nx-1):
            fxR = w_x(i, j) * grad_x(i, j)
            fxL = w_x(i-1, j) * grad_x(i-1, j)
            fyT = w_y(i, j) * grad_y(i, j)
            fyB = w_y(i, j-1) * grad_y(i, j-1)
            div_ij = (fxR - fxL + fyT - fyB) / h
            sum_div += div_ij

    # Boundary flux (outward normal): sum face fluxes at domain boundary
    flux_out = 0.0
    # Left boundary (i=0), normal = (-1,0), outward flux = - w grad_x at i-1/2
    i = 0
    for j in range(0, ny):
        if j == 0 or j == ny-1:
            continue  # corners counted on edges below
        gxl = (phi[j][i] - phi[j][i+1]) / h  # one-sided outward diff
        wl = w_x(i, j)  # use face between 0 and 1
        flux_out += wl * gxl
    # Right boundary (i=nx-1), normal = (+1,0)
    i = nx-2
    for j in range(0, ny):
        if j == 0 or j == ny-1:
            continue
        gxr = (phi[j][i+1] - phi[j][i]) / h
        wr = w_x(i, j)
        flux_out += wr * gxr
    # Bottom boundary (j=0), normal = (0,-1)
    j = 0
    for i in range(0, nx):
        if i == 0 or i == nx-1:
            continue
        gyb = (phi[j][i] - phi[j+1][i]) / h
        wb = w_y(i, j)
        flux_out += wb * gyb
    # Top boundary (j=ny-1), normal = (0,+1)
    j = ny-2
    for i in range(0, nx):
        if i == 0 or i == nx-1:
            continue
        gyT = (phi[j+1][i] - phi[j][i]) / h
        wT = w_y(i, j)
        flux_out += wT * gyT

    return sum_div, flux_out


def run_check(nx=33, ny=33, spacing=1.0, a=1e-4, tol=1e-8):
    phi, w = build_fields(nx, ny, spacing, a)
    sum_div, flux_out = divergence_and_boundary_flux(phi, w, spacing)
    resid = abs(sum_div - flux_out)
    return {
        'grid': f'{nx}x{ny}',
        'spacing': spacing,
        'a_param': a,
        'sum_div_interior': sum_div,
        'flux_out_boundary': flux_out,
        'abs_residual': resid,
        'passed': resid <= tol,
        'note': 'Discrete divergence theorem: interior sum equals boundary flux (varying w).'
    }


if __name__ == '__main__':
    result = run_check()
    payload = {
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'conservation_check_varying': result,
    }
    out_path = 'docs/conservation_check_varying.json'
    with open(out_path, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f'Wrote {out_path}: passed={result["passed"]}, |sum-div - flux|={result["abs_residual"]:.3e}')


