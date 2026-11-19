"""Build the modelling table: one row per (player, target season) with inputs known before that season.
MiLB park adjustment (on by default; BDL_MILB_PARK=0 to disable) (needs data/milb_pf_map.csv from milb_pf_map.py); BDL_MILB_PARK_SCALE (default 0.5)."""
import numpy as np, pandas as pd, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
LAGS = (1, 2, 3)
H2STATS = ('bb', 'k', 'hr', 'babip', 'iso', 'obp', 'slg', 'woba', 'xwoba', 'ev', 'ev90', 'barrel', 'hardhit', 'la', 'oswing', 'zcontact', 'swstr', 'gb', 'pull')
MILB_PARK = os.environ.get('BDL_MILB_PARK', '1') == '1'   # on by default since Nov 18 2026; 0 = old unadjusted lines
def load(b=None):
    if b is None: b = pd.read_pickle(f'{D}/mlb.pkl')
    b = b[b.position != 'P'].copy()
    b['Team'] = b.Team.replace({'OAK': 'ATH', 'FLA': 'MIA', 'TBD': 'TBR'})
    bip = (b.AB - b.SO - b.HR + b.SF).clip(lower=0); bb = b.GB + b.FB + b.LD
    f = lambda a, c: a.where(a.notna(), c)
    S = {}  # stat -> (value, denominator)
    S['bb'] = ((b.BB - b.IBB) / b.PA, b.PA); S['k'] = (b.SO / b.PA, b.PA); S['hbp'] = (b.HBP / b.PA, b.PA); S['ibb'] = (b.IBB / b.PA, b.PA); S['hr'] = (b.HR / b.PA, b.PA)
    S['babip'] = ((b.H - b.HR) / bip, bip); S['xbh'] = ((b['2B'] + b['3B']) / bip, bip); S['iso'] = ((b['2B'] + 2 * b['3B'] + 3 * b.HR) / b.AB, b.AB)
    S['avg'] = (b.H / b.AB, b.AB); S['obp'] = (b.OBP, b.PA); S['slg'] = (b.SLG, b.AB); S['woba'] = (b.wOBA, b.PA)
    ev = b.Events.where(b.Events > 0)
    S['xwoba'] = (f(b.xwOBA, b.xwoba), b.PA.where(ev.notna())); S['xobp'] = (b.xobp, b.PA.where(ev.notna())); S['xba'] = (f(b.xAVG, b.xba), b.AB.where(ev.notna()))
    S['xslg'] = (f(b.xSLG, b.xslg), b.AB.where(ev.notna())); S['xiso'] = (b.xiso, b.AB.where(ev.notna())); S['xwobacon'] = (b.xwobacon, ev)
    S['ev'] = (b.EV, ev); S['ev90'] = (b.EV90, ev); S['maxev'] = (b.maxEV, ev); S['la'] = (b.LA, ev); S['barrel'] = (b['Barrel%'], ev); S['hardhit'] = (b['HardHit%'], ev)
    S['sweet'] = (b.sweet_spot_percent / 100, ev); S['best'] = (b.avg_best_speed, ev); S['popup'] = (b.popups_percent / 100, ev); S['under'] = (b.poorlyunder_percent / 100, ev)
    S['topped'] = (b.poorlytopped_percent / 100, ev); S['flare'] = (b.flareburner_percent / 100, ev); S['solid'] = (b.solidcontact_percent / 100, ev)
    S['gb'] = (b.GB / bb, bb); S['fb'] = (b.FB / bb, bb); S['ld'] = (b.LD / bb, bb); S['pull'] = (b['Pull%'], bb)
    for n, c in (('oswing', 'O-Swing%'), ('zswing', 'Z-Swing%'), ('zcontact', 'Z-Contact%'), ('ocontact', 'O-Contact%'), ('swstr', 'SwStr%'), ('zone', 'Zone%')): S[n] = (b[c], b.Pitches)
    S['sprint'] = (b.sprint_speed, b.PA.where(b.sprint_speed.notna())); S['spd'] = (b.Spd, b.PA)
    S['batspeed'] = (b.AvgBatSpeed, b.CompetitiveSwings); S['squp'] = (b['SquaredUpContact%'], b.CompetitiveSwings); S['blast'] = (b['BlastContact%'], b.CompetitiveSwings)
    ps = b[['mlbam', 'Season', 'PlayerName', 'Team', 'Age', 'Bats', 'PA', 'AB', 'OBP', 'SLG']].copy()
    lg = {}
    for s, (v, n) in S.items():
        n = n.where(v.notna() & (n > 0)).fillna(0).astype(float); v = v.fillna(0).astype(float)
        m = (v * n).groupby(b.Season).sum() / n.groupby(b.Season).sum()
        ps['v_' + s] = v - b.Season.map(m).fillna(0); ps['n_' + s] = n; lg[s] = m
    return ps, list(S), pd.DataFrame(lg)
