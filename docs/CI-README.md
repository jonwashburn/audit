# Audit CI Harness — How to Run and What It Checks

This repository includes a tiny, dependency‑free Python harness that runs the core validation checks and writes a unified JSON status the website can stream.

## Prerequisites
- Python 3.9+ (tested on 3.10+)
- No external packages required

## Quick start (one command)
```bash
python3 scripts/ci_status.py
```
This writes `docs/ci_status.json` with an overall pass/fail summary and per‑check results.

## Individual checks (what runs under the hood)

1) Gating S (parity‑gate schedule)
   - Script: `scripts/ilg_gates_check.py`
   - Asserts: `|B| = 46` blocked ticks and `S = 489/512 ≈ 0.955078125`
   - Why it matters: Fixes the suppression from the 1024‑tick breath; reused by growth, lensing, and g−2 without reweighting

2) Growth demo JSON
   - Script: `scripts/linear_growth_demo.py --normalise --write-json docs/demo_results.json`
   - Computes D and D/ΛCDM using the same μ as lensing; **a0** is derived from `S`, `T=1024`, `N_gates=9`; **β** is fixed by gates: `β=(T·N_gates)/S`

3) Lensing demo JSON
   - Script: `scripts/lensing_demo.py --write-json docs/lensing_results.json`
   - Computes Σ(a,k)=μ(a,k) with the same μ and canonical parameters as growth

4) Conservation checks (discrete divergence form)
   - Constant‑w Laplacian (2D): `scripts/conservation_check.py` → `docs/conservation_check.json`
   - Varying‑w divergence theorem (2D): `scripts/conservation_check_varying_w.py` → `docs/conservation_check_varying.json`
   - 3D constant‑w Laplacian & varying‑w divergence theorem: `scripts/conservation_check_3d.py` → `docs/conservation_check_3d.json`
   - These confirm the conservative face‑flux stencil matches the continuous divergence form and satisfies a discrete divergence theorem on toy fields

## Unified status JSON
After running `ci_status.py`, the website audit page reads:
- `docs/ci_status.json` (overall badge)
- `docs/lensing_results.json` and `docs/demo_results.json` (tables)
- `docs/conservation_check_varying.json` and `docs/conservation_check_3d.json` (conservation badges)

## Expected outcomes (pass criteria)
- Gates: `|B|=46` and `S=489/512`
- Growth/Lensing JSONs exist and parse correctly
- Conservation (2D/3D): pass=True with small residuals (machine‑precision for constant‑w Laplacian; ~1e−12–1e−8 for divergence theorem)

## Notes
- No tuning: **a0** and **β** are derived from the canonical gate schedule and breath structure; the same μ is reused across growth and lensing.
- See the Study Guide for derivations and acceptance checks.
