"""Put the Steamer600/BDL 50-50 blend on the bdlight.net Scoresheet pages (Projections, Rankings, FT Hitters)."""
import re, json, sys, unicodedata, numpy as np, pandas as pd
SITE = sys.argv[1]; P = '/home/claude/proj'
def cd(f):
    h = open(f'{SITE}/{f}').read()
    mc = re.search(r'const C=(\[.*?\]);\n', h, re.S); md = re.search(r'const D=(\[.*?\]);\n', h, re.S)
    return h, json.loads(mc.group(1)), json.loads(md.group(1)), mc, md
norm = lambda s: re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())
# ---- BDL 2027 on Steamer's level
raw = pd.read_pickle(f'{P}/data/proj2027_raw.pkl'); q = raw[raw.pPA >= 350]
so = np.average(q.pOBP - q.BDL_OBP, weights=q.pPA); ss = np.average(q.pSLG - q.BDL_SLG, weights=q.pPA)
raw['bOBP'] = raw.BDL_OBP + so; raw['bSLG'] = raw.BDL_SLG + ss; bdl = raw.set_index('mlbam')
st = pd.DataFrame(json.load(open(f'{P}/raw/steamer_2027.json')))[['PlayerName', 'Team', 'xMLBAMID', 'OBP', 'SLG', 'PA']].dropna(subset=['xMLBAMID'])
st['mlbam'] = st.xMLBAMID.astype(int); st['k'] = st.PlayerName.map(norm); st['Team'] = st.Team.fillna('')
sv = {y: pd.read_csv(f'{P}/raw/sv_custom_{y}.csv', encoding='utf-8-sig').set_index('player_id') for y in (2025, 2026)}
# ---- Projections page
h, C, D, mc, md = cd('scoresheet_projections.html'); ix = {c['n']: i for i, c in enumerate(C)}
rows = []; miss = []; amb = 0; proj = {}
for r in D:
    nm, tm = r[ix['Player']], r[ix['Team']] or ''
    c = st[st.k == norm(nm)]
    if len(c) > 1:
        c2 = c[c.Team == tm]; c = c2 if len(c2) else c
    if len(c) > 1: amb += 1; c = c.iloc[(c.OBP - r[ix['Stmr OBP']]).abs().argsort()[:1]]
    if len(c) == 0: miss.append(nm); mid = None
    else: mid = int(c.mlbam.iloc[0])
    so_, ss_ = r[ix['Stmr OBP']], r[ix['Stmr SLG']]
    if mid in bdl.index and pd.notna(bdl.loc[mid, 'bOBP']): bo, bs = round(float(bdl.loc[mid, 'bOBP']), 3), round(float(bdl.loc[mid, 'bSLG']), 3)
    else: bo = bs = None; miss.append(nm + ' (no BDL)')
    lo, ls = (round((so_ + bo) / 2, 3), round((ss_ + bs) / 2, 3)) if bo is not None else (so_, ss_)
    g = lambda y, c_: (None if mid not in sv[y].index or pd.isna(sv[y].loc[mid, c_]) else float(sv[y].loc[mid, c_]))
    pa25 = g(2025, 'pa'); pa25 = int(pa25) if pa25 else None
    rows.append([r[0], nm, r[ix['Team']], r[ix['Age']], r[ix['Pos']], so_, ss_, r[ix['Stmr OPS']], bo, bs, None if bo is None else round(bo + bs, 3), lo, ls, round(lo + ls, 3), round(round(lo + ls, 3) - r[ix['Stmr OPS']], 3),
                 r[ix['PA 26']], r[ix['wOBA 26']], r[ix['xwOBA 26']], pa25, g(2025, 'woba') if pa25 else None, g(2025, 'xwoba') if pa25 else None])
    proj[(nm, r[ix['Team']] or '')] = (lo, ls, r[ix['OBP']], r[ix['SLG']], mid, abs(float(c.OBP.iloc[0]) - so_) if len(c) else None)