def milb_park(m):
    """Per-line half-park multipliers e_<comp> = 1 + (pf - 1)/2 from the affiliate's 1-yr regressed factor. 1.0 when unknown."""
    E = ['HR', '2B', '3B', 'BB', 'SO', 'AVG', 'OBP']
    mp = pd.read_csv(f'{D}/milb_pf_map.csv')
    org = m.Team.fillna('').str.replace(r'\s*\(.*\)$', '', regex=True)
    key = pd.DataFrame({'Season': m.Season.values, 'lvl': m.lvl.values, 'org': org.values})
    r = key.merge(mp, on=['Season', 'lvl', 'org'], how='left')
    sc = float(os.environ.get('BDL_MILB_PARK_SCALE', '0.5'))   # share of the park deviation in a player's line; 0.5 = half his games at home
    out = {c: 1 + (r['pf_' + c].fillna(1).values - 1) * sc for c in E}
    return out, r['pf_HR'].notna().values
def milb_table():
    m = pd.read_pickle(f'{D}/milb.pkl'); m['grp'] = m.lvl.replace({'A+': 'LO', 'A': 'LO'})
    for c in ('PA','AB','H','2B','3B','HR','BB','IBB','SO','HBP','SF','OBP','SLG','SwStr%','Spd','Age'): m[c] = pd.to_numeric(m[c], errors='coerce')
    if MILB_PARK:   # neutralize the half of each line played in the affiliate's park
        e, hit = milb_park(m); print(f'milb park: matched {hit.mean():.1%} of lines, {m.PA[hit].sum() / m.PA.sum():.1%} of PA')
        hr = m.HR / e['HR']; d2 = m['2B'] / e['2B']; d3 = m['3B'] / e['3B']; so = m.SO / e['SO']; h = m.H / e['AVG']
        ubb = (m.BB - m.IBB) / e['BB']; obp = m.OBP / e['OBP']
    else:
        hr, d2, d3, so, h, ubb, obp = m.HR, m['2B'], m['3B'], m.SO, m.H, m.BB - m.IBB, m.OBP
    bip = (m.AB - so - hr + m.SF).clip(lower=1)
    V = dict(obp=obp, iso=(d2 + 2 * d3 + 3 * hr) / m.AB.clip(lower=1), k=so / m.PA, bb=ubb / m.PA, hr=hr / m.PA, babip=(h - hr) / bip, spd=m.Spd, swstr=m['SwStr%'])
    out = m[['mlbam', 'Season', 'grp', 'lvl', 'PA', 'Age']].copy()
    for s, v in V.items():
        ok = v.notna(); w = m.PA.where(ok, 0); key = [m.Season, m.lvl]
        mu = (v.fillna(0) * w).groupby(key).transform('sum') / w.groupby(key).transform('sum')
        out['d_' + s] = (v - mu).fillna(0); out['w_' + s] = w
    # collapse to one row per player-season-group (PA-weighted)
    g = out.groupby(['mlbam', 'Season', 'grp']); res = g.PA.sum().to_frame('PA'); res['Age'] = g.Age.min()
    for s in V:
        res['w_' + s] = g['w_' + s].sum(); res['d_' + s] = (out['d_' + s] * out['w_' + s]).groupby([out.mlbam, out.Season, out.grp]).sum() / res['w_' + s].clip(lower=1)
    return res.reset_index(), list(V)
def park():
    pf = pd.read_pickle(f'{D}/pf.pkl')[['pfyear', 'Team', 'pf_obp', 'pf_slg', 'pf_hr']]
    return pf
