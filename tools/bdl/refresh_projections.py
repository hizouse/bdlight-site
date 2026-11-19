"""Refresh every page that uses BDL projections from a new bdl_projections_2027.csv, in one pass:
  scoresheet_projections.html  BDL OBP/SLG/OPS, Blend, Δ OPS, Rk
  scoresheet.html              OBP/SLG/OPS (blend), Adj OPS, VORP 20, Rk, Pos Rk   (replacement levels recomputed)
  scoresheet_ft_hitters.html   same as Rankings (row order kept: PIN/PROT arrays are indexed by row)
  scoresheet_ft.html           FT poach board hitter values/bands, via rebuild_board.py
Steamer600 numbers on the pages are left as they are.
usage: python refresh_projections.py SITE_DIR NEW_proj2027_raw.pkl "Nov 18" [OLD_proj2027_raw.pkl]
BDL values = BDL_OBP/SLG from the BDL pipeline's data/proj2027_raw.pkl (all hitters, not just the exported CSV's), shifted to Steamer's
league level (PA-weighted over Steamer 350+ PA), as on the site since Nov 16.
Matching: page rows -> MLBAM id through the values the pages were built from (tools/bdl/bdl_site_values.csv, or OLD raw pkl for the
first run), by name and BDL OBP/SLG. Afterward tools/bdl/bdl_site_values.csv holds the new values for the next refresh."""
import re, json, sys, os, shutil, unicodedata, subprocess, numpy as np, pandas as pd
SITE, NEW, DAY = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__)); VALS = f'{HERE}/bdl_site_values.csv'
norm = lambda s: re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())
def cd(f):
    h = open(f'{SITE}/{f}').read()
    mc = re.search(r'const C=(\[.*?\]);\n', h, re.S); md = re.search(r'const D=(\[.*?\]);\n', h, re.S)
    return h, json.loads(mc.group(1)), json.loads(md.group(1)), md
def shifted(f):
    raw = pd.read_pickle(f); q = raw[raw.pPA >= 350]
    so = np.average(q.pOBP - q.BDL_OBP, weights=q.pPA); ss = np.average(q.pSLG - q.BDL_SLG, weights=q.pPA)
    return pd.DataFrame({'mlbam': raw.mlbam.astype(int), 'Player': raw.PlayerName.fillna(''), 'OBP': (raw.BDL_OBP + so).round(3), 'SLG': (raw.BDL_SLG + ss).round(3)}).dropna()
old = shifted(sys.argv[4]) if len(sys.argv) > 4 else pd.read_csv(VALS); newv = shifted(NEW); new = newv.set_index('mlbam')
old['k'] = old.Player.map(norm)
# ---------- Projections page
h, C, D, md = cd('scoresheet_projections.html'); ix = {c['n']: i for i, c in enumerate(C)}
proj = {}; nomatch = []; moved = []
for r in D:
    nm, tm = r[ix['Player']], r[ix['Team']] or ''
    if r[ix['BDL OBP']] is None:   # no BDL line: blend = Steamer, unchanged
        proj[(nm, tm)] = (r[ix['Blend OBP']], r[ix['Blend SLG']]); continue
    c = old[(old.k == norm(nm)) & np.isclose(old.OBP, r[ix['BDL OBP']]) & np.isclose(old.SLG, r[ix['BDL SLG']])]
    if len(c) > 1: print('ambiguous', nm, c.mlbam.tolist())
    if len(c) != 1 or c.mlbam.iloc[0] not in new.index: nomatch.append(nm); proj[(nm, tm)] = (r[ix['Blend OBP']], r[ix['Blend SLG']]); continue
    n = new.loc[c.mlbam.iloc[0]]; bo, bs = round(float(n.OBP), 3), round(float(n.SLG), 3)
    moved.append((nm, round(bo + bs - r[ix['BDL OPS']], 3)))
    so, ss = r[ix['Stmr OBP']], r[ix['Stmr SLG']]
    r[ix['BDL OBP']], r[ix['BDL SLG']], r[ix['BDL OPS']] = bo, bs, round(bo + bs, 3)
    lo, ls = round((so + bo) / 2, 3), round((ss + bs) / 2, 3)
    r[ix['Blend OBP']], r[ix['Blend SLG']], r[ix['Blend OPS']] = lo, ls, round(lo + ls, 3)
    r[ix['Δ OPS']] = round(r[ix['Blend OPS']] - r[ix['Stmr OPS']], 3)
    proj[(nm, tm)] = (lo, ls)
assert not nomatch, nomatch
D.sort(key=lambda r: -r[ix['Blend OPS']]); [r.__setitem__(ix['Rk'], i + 1) for i, r in enumerate(D)]
h = h[:md.start(1)] + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + h[md.end(1):]
h = re.sub(r'Built Nov \d+, 2026', f'Built {DAY}, 2026', h)
open(f'{SITE}/scoresheet_projections.html', 'w').write(h)
mv = pd.DataFrame(moved, columns=['Player', 'dBDL_OPS'])
print(f'projections: {len(D)} rows, BDL OPS moved mean |%.4f| max %+.3f / %+.3f' % (mv.dBDL_OPS.abs().mean(), mv.dBDL_OPS.min(), mv.dBDL_OPS.max()))
# ---------- Rankings + FT Hitters
for f in ('scoresheet.html', 'scoresheet_ft_hitters.html'):
    h, C, D, md = cd(f); ix = {c['n']: i for i, c in enumerate(C)}; bad = []
    for r in D:
        pos, nm = r[ix['Player']].split(' ', 1); k = (nm, r[ix['Team']] or '')
        if k not in proj: bad.append(k); continue
        lo, ls = proj[k]; r[ix['OBP']] = lo; r[ix['SLG']] = ls; r[ix['OPS']] = round(lo + ls, 3)
        r[ix['Adj OPS']] = round(r[ix['OPS']] + (r[ix['SB adj']] or 0) + (r[ix['Def adj']] or 0), 3)
    assert not bad, (f, bad[:5])
    rep = {}
    for p in ('C', '1B', '2B', '3B', 'SS', 'OF'):
        v = sorted((r[ix['Adj OPS']] for r in D if r[ix['Pos']] == p), reverse=True); n = 61 if p == 'OF' else 21; rep[p] = v[min(n, len(v)) - 1]
    rep['DH'] = rep['1B']
    for r in D: r[ix['VORP 20']] = round(r[ix['Adj OPS']] - rep[r[ix['Pos']]], 3)
    pc = {}
    for i, r in enumerate(sorted(D, key=lambda r: -r[ix['Adj OPS']])):
        r[ix['Rk']] = i + 1; pc[r[ix['Pos']]] = pc.get(r[ix['Pos']], 0) + 1; r[ix['Pos Rk']] = pc[r[ix['Pos']]]
    h = h[:md.start(1)] + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + h[md.end(1):]
    h = re.sub(r'Rankings built Nov \d+, 2026', f'Rankings built {DAY}, 2026', h); h = re.sub(r'Built Nov \d+, 2026', f'Built {DAY}, 2026', h)
    open(f'{SITE}/{f}', 'w').write(h)
    print(f, len(D), 'rows; replacement Adj OPS', {p: round(v, 3) for p, v in rep.items()})
# ---------- FT board
subprocess.run([sys.executable, f'{HERE}/rebuild_board.py', SITE, DAY], check=True)
newv.to_csv(VALS, index=False)
