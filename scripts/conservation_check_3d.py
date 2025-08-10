#!/usr/bin/env python3
"""
3D toy conservation checks on a regular voxel grid.

1) Constant-w Laplacian: Φ = x^2 + y^2 + z^2 ⇒ ΔΦ = 6 everywhere.
   Verify central-difference Laplacian equals 6 on interior nodes.

2) Varying-w divergence theorem: w(x,y,z) = 1/(1 + a * r^2), r^2=x^2+y^2+z^2.
   Compute interior sum of div(w ∇Φ) via face flux differences and compare to
   outward boundary flux sum; residual should be ~0.

Outputs JSON with both checks and pass/fail.
"""
import json
from datetime import datetime


def laplacian_central_3d(phi, h=1.0):
    nz = len(phi)
    ny = len(phi[0])
    nx = len(phi[0][0])
    lap = [[[0.0]*nx for _ in range(ny)] for __ in range(nz)]
    inv_h2 = 1.0/(h*h)
    for k in range(1, nz-1):
        for j in range(1, ny-1):
            for i in range(1, nx-1):
                lap[k][j][i] = (
                    (phi[k][j][i+1] - 2.0*phi[k][j][i] + phi[k][j][i-1])
                  + (phi[k][j+1][i] - 2.0*phi[k][j][i] + phi[k][j-1][i])
                  + (phi[k+1][j][i] - 2.0*phi[k][j][i] + phi[k-1][j][i])
                ) * inv_h2
    return lap


def build_phi_w_3d(nx=17, ny=17, nz=17, h=1.0, a=1e-4):
    phi = [[[ (i*h)**2 + (j*h)**2 + (k*h)**2 for i in range(nx)] for j in range(ny)] for k in range(nz)]
    w = [[[ 1.0/(1.0 + a*((i*h)**2 + (j*h)**2 + (k*h)**2)) for i in range(nx)] for j in range(ny)] for k in range(nz)]
    return phi, w


def face_avg(a, b):
    return 0.5*(a+b)


def divergence_sum_and_boundary_flux_3d(phi, w, h=1.0):
    nz = len(phi)
    ny = len(phi[0])
    nx = len(phi[0][0])

    def grad_x(i_half, j, k):
        i = i_half
        return (phi[k][j][i+1] - phi[k][j][i]) / h

    def grad_y(i, j_half, k):
        j = j_half
        return (phi[k][j+1][i] - phi[k][j][i]) / h

    def grad_z(i, j, k_half):
        k = k_half
        return (phi[k+1][j][i] - phi[k][j][i]) / h

    def w_x(i_half, j, k):
        i = i_half
        return face_avg(w[k][j][i], w[k][j][i+1])

    def w_y(i, j_half, k):
        j = j_half
        return face_avg(w[k][j][i], w[k][j+1][i])

    def w_z(i, j, k_half):
        k = k_half
        return face_avg(w[k][j][i], w[k+1][j][i])

    sum_div = 0.0
    for k in range(1, nz-1):
        for j in range(1, ny-1):
            for i in range(1, nx-1):
                fxR = w_x(i, j, k) * grad_x(i, j, k)
                fxL = w_x(i-1, j, k) * grad_x(i-1, j, k)
                fyT = w_y(i, j, k) * grad_y(i, j, k)
                fyB = w_y(i, j-1, k) * grad_y(i, j-1, k)
                fzU = w_z(i, j, k) * grad_z(i, j, k)
                fzD = w_z(i, j, k-1) * grad_z(i, j, k-1)
                div_ijk = (fxR - fxL + fyT - fyB + fzU - fzD) / h
                sum_div += div_ijk

    flux_out = 0.0
    # x-min face (i=0), outward normal (-1,0,0)
    i = 0
    for k in range(nz):
        for j in range(ny):
            if j in (0, ny-1) or k in (0, nz-1):
                continue
            gx = (phi[k][j][i] - phi[k][j][i+1]) / h
            wx = w_x(i, j, k)
            flux_out += wx * gx
    # x-max face (i=nx-1)
    i = nx-2
    for k in range(nz):
        for j in range(ny):
            if j in (0, ny-1) or k in (0, nz-1):
                continue
            gx = (phi[k][j][i+1] - phi[k][j][i]) / h
            wx = w_x(i, j, k)
            flux_out += wx * gx
    # y-min face (j=0)
    j = 0
    for k in range(nz):
        for i in range(nx):
            if i in (0, nx-1) or k in (0, nz-1):
                continue
            gy = (phi[k][j][i] - phi[k][j+1][i]) / h
            wy = w_y(i, j, k)
            flux_out += wy * gy
    # y-max face (j=ny-1)
    j = ny-2
    for k in range(nz):
        for i in range(nx):
            if i in (0, nx-1) or k in (0, nz-1):
                continue
            gy = (phi[k][j+1][i] - phi[k][j][i]) / h
            wy = w_y(i, j, k)
            flux_out += wy * gy
    # z-min face (k=0)
    k = 0
    for j in range(ny):
        for i in range(nx):
            if i in (0, nx-1) or j in (0, ny-1):
                continue
            gz = (phi[k][j][i] - phi[k+1][j][i]) / h
            wz = w_z(i, j, k)
            flux_out += wz * gz
    # z-max face (k=nz-1)
    k = nz-2
    for j in range(ny):
        for i in range(nx):
            if i in (0, nx-1) or j in (0, ny-1):
                continue
            gz = (phi[k+1][j][i] - phi[k][j][i]) / h
            wz = w_z(i, j, k)
            flux_out += wz * gz

    return sum_div, flux_out


def run_checks_3d():
    h = 1.0
    nx = ny = nz = 17
    phi, w = build_phi_w_3d(nx, ny, nz, h, a=1e-4)
    # Constant-w Laplacian (use w=1 via phi only)
    lap = laplacian_central_3d(phi, h)
    max_abs_err = 0.0
    count = 0
    for k in range(1, nz-1):
        for j in range(1, ny-1):
            for i in range(1, nx-1):
                err = abs(lap[k][j][i] - 6.0)
                if err > max_abs_err:
                    max_abs_err = err
                count += 1
    lap_ok = (max_abs_err <= 1e-12)
    # Varying-w divergence theorem
    sum_div, flux_out = divergence_sum_and_boundary_flux_3d(phi, w, h)
    resid = abs(sum_div - flux_out)
    div_ok = (resid <= 1e-8)
    return {
        'constant_w_laplacian': {
            'expected': 6.0,
            'max_abs_err': max_abs_err,
            'count_interior': count,
            'passed': lap_ok
        },
        'varying_w_divergence': {
            'sum_div_interior': sum_div,
            'flux_out_boundary': flux_out,
            'abs_residual': resid,
            'passed': div_ok
        }
    }


if __name__ == '__main__':
    result = run_checks_3d()
    payload = {
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'conservation_check_3d': result,
    }
    out_path = 'docs/conservation_check_3d.json'
    with open(out_path, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {out_path}: Laplacian OK={result['constant_w_laplacian']['passed']}, Varying-w OK={result['varying_w_divergence']['passed']}")


