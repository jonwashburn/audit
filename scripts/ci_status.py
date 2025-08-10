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
    # Summarize
    summary = all(v.get('passed', False) for k, v in status.items() if isinstance(v, dict) and 'passed' in v)
    status['summary'] = {'passed': summary}
    # Write
    out_path = DOCS / 'ci_status.json'
    with open(out_path, 'w') as f:
        json.dump(status, f, indent=2)
    print(f'Wrote {out_path}: overall passed={summary}')


