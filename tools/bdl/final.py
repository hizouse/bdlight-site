"""Final system: walk-forward backtest vs Steamer/ZiPS + 2027 projections."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
OUT = os.path.join(D, '..', 'out'); os.makedirs(OUT, exist_ok=True)
T0 = pd.read_pickle(f'{D}/T.pkl'); stats, mstats, lg = pd.read_pickle(f'{D}/meta.pkl'); P = json.load(open(f'{D}/stage1.json'))
F0 = features(T0, stats, mstats, P, h2=False); KW = dict(gbm=False, alpha=300)
h = (T0.Y <= 2026).values; T = T0[h].reset_index(drop=True); F = F0[h].reset_index(drop=True)
R = attach(walk(T, F, lg, TESTS, **KW))
for c in ('OBP', 'SLG'): R['mix' + c] = (R['my' + c] + R['steamer' + c]) / 2
R.to_pickle(f'{D}/R_final.pkl')
cols = {'BDL': ('myOBP', 'mySLG'), 'Steamer': ('steamerOBP', 'steamerSLG'), 'ZiPS': ('zipsOBP', 'zipsSLG'), 'BDL+Stm': ('mixOBP', 'mixSLG')}
pd.set_option('display.width', 250); summ = []
for lab, mp, st in (('400+ PA, stayed with projected team', 400, True), ('400+ PA, everyone', 400, False), ('150+ PA, everyone', 150, False), ('All hitters (PA-weighted)', 1, False)):
    G, S = grade(R, cols, mp, st, verbose=False); G['sample'] = lab; summ.append(G.reset_index())
    print(f'\n=== {lab}  (n={len(S)})'); print(G.drop(columns='sample').round(1).to_string())
    # bootstrap: resample players within season, share of resamples where BDL has lower pooled RMSE
    rng = np.random.default_rng(7); S = S.reset_index(drop=True); E = {}
    for n, (o, s) in cols.items():
        eo = S[o] - S.OBP_t; es = S[s] - S.SLG_t
        for Y, g in S.groupby('Y'):
            eo[g.index] -= np.average(eo[g.index], weights=g.PA_t); es[g.index] -= np.average(es[g.index], weights=g.PA_t)
        E[n] = (eo.values, es.values)
    w = S.PA_t.values; idx = [rng.integers(0, len(S), len(S)) for _ in range(4000)]
    for other in ('Steamer', 'ZiPS'):
        win = {}
        for j, m in enumerate(('OBP', 'SLG', 'OPS')):
            f = lambda n, i: np.average(((E[n][0] + E[n][1]) if m == 'OPS' else E[n][j])[i] ** 2, weights=w[i])
            win[m] = np.mean([f('BDL', i) < f(other, i) for i in idx])
        print(f'   BDL beats {other} in resamples: OBP {win["OBP"]:.0%}  SLG {win["SLG"]:.0%}  OPS {win["OPS"]:.0%}')
    if mp == 400 and st:  # un-normalised errors too (league level guessed as last season's)
        print('   raw (no mean shift) PA-wtd RMSE, pooled:', {n: [round(float(np.sqrt(np.average((S[c] - S[t]) ** 2, weights=w)) * 1000), 1) for c, t in ((o, 'OBP_t'), (s, 'SLG_t'))] for n, (o, s) in cols.items()})
pd.concat(summ).to_csv(f'{OUT}/backtest_summary.csv', index=False)
# ---------- 2027
tr = ((T0.Y >= 2016) & (T0.Y <= 2026) & (T0.PA_t >= 1)).values; te = (T0.Y == 2027).values
yo, ys = lgdev(T0, lg); pr = T0.loc[te, ['mlbam', 'PlayerName', 'team', 'age', 'Bats', 'PA_1', 'PA_2', 'PA_3']].copy(); coefs = {}
for tg, y in (('OBP', yo), ('SLG', ys)):
    w = weights(T0, tg).values; m = Model(**KW).fit(F0[tr], y[tr].values, w[tr]); pr['BDL_' + tg] = m.predict(F0[te]) + lg[tg.lower()][2026]
    coefs[tg] = pd.Series(m.r.coef_ * 1000, index=F0.columns)
pd.DataFrame(coefs).round(2).to_csv(f'{OUT}/coefficients_per_sd.csv')
pj = pd.read_pickle(f'{D}/proj.pkl'); s = pj[(pj.sys == 'steamer') & (pj.Season == 2027)][['mlbam', 'name', 'pPA', 'pOBP', 'pSLG']]
pr = pr.merge(s, on='mlbam', how='left'); pr['PlayerName'] = pr.PlayerName.fillna(pr.name)
mi = pd.read_pickle(f'{D}/milb.pkl'); mp_ = mi[mi.Season == 2026].groupby('mlbam').PA.sum(); pr['MiLB_PA_2026'] = pr.mlbam.map(mp_).fillna(0)
pr.to_pickle(f'{D}/proj2027_raw.pkl'); print('\n2027 rows', len(pr), 'with Steamer', pr.pOBP.notna().sum())
print(pd.DataFrame(coefs).round(2).sort_values('SLG', key=abs, ascending=False).head(40).to_string())
