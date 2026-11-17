"""Stage 2: next-season OBP / SLG from talent composites, Statcast skills, minor-league lines, age and park."""
import numpy as np, pandas as pd, os, json, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage1 import comp
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
MG = ('AAA', 'AA', 'LO')
H2 = ('bb', 'k', 'hr', 'babip', 'iso', 'obp', 'slg', 'woba', 'xwoba', 'ev', 'ev90', 'barrel', 'hardhit', 'la', 'oswing', 'zcontact', 'swstr', 'gb', 'pull')
L1 = ('obp', 'slg', 'bb', 'k', 'babip', 'iso', 'xwoba', 'xobp', 'barrel', 'ev90', 'oswing', 'zcontact', 'sprint')
def features(T, stats, mstats, P, drop=('batspeed', 'squp', 'blast'), h2=True, l1=True):
    F = pd.DataFrame(index=T.index)
    for s in stats:
        if s in drop: continue
        F['c_' + s], den = comp(T, s, P[s]['d'], P[s]['c'])
        if s == 'obp': rel = den / (den + 300); wpa = den
        if s == 'xwoba': F['rel_sc'] = den / (den + 300)
    F['rel'] = rel; nr = 1 - rel
    if l1:   # last season on its own, so the fit can lean more or less on recency than the fixed year weights
        for s in L1: F['l1_' + s], _ = comp(T, s, 1, P[s]['c'], lags=(1,))
    if h2:   # second-half movement within last season
        for s in H2:
            n = T['h2n_' + s].fillna(0).values; F['h2_' + s] = n / (n + 0.7 * P[s]['c']) * T['h2d_' + s].fillna(0).values
    a = (T.age.fillna(27) - 27).clip(-7, 13).values
    F['a_pos'] = np.maximum(a, 0); F['a_neg'] = np.minimum(a, 0); F['a2'] = np.maximum(a, 0) ** 2; F['nr_a'] = nr * a; F['nr_a2'] = nr * a * a
    for s in ('xwoba', 'k', 'iso', 'sprint', 'barrel', 'bb'):
        if s not in drop: F[f'a_x_{s}'] = a * F['c_' + s]
    if 'xwoba' not in drop:
        F['luck'] = F.c_woba - F.c_xwoba; F['a_x_luck'] = a * F.luck
    mtot = 0
    for g in MG:
        den = 0
        for s in mstats:
            f, den = comp(T, s, 0.6, 250, pre=f'm{g}_')
            F[f'm{g}_{s}'] = f * nr; 
        F[f'm{g}_rel'] = den / (den + 250) * nr; F[f'm{g}_rel_a'] = F[f'm{g}_rel'] * a; mtot = mtot + den
    F['noinfo'] = nr * (1 - mtot / (mtot + 250))
    # park: new park, and the parks behind the past lines (PA-weighted)
    op = {c: 0 for c in ('pf_obp', 'pf_slg', 'pf_hr')}; tot = 0
    for k in (1, 2, 3):
        w = T[f'PA_{k}'].fillna(0).values * 0.75 ** (k - 1); tot = tot + w
        for c in op: op[c] = op[c] + w * T[f'{c}_old{k}'].fillna(0).values
    for c in op:
        F[c + '_new'] = T[c + '_new'].fillna(0).values; F[c + '_old'] = op[c] / (tot + 300)
    F['bats_L'] = (T.Bats == 'L').astype(float).values; F['bats_S'] = (T.Bats == 'S').astype(float).values
    return F.fillna(0)
def weights(T, target):
    v, tau2 = (0.22, 0.020 ** 2) if target == 'OBP' else (0.75, 0.045 ** 2)   # binomial-ish noise per PA, talent-change variance
    n = T.PA_t if target == 'OBP' else T.AB_t
    return 1 / (tau2 + v / n.clip(lower=1))
class Model:
    def __init__(self, alpha=30, gbm=True, gw=0.5): self.alpha, self.gbm, self.gw = alpha, gbm, gw
    def fit(self, F, y, w):
        self.mu = np.average(F.values, axis=0, weights=w); self.sd = np.sqrt(np.average((F.values - self.mu) ** 2, axis=0, weights=w)) + 1e-9
        Z = (F.values - self.mu) / self.sd; self.r = Ridge(alpha=self.alpha * w.mean()).fit(Z, y, sample_weight=w)
        if self.gbm:
            self.g = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.03, max_iter=250, min_samples_leaf=60, l2_regularization=5, random_state=0).fit(F.values, y - self.r.predict(Z), sample_weight=w)
        return self
    def predict(self, F):
        Z = (F.values - self.mu) / self.sd; p = self.r.predict(Z)
        return p + self.gw * self.g.predict(F.values) if self.gbm else p