print('projections rows', len(rows), 'ambiguous', amb, 'missing', miss)
dchk = [(k, v[5]) for k, v in proj.items() if v[5] is not None and v[5] > 0.004]; print('Steamer OBP moved >4 pts since page build:', len(dchk), dchk[:8])
rows.sort(key=lambda r: -r[13]); [r.__setitem__(0, i + 1) for i, r in enumerate(rows)]
col = lambda n, f, t, d='desc', g=False: {"n": n, "f": f, "t": t, "d": d, "g": g}
C2 = [col('Rk', 'int', 'Rank among all hitters by the column you sorted (by Blend OPS when sorting by Rk or a text column)', 'asc'), col('Player', 'txt', 'Player', 'asc'), col('Team', 'txt', 'Steamer team (blank = free agent)', 'asc'),
      col('Age', 'int', '2027 MLB season age (age on June 30, 2027)', 'asc'), col('Pos', 'txt', 'Positions with a line on the Rankings tab', 'asc'),
      col('Stmr OBP', 'f3', 'Steamer600 OBP', g=True), col('Stmr SLG', 'f3', 'Steamer600 SLG'), col('Stmr OPS', 'f3', 'Steamer600 OPS'),
      col('BDL OBP', 'f3', 'BDL projected OBP (FanGraphs + Baseball Savant model, in the projected home park, set to Steamer\'s league level)', g=True), col('BDL SLG', 'f3', 'BDL projected SLG'), col('BDL OPS', 'f3', 'BDL projected OPS'),
      col('Blend OBP', 'f3', 'Average of Steamer600 and BDL OBP; used on the Rankings tab', g=True), col('Blend SLG', 'f3', 'Average of Steamer600 and BDL SLG; used on the Rankings tab'), col('Blend OPS', 'f3', 'Blend OBP + Blend SLG'), col('Δ OPS', 'sz3', 'Blend OPS minus Steamer600 OPS'),
      col('PA 26', 'int', '2026 MLB plate appearances', g=True), col('wOBA 26', 'f3', '2026 wOBA (Baseball Savant)'), col('xwOBA 26', 'f3', '2026 expected wOBA (Baseball Savant)'),
      col('PA 25', 'int', '2025 MLB plate appearances', g=True), col('wOBA 25', 'f3', '2025 wOBA (Baseball Savant)'), col('xwOBA 25', 'f3', '2025 expected wOBA (Baseball Savant)')]
h = h[:md.start(1)] + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + h[md.end(1):]
h = h[:mc.start(1)] + json.dumps(C2, ensure_ascii=False) + h[mc.end(1):]
assert "c.n==='OPS'" in h; h = h.replace("AI=C.findIndex(c=>c.n==='OPS')", "AI=C.findIndex(c=>c.n==='Blend OPS')")
a = h.index('<h1>'); b = h.index('<div class="controls">')
head = ('<h1>Scoresheet 2027 Projections</h1><p class="sub">Steamer600, BDL, and their 50/50 blend · 574 hitters on the Rankings tab</p>\n'
 '<div class="explain"><b>Blend</b> is the average of Steamer600 and BDL, and is what the <a href="scoresheet.html">2027 Rankings</a> use for OBP, SLG, and OPS.<br>'
 '<b>BDL</b> projects next-season OBP and SLG from three years of FanGraphs results and Baseball Savant data (expected stats, exit velocity and barrels, swing decisions and contact, sprint speed), each regressed toward league average by sample size, plus minor-league lines for hitters with little MLB time, age, and the home park. BDL figures are set to Steamer&rsquo;s league level so the two are comparable.<br>'
 '<b>Backtest.</b> Each season from 2019 to 2026 (2020 skipped) was projected using only earlier seasons and graded on hitters with 400+ PA who stayed with their projected team (1,328 hitter-seasons; PA-weighted error in points, projections shifted to the sample average). OPS: BDL 70.0, Steamer 71.9, ZiPS 71.9, blend 69.7. SLG: BDL 50.2, Steamer 52.1, blend 50.2. OBP: BDL 25.5, Steamer 25.7, blend 25.1. BDL&rsquo;s edge is in SLG; on OBP it is about even with Steamer, and Steamer was slightly better in 2026 alone. BDL does not predict the league run level better than Steamer, which is why it borrows Steamer&rsquo;s.<br>'
 '<b>wOBA and xwOBA</b> for 2026 and 2025 are shown for reference. They replace the earlier luck, contact, and young-xwOBA adjustments to Steamer, which BDL now covers.</div>\n')
