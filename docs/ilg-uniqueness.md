### ILG Kernel Uniqueness (Draft)

- Kernel form: w = 1/(1+χ), with load χ ∝ (r^2 a / c^2) · N_gates / Capacity(r)
- Variational principle: minimize ledger action under capacity constraint

Action and constraint
- Minimize A[w] = ∫_shell w |∇Φ|^2 dV
- Subject to per-breath capacity: ∫_shell (1 − w) C(r,a) dV ≤ Λ

Lagrangian and Euler–Lagrange condition
- L = A + λ (∫ (1 − w) C − Λ)
- Stationarity: δL/δw = |∇Φ|^2 − λ C = 0 ⇒ w = 1/(1+χ)
  (after normalization of χ := (C/|∇Φ|^2) and KKT conditions)

Properties and limits
- Low-load: λ→0 ⇒ w→1 (Newtonian)
- High-load: budget binds ⇒ w≈1/χ (deep MOND-like)
- Conservation: divergence form preserved; reduces to Poisson when χ→0
- Uniqueness: convex objective and affine constraint ⇒ unique minimizer

Open items
- Fix explicit C(r,a) from parity-gate combinatorics and breath schedule (nine-gate schedule locked: |B|=46 ⇒ S=489/512)
- Provide spherical solutions and rotation curve fits with fixed a0
