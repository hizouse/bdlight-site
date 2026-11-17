"""Stage 1: per-stat 'talent' composites. For each stat pick year-decay d and regression constant c
(composite = sum_k d^(k-1) n_k dev_k / (sum_k d^(k-1) n_k + c)) that best predict the same stat next season.
Tuned only on target seasons <= 2021 so later test seasons are untouched."""
import numpy as np, pandas as pd, os, json
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
def comp(T, s, d, c, pre='', lags=(1, 2, 3)):
    num = 0; den = 0
    for k in lags:
        n = T[f'{pre}n_{s}_{k}'].fillna(0).values if pre == '' else T[f'{pre}w_{s}_{k}'].fillna(0).values
        v = T[f'{pre}v_{s}_{k}'].fillna(0).values if pre == '' else T[f'{pre}d_{s}_{k}'].fillna(0).values
        w = d ** (k - 1); num = num + w * n * v; den = den + w * n
    return num / (den + c), den
if __name__ == '__main__':
    T = pd.read_pickle(f'{D}/T.pkl'); stats, mstats, lg = pd.read_pickle(f'{D}/meta.pkl')
    nxt = T[['mlbam', 'Y'] + [f'v_{s}_1' for s in stats] + [f'n_{s}_1' for s in stats]].copy(); nxt['Y'] -= 1
    nxt.columns = ['mlbam', 'Y'] + [f't_{s}' for s in stats] + [f'tn_{s}' for s in stats]
    X = T.merge(nxt, on=['mlbam', 'Y'], how='inner'); X = X[X.Y <= 2021]
    P = {}
    for s in stats:
        if s in ('batspeed', 'squp', 'blast'): P[s] = dict(d=0.6, c=None); continue
        tn = X[f'tn_{s}'].fillna(0).values; t = X[f't_{s}'].fillna(0).values
        med = np.median(X[f'n_{s}_1'][X[f'n_{s}_1'] > 0]); best = None
        for d in (0.3, 0.45, 0.6, 0.75, 0.9):
            for cm in (0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 1.5, 2.5, 4):
                f, den = comp(X, s, d, cm * med * 3); ok = (tn > 0) & (den > 0)
                w = tn[ok]; e = np.sqrt(np.average((t[ok] - f[ok]) ** 2, weights=w))
                if best is None or e < best[0]: best = (e, d, cm * med * 3)
        f0 = np.sqrt(np.average(t[(tn > 0)] ** 2, weights=tn[tn > 0]))
        P[s] = dict(d=best[1], c=round(float(best[2]), 1)); print(f'{s:9s} decay {best[1]:.2f}  c {best[2]:8.0f}   rmse {best[0]:.4f} vs no-info {f0:.4f}  (R2 {1 - (best[0] / f0) ** 2:.2f})')
    for s in ('batspeed', 'squp', 'blast'): P[s]['c'] = P['ev']['c'] * 2
    json.dump(P, open(f'{D}/stage1.json', 'w'), indent=1)
