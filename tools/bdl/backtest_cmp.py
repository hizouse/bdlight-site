"""Walk-forward backtest (final.py settings: ridge alpha 300, no GBM, h2 off) for one or more feature tables, graded on
final.py's samples, plus a MiLB-reliant subset (hitters with < 300 MLB PA in the prior 3 seasons).
usage: python backtest_cmp.py _base _park ..."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import *
KW = dict(gbm=False, alpha=300)
P = json.load(open(f'{D}/stage1.json'))
cols = {'BDL': ('myOBP', 'mySLG'), 'Steamer': ('steamerOBP', 'steamerSLG')}
res = {}
for tag in sys.argv[1:]:
    T0 = pd.read_pickle(f'{D}/T{tag}.pkl'); stats, mstats, lg = pd.read_pickle(f'{D}/meta{tag}.pkl')
    F0 = features(T0, stats, mstats, P, h2=False)
    h = (T0.Y <= 2026).values; T = T0[h].reset_index(drop=True); F = F0[h].reset_index(drop=True)
    R = attach(walk(T, F, lg, TESTS, **KW))
    mp3 = T[['mlbam', 'Y']].assign(mlbpa3=T[['PA_1', 'PA_2', 'PA_3']].fillna(0).sum(axis=1)); R = R.merge(mp3, on=['mlbam', 'Y'], how='left')
    R.to_pickle(f'{D}/R{tag}.pkl'); res[tag] = R
rows = []
for tag, R in res.items():
    for lab, mp, st, sub in (('400+ PA, same team', 400, True, None), ('400+ PA, everyone', 400, False, None), ('150+ PA, everyone', 150, False, None),
                             ('All hitters', 1, False, None), ('150+ PA, <300 MLB PA prior 3 yrs', 150, False, 'rookie'), ('All, <300 MLB PA prior 3 yrs', 1, False, 'rookie')):
        RR = R[R.mlbpa3 < 300] if sub else R
        G, S = grade(RR, cols, mp, st, verbose=False)
        a = G.loc['ALL']; rows.append(dict(tag=tag, sample=lab, n=int(a.n), BDL_OBP=a.BDL_OBP, BDL_SLG=a.BDL_SLG, BDL_OPS=a.BDL_OPS, Stm_OBP=a.Steamer_OBP, Stm_SLG=a.Steamer_SLG))
out = pd.DataFrame(rows); pd.set_option('display.width', 200)
print(out.round(2).to_string(index=False))
out.to_csv(f'{D}/../out/backtest_cmp_{"_".join(t.strip("_") for t in res)}.csv', index=False)