h = h[:a] + head + h[b:]
f0 = h.index('<footer>'); f1 = h.index('<p class="credit">')
h = h[:f0] + '<footer>Click a header to sort; click again to reverse. Sources: Steamer600 2027 and 2013&ndash;26 preseason Steamer and ZiPS projections (FanGraphs), FanGraphs MLB and minor-league batting 2012&ndash;26, Baseball Savant expected statistics, Statcast leaderboards, sprint speed, and park factors 2015&ndash;26. Built Nov 16, 2026.' + h[f1:]
h = h.replace('<title>Scoresheet 2027 Projections</title>', '<title>Scoresheet 2027 Projections</title>')
open(f'{SITE}/scoresheet_projections.html', 'w').write(h)
# ---- Rankings + FT hitters
for f in ('scoresheet.html', 'scoresheet_ft_hitters.html'):
    h, C, D, mc, md = cd(f); ix = {c['n']: i for i, c in enumerate(C)}; bad = []; chg = []
    for r in D:
        pos, nm = r[ix['Player']].split(' ', 1); k = (nm, r[ix['Team']] or '')
        if k not in proj: bad.append(k); continue
        lo, ls, oo, os_, _, _ = proj[k]
        if abs(oo - r[ix['OBP']]) > 1e-9 or abs(os_ - r[ix['SLG']]) > 1e-9: bad.append(('old mismatch', k))
        chg.append(lo + ls - r[ix['OPS']]); r[ix['OBP']] = lo; r[ix['SLG']] = ls; r[ix['OPS']] = round(lo + ls, 3)
        r[ix['Adj OPS']] = round(r[ix['OPS']] + (r[ix['SB adj']] or 0) + (r[ix['Def adj']] or 0), 3)
    rep = {}
    for p in ('C', '1B', '2B', '3B', 'SS', 'OF'):
        v = sorted((r[ix['Adj OPS']] for r in D if r[ix['Pos']] == p), reverse=True); n = 61 if p == 'OF' else 21; rep[p] = v[min(n, len(v)) - 1]
    rep['DH'] = rep['1B']
    for r in D: r[ix['VORP 20']] = round(r[ix['Adj OPS']] - rep[r[ix['Pos']]], 3)
    D.sort(key=lambda r: -r[ix['VORP 20']]); pc = {}
    o = sorted(D, key=lambda r: -r[ix['Adj OPS']])
    for i, r in enumerate(o): r[ix['Rk']] = i + 1; pc[r[ix['Pos']]] = pc.get(r[ix['Pos']], 0) + 1; r[ix['Pos Rk']] = pc[r[ix['Pos']]]
    for n_, t_ in (('OBP', 'Blend OBP: average of Steamer600 and BDL (see Projections)'), ('SLG', 'Blend SLG: average of Steamer600 and BDL (see Projections)')): C[ix[n_]]['t'] = t_
    C[ix['OPS']]['t'] = re.sub(r'Adjusted Steamer600 OBP and SLG \([^)]*\)', 'Blend of Steamer600 and BDL OBP and SLG (see Projections)', C[ix['OPS']]['t'])
    h = h[:md.start(1)] + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + h[md.end(1):]
    h = h[:mc.start(1)] + json.dumps(C, ensure_ascii=False, separators=(',', ':')) + h[mc.end(1):]
    n0 = h.count('OBP/SLG/OPS are modified Steamer projections.'); h = h.replace('OBP/SLG/OPS are modified Steamer projections.', 'OBP/SLG/OPS are a 50/50 blend of Steamer600 and BDL projections.')
    old = re.search(r'<b>Adj OPS</b> = adjusted Steamer OPS \(Steamer with the luck, contact, and young-xwOBA adjustments on the <a href="scoresheet_projections.html">Projections</a> tab\)', h)
    assert old and n0 == 1, (f, bool(old), n0)
    h = h.replace(old.group(0), '<b>Adj OPS</b> = blend OPS (the average of Steamer600 and BDL on the <a href="scoresheet_projections.html">Projections</a> tab)')
    h = h.replace('Steamer600 2027 projections (FanGraphs), adjusted with 2026 Statcast and Savant expected stats (see Projections)', 'Steamer600 2027 projections (FanGraphs) blended with BDL projections (see Projections)')
    h = re.sub(r'Rankings built Nov \d+, 2026', 'Rankings built Nov 16, 2026', h)
    open(f'{SITE}/{f}', 'w').write(h)
    print(f, len(D), 'unmatched', bad[:5], len(bad), '| OPS change mean %+.4f sd %.4f max %.3f' % (np.mean(chg), np.std(chg), np.max(np.abs(chg))), 'repl', rep, '| leftover old text:', len(re.findall('luck, contact|young-xwOBA|[Aa]djusted Steamer', h)))
