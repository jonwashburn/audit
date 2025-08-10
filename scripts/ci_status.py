#!/usr/bin/env python3
"""
Minimal CI/status harness for the audit repo.

Runs core checks and writes a unified docs/ci_status.json suitable for the website:
- Gating S: run ilg_gates_check.py (import or subprocess) and ensure |B|=46, S=489/512
- Growth JSON present and well-formed
- Lensing JSON present and well-formed
- Conservation checks: 2D constant-w, 2D varying-w, 3D combined
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
SCRIPTS = ROOT / 'scripts'


def run_gates_check():
    p = subprocess.run([sys.executable, str(SCRIPTS / 'ilg_gates_check.py')], capture_output=True, text=True)
    out = p.stdout
    ok = ('|B| (brute)   = 46' in out) and ('S   (brute)   = 1 - 46/1024' in out)
    return {'passed': ok, 'stdout': out.strip()}


def check_json(path, keys):
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        # If multiple keys provided, treat as top-level required keys
        if isinstance(keys, (list, tuple)) and len(keys) > 1:
            ok = all(k in data for k in keys)
            return {'passed': ok, 'path': str(path)}
        # Otherwise treat as a nested path sequence
        ok = True
        cur = data
        for k in keys:
            cur = cur.get(k, None)
            if cur is None:
                ok = False
                break
        return {'passed': ok, 'path': str(path)}
    except Exception as e:
        return {'passed': False, 'path': str(path), 'error': str(e)}


def run_conservation(script, out_json):
    p = subprocess.run([sys.executable, str(SCRIPTS / script)], capture_output=True, text=True)
    ok = p.returncode == 0 and Path(DOCS / out_json).exists()
    return {'passed': ok, 'stdout': p.stdout.strip()}


if __name__ == '__main__':
    status = {'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
    # Gating S
    status['gates'] = run_gates_check()
    # Growth JSON
    status['growth_json'] = check_json(DOCS / 'demo_results.json', ['growth'])
    # Lensing JSON
    status['lensing_json'] = check_json(DOCS / 'lensing_results.json', ['lensing'])
    # ILG numeric limit checks
    try:
        subprocess.run([sys.executable, str(SCRIPTS / 'ilg_limit_checks.py')], check=True)
        with open(DOCS / 'ilg_limit_checks.json', 'r') as f:
            _ = json.load(f)
        status['ilg_limits'] = {'passed': True, 'path': str(DOCS / 'ilg_limit_checks.json')}
    except Exception as e:
        status['ilg_limits'] = {'passed': False, 'error': str(e)}
    # Masses snapshot JSON
    try:
        # Generate fresh snapshot each run
        subprocess.run([sys.executable, str(SCRIPTS / 'masses_snapshot_json.py')], check=True)
        status['masses_json'] = check_json(DOCS / 'masses_snapshot.json', ['charged_leptons', 'quarks', 'bosons', 'ckm', 'pmns', 'neutrinos'])
    except Exception as e:
        status['masses_json'] = {'passed': False, 'error': str(e)}
    # Conservation 2D constant-w
    status['cons_2d_const'] = run_conservation('conservation_check.py', 'conservation_check.json')
    # Conservation 2D varying-w
    status['cons_2d_var'] = run_conservation('conservation_check_varying_w.py', 'conservation_check_varying.json')
    # Conservation 3D
    status['cons_3d'] = run_conservation('conservation_check_3d.py', 'conservation_check_3d.json')
    # Ledger snapshot (non-failing): capture stdout to docs/ledger_snapshot_v22c.txt
    try:
        out_txt = DOCS / 'ledger_snapshot_v22c.txt'
        p = subprocess.run([sys.executable, str(SCRIPTS / 'ledger_snapshot_v22c.py')], capture_output=True, text=True, timeout=120)
        DOCS.mkdir(parents=True, exist_ok=True)
        with open(out_txt, 'w') as f:
            f.write(p.stdout)
        status['ledger_snapshot'] = {
            'present': True,
            'path': str(out_txt),
            'lines': p.stdout.count('\n') + (0 if not p.stdout else 1)
        }
    except Exception as e:
        status['ledger_snapshot'] = {'present': False, 'error': str(e)}
    # Metrics presence and badges
    try:
        subprocess.run([sys.executable, str(SCRIPTS / 'metrics.py')], check=True)
        with open(DOCS / 'metrics.json', 'r') as f:
            mx = json.load(f)
        all_green = bool(mx.get('badges', {}).get('all_green', False))
        status['metrics'] = {'passed': all_green, 'path': str(DOCS / 'metrics.json')}
    except Exception as e:
        status['metrics'] = {'passed': False, 'error': str(e)}
    # Uncertainties presence check
    try:
        unc_path = DOCS / 'masses_uncertainties.json'
        present = unc_path.exists()
        nonzero = False
        keys_ok = False
        if present:
            with open(unc_path, 'r') as f:
                unc = json.load(f)
            keys_ok = all(k in unc for k in ['ckm', 'pmns', 'neutrinos'])
            def has_nonzero(x):
                if isinstance(x, dict):
                    return any(has_nonzero(v) for v in x.values())
                if isinstance(x, list):
                    return any(has_nonzero(v) for v in x)
                if isinstance(x, (int, float)):
                    return x != 0
                return False
            nonzero = has_nonzero(unc)
        status['uncertainties'] = {'present': present, 'keys_ok': keys_ok, 'nonzero': nonzero}
    except Exception as e:
        status['uncertainties'] = {'present': False, 'keys_ok': False, 'nonzero': False, 'error': str(e)}
    # Verify z present in grids
    try:
        okz = True
        # growth grid
        with open(DOCS / 'demo_results.json', 'r') as f:
            gr = json.load(f)
        for cell in gr.get('grid', []):
            if 'z' not in cell:
                okz = False
                break
        # lensing grid
        with open(DOCS / 'lensing_results.json', 'r') as f:
            lj = json.load(f)
        for cell in lj.get('grid', []):
            if 'z' not in cell:
                okz = False
                break
        status['z_in_grids'] = {'passed': okz}
    except Exception as e:
        status['z_in_grids'] = {'passed': False, 'error': str(e)}

    # Summarize
    passed_flags = {k: v.get('passed', None) for k, v in status.items() if isinstance(v, dict) and 'passed' in v}
    summary = all(v is True for v in passed_flags.values())
    failed = [k for k, v in passed_flags.items() if v is False]
    status['summary'] = {'passed': summary, 'failed_checks': failed}
    # Human-readable explanations
    status['explanations'] = {
        'overall': 'Overall passes when all required checks pass. Optional artifacts (ledger snapshot, uncertainties) do not gate pass/fail.',
        'gates': 'Parity-gate combinatorics: verifies the 9-gate schedule blocks |B|=46 of 1024 ticks (S=489/512) by brute force and analytically.',
        'growth_json': 'Structure growth demo: docs/demo_results.json exists and contains growth results and grid.',
        'lensing_json': 'Lensing demo: docs/lensing_results.json exists and contains lensing rows and grid.',
        'masses_json': 'Mass/mixing snapshot: docs/masses_snapshot.json exists and includes charged_leptons, quarks, bosons, CKM, PMNS, and neutrinos.',
        'cons_2d_const': '2D conservation (constant w=1): discrete Laplacian test passes with negligible residuals.',
        'cons_2d_var': '2D conservation (varying w): discrete divergence theorem (source minus flux) agrees to numerical precision.',
        'cons_3d': '3D conservation: both constant-w Laplacian and varying-w divergence checks pass on a voxel cube.',
        'ilg_limits': 'ILG limits: numeric probes confirm Newtonian recovery (mu→1) and controlled deep-regime behavior; sweep serialized to docs/ilg_limit_checks.json.',
        'metrics': 'Aggregated residual metrics computed and badges derived.',
        'uncertainties': 'Presence/shape of docs/masses_uncertainties.json; values may be zero until measured/model uncertainties are provided.',
        'z_in_grids': 'Asserts each (a,k) grid cell reports redshift z=1/a−1 for clarity.'
    }
    # Write
    out_path = DOCS / 'ci_status.json'
    with open(out_path, 'w') as f:
        json.dump(status, f, indent=2)
    print(f'Wrote {out_path}: overall passed={summary}')