def build(targets=range(2016, 2028), proj_team=None):
    ps, stats, lg = load(); mi, mstats = milb_table(); pf = park()
    rows = []
    for Y in targets:
        ids = set(ps[ps.Season.between(Y - 3, Y - 1)].mlbam) | set(mi[mi.Season.between(Y - 2, Y - 1)].mlbam) | set(ps[ps.Season == Y].mlbam)
        rows.append(pd.DataFrame({'mlbam': sorted(ids), 'Y': Y}))
    T = pd.concat(rows, ignore_index=True)
    tgt = ps[['mlbam', 'Season', 'PlayerName', 'Team', 'Age', 'PA', 'AB', 'OBP', 'SLG', 'Bats']].rename(columns={'Season': 'Y', 'Team': 'team', 'Age': 'age_act', 'PA': 'PA_t', 'AB': 'AB_t', 'OBP': 'OBP_t', 'SLG': 'SLG_t'})
    T = T.merge(tgt, on=['mlbam', 'Y'], how='left')
    for k in LAGS:
        x = ps[['mlbam', 'Season', 'Team', 'Age', 'PA'] + [c for c in ps if c[:2] in ('v_', 'n_')]].copy(); x['Y'] = x.Season + k
        x = x.drop(columns='Season').rename(columns={c: f'{c}_{k}' for c in x if c not in ('mlbam', 'Y')})
        T = T.merge(x, on=['mlbam', 'Y'], how='left')
        for g in ('AAA', 'AA', 'LO'):
            x = mi[mi.grp == g].drop(columns='grp').copy(); x['Y'] = x.Season + k
            x = x.drop(columns='Season').rename(columns={c: f'm{g}_{c}_{k}' for c in x if c not in ('mlbam', 'Y')})
            T = T.merge(x, on=['mlbam', 'Y'], how='left')
    # age in target season
    age = T.age_act.copy()
    for k in LAGS:
        age = age.fillna(T[f'Age_{k}'] + k)
        for g in ('AAA', 'AA', 'LO'): age = age.fillna(T[f'm{g}_Age_{k}'] + k)
    T['age'] = age
    # names / handedness for projection rows
    nm = ps.sort_values('Season').groupby('mlbam')[['PlayerName', 'Bats']].last(); T['PlayerName'] = T.PlayerName.fillna(T.mlbam.map(nm.PlayerName)); T['Bats'] = T.Bats.fillna(T.mlbam.map(nm.Bats))
    mn = pd.read_pickle(f'{D}/milb.pkl').sort_values('Season').groupby('mlbam').PlayerName.last(); T['PlayerName'] = T.PlayerName.fillna(T.mlbam.map(mn))
    # park: target-season team (or supplied projected team), factors measured through Y-1
    if proj_team is not None:
        T = T.merge(proj_team, on=['mlbam', 'Y'], how='left'); T['team'] = T.team.fillna(T.pteam)
    def pfmerge(T, teamcol, year, suffix):
        key = pd.DataFrame({'Team': T[teamcol].values, 'pfyear': np.clip(year, 2015, 2026)})
        if suffix == 'new': key.loc[(key.Team == 'TBR') & (key.pfyear == 2025), 'pfyear'] = 2024   # Rays back at Tropicana in 2026: use its last 3-yr factor, not Steinbrenner's
        r = key.merge(pf, on=['Team', 'pfyear'], how='left')
        bad = (key.Team.isin(['ATH', 'TBR']) & (np.asarray(year) == 2024) & (suffix == 'new')).values  # 2025: both clubs moved to parks with no history
        for c in ('pf_obp', 'pf_slg', 'pf_hr'): T[f'{c}_{suffix}'] = np.where(bad, 0, (r[c].fillna(1).values - 1) / 2)
        return T
    T = pfmerge(T, 'team', T.Y.values - 1, 'new')
    for k in LAGS: T = pfmerge(T, f'Team_{k}', T.Y.values - k, f'old{k}')
    # second-half-of-last-season movement: (2nd-half rate - full-season rate), to be shrunk in the model
    h2, _, _ = load(pd.read_pickle(f'{D}/mlb_h2.pkl')); full = ps.set_index(['mlbam', 'Season'])
    for s_ in H2STATS:
        x = h2[['mlbam', 'Season', 'v_' + s_, 'n_' + s_]].copy(); fv = full['v_' + s_].reindex(pd.MultiIndex.from_frame(x[['mlbam', 'Season']])).values
        x['h2d_' + s_] = np.where(x['n_' + s_] > 0, x['v_' + s_] - fv, 0); x['h2n_' + s_] = x['n_' + s_]; x['Y'] = x.Season + 1
        T = T.merge(x[['mlbam', 'Y', 'h2d_' + s_, 'h2n_' + s_]], on=['mlbam', 'Y'], how='left')
    T.attrs['stats'] = stats; T.attrs['mstats'] = mstats
    return T, stats, mstats, lg
if __name__ == '__main__':
    pj = pd.read_pickle(f'{D}/proj.pkl'); pt = pj[pj.sys == 'steamer'][['mlbam', 'Season', 'pteam']].rename(columns={'Season': 'Y'})
    T, stats, mstats, lg = build(proj_team=pt)
    tag = os.environ.get('BDL_TAG', '')
    T.to_pickle(f'{D}/T{tag}.pkl'); pd.to_pickle((stats, mstats, lg), f'{D}/meta{tag}.pkl')
    print(T.shape, T.groupby('Y').PA_t.agg(['count', 'sum']).T.round())
