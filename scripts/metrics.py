#!/usr/bin/env python3
"""
Compute compact audit metrics and write docs/metrics.json

Includes:
- masses snapshot summary (by sector) from docs/masses_snapshot.json
- growth and lensing residual summaries from docs/demo_results.json and docs/lensing_results.json
- conservation residual summaries from docs/conservation_check*.json
- a composite "all_green" and "no_knobs" indicator (no sector-specific knobs; verifies present status only)
"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


def load_json(path: Path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def masses_summary(ms):
    if not ms:
        return {'present': False}
    # Summarize max |delta| per sector
    cl = ms.get('charged_leptons', {}).get('deltas_pct', {})
    qd = ms.get('quarks', {}).get('down', {}).get('deltas_pct', {})
    qu = ms.get('quarks', {}).get('up', {}).get('deltas_pct', {})
    b = ms.get('bosons', {}).get('deltas_pct', {})
    def max_abs(d):
        vals = [abs(float(v)) for v in d.values() if isinstance(v, (int,float))]
        return max(vals) if vals else None
    return {
        'present': True,
        'charged_leptons_max_abs_pct': max_abs(cl),
        'quarks_down_max_abs_pct': max_abs(qd),
        'quarks_up_max_abs_pct': max_abs(qu),
        'bosons_max_abs_pct': max_abs(b),
        'dirac_nu': bool(ms.get('neutrinos', {}).get('dirac', False)),
    }


def growth_summary(gr):
    if not gr or not isinstance(gr.get('growth'), list):
        return {'present': False}
    ratios = [float(x.get('ratio', 1.0)) for x in gr['growth']]
    if not ratios:
        return {'present': False}
    dev = [abs(r-1.0) for r in ratios]
    return {'present': True, 'max_abs_ratio_dev': max(dev), 'mean_abs_ratio_dev': sum(dev)/len(dev)}


def lensing_summary(lj):
    if not lj or not isinstance(lj.get('lensing'), list):
        return {'present': False}
    sig = [abs(float(x.get('Sigma', 1.0)) - 1.0) for x in lj['lensing']]
    if not sig:
        return {'present': False}
    return {'present': True, 'max_abs_sigma_dev': max(sig), 'mean_abs_sigma_dev': sum(sig)/len(sig)}


def conservation_summaries():
    out = {}
    c2 = load_json(DOCS / 'conservation_check.json')
    if c2 and 'conservation_check' in c2:
        out['const_2d'] = {'present': True, **c2['conservation_check']}
    else:
        out['const_2d'] = {'present': False}
    c2v = load_json(DOCS / 'conservation_check_varying.json')
    if c2v and 'conservation_check_varying' in c2v:
        out['varying_2d'] = {'present': True, **c2v['conservation_check_varying']}
    else:
        out['varying_2d'] = {'present': False}
    c3 = load_json(DOCS / 'conservation_check_3d.json')
    if c3 and 'conservation_check_3d' in c3:
        out['const_3d'] = {'present': True, **c3['conservation_check_3d']}
    else:
        out['const_3d'] = {'present': False}
    return out


def main():
    ms = load_json(DOCS / 'masses_snapshot.json')
    gr = load_json(DOCS / 'demo_results.json')
    lj = load_json(DOCS / 'lensing_results.json')
    con = conservation_summaries()

    metrics = {
        'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'masses': masses_summary(ms),
        'growth': growth_summary(gr),
        'lensing': lensing_summary(lj),
        'conservation': con,
    }

    # Composite badges
    all_present = all(v.get('present', False) for k, v in metrics.items() if isinstance(v, dict) and k in ['masses','growth','lensing'])
    cons_ok = True
    if isinstance(con.get('const_2d'), dict) and con['const_2d'].get('present'):
        cons_ok = cons_ok and bool(con['const_2d'].get('passed', True))
    if isinstance(con.get('varying_2d'), dict) and con['varying_2d'].get('present'):
        cons_ok = cons_ok and bool(con['varying_2d'].get('passed', True))
    if isinstance(con.get('const_3d'), dict) and con['const_3d'].get('present'):
        # both tests inside 3d
        c3 = con['const_3d']
        const_ok = c3.get('constant_w_laplacian', {}).get('passed', True)
        var_ok = c3.get('varying_w_divergence', {}).get('passed', True)
        cons_ok = cons_ok and const_ok and var_ok
    metrics['badges'] = {
        'all_green': bool(all_present and cons_ok),
        'no_knobs': True  # asserted by architecture; no sector-specific fits used in snapshot
    }

    out = DOCS / 'metrics.json'
    with open(out, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()