def lgdev(T, lg):
    return T.OBP_t - T.Y.map(lg.obp), T.SLG_t - T.Y.map(lg.slg)
def walk(T, F, lg, tests, first=2016, **kw):
    yo, ys = lgdev(T, lg); out = {}
    for Y in tests:
        tr = ((T.Y >= first) & (T.Y < Y) & (T.PA_t >= 1)).values; te = (T.Y == Y).values
        res = T.loc[te, ['mlbam', 'Y', 'PlayerName', 'team', 'age', 'PA_t', 'OBP_t', 'SLG_t']].copy()
        for tg, y in (('OBP', yo), ('SLG', ys)):
            w = weights(T, tg).values; m = Model(**kw).fit(F[tr], y[tr].values, w[tr])
            res['my' + tg] = m.predict(F[te]) + lg[tg.lower()][Y - 1]
        out[Y] = res
    return pd.concat(out.values())
def rmse(p, y, w, norm=True):
    if norm: p = p - np.average(p - y, weights=w)
    return np.sqrt(np.average((p - y) ** 2, weights=w))
def grade(R, cols, minpa=400, same_team=True, label='', verbose=True):
    """cols: dict name -> (obp col, slg col). Common sample across all listed systems."""
    S = R[R.PA_t >= minpa].copy()
    if same_team: S = S[(S.team != '- - -') & (S.team == S.pteam)]
    for n, (o, s) in cols.items(): S = S[S[o].notna() & S[s].notna()]
    rows = []
    for Y, g in list(S.groupby('Y')) + [('ALL', S)]:
        w = g.PA_t.values; r = {'Y': Y, 'n': len(g)}
        for n, (o, s) in cols.items():
            if Y == 'ALL':  # pooled: normalise within season, then pool
                eo = np.concatenate([(h[o] - h.OBP_t - np.average(h[o] - h.OBP_t, weights=h.PA_t)).values for _, h in g.groupby('Y')])
                es = np.concatenate([(h[s] - h.SLG_t - np.average(h[s] - h.SLG_t, weights=h.PA_t)).values for _, h in g.groupby('Y')])
                ww = np.concatenate([h.PA_t.values for _, h in g.groupby('Y')])
                r[n + '_OBP'] = np.sqrt(np.average(eo ** 2, weights=ww)) * 1000; r[n + '_SLG'] = np.sqrt(np.average(es ** 2, weights=ww)) * 1000; r[n + '_OPS'] = np.sqrt(np.average((eo + es) ** 2, weights=ww)) * 1000
            else:
                r[n + '_OBP'] = rmse(g[o].values, g.OBP_t.values, w) * 1000; r[n + '_SLG'] = rmse(g[s].values, g.SLG_t.values, w) * 1000
                r[n + '_OPS'] = rmse((g[o] + g[s]).values, (g.OBP_t + g.SLG_t).values, w) * 1000
        rows.append(r)
    G = pd.DataFrame(rows).set_index('Y')
    if verbose: print(label); print(G.round(1).to_string())
    return G, S
def attach(R):
    pj = pd.read_pickle(f'{D}/proj.pkl'); pj['pteam'] = pj.pteam.replace({'OAK': 'ATH'})
    for sysn in ('steamer', 'zips'):
        x = pj[pj.sys == sysn][['mlbam', 'Season', 'pOBP', 'pSLG'] + (['pteam'] if sysn == 'steamer' else [])].rename(columns={'Season': 'Y', 'pOBP': sysn + 'OBP', 'pSLG': sysn + 'SLG'})
        R = R.merge(x, on=['mlbam', 'Y'], how='left')
    return R
TESTS = (2019, 2021, 2022, 2023, 2024, 2025, 2026)
if __name__ == '__main__':
    T = pd.read_pickle(f'{D}/T.pkl'); stats, mstats, lg = pd.read_pickle(f'{D}/meta.pkl'); P = json.load(open(f'{D}/stage1.json'))
    T = T[T.Y <= 2026].reset_index(drop=True)
    F = features(T, stats, mstats, P); print('features', F.shape)
    cols = {'me': ('myOBP', 'mySLG'), 'stm': ('steamerOBP', 'steamerSLG'), 'zips': ('zipsOBP', 'zipsSLG')}
    for name, kw in (('ridge only', dict(gbm=False)), ('ridge+gbm', dict(gbm=True))):
        R = attach(walk(T, F, lg, TESTS, **kw))
        grade(R, cols, 400, True, f'--- {name}: 400+ PA, same team as projected')
        grade(R, cols, 150, False, f'--- {name}: 150+ PA, all')
    R.to_pickle(f'{D}/R.pkl')
