"""2027 table: BDL projections put on Steamer's league level (Steamer has been unbiased for 400+ PA hitters), Steamer, and the 50/50 blend."""
import pandas as pd, numpy as np, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'); OUT = os.path.join(D, '..', 'out')
p = pd.read_pickle(f'{D}/proj2027_raw.pkl'); q = p[p.pPA >= 350]
so = np.average(q.pOBP - q.BDL_OBP, weights=q.pPA); ss = np.average(q.pSLG - q.BDL_SLG, weights=q.pPA); print('level shift OBP %+.4f SLG %+.4f' % (so, ss))
p['OBP'] = p.BDL_OBP + so; p['SLG'] = p.BDL_SLG + ss; p['OPS'] = p.OBP + p.SLG; p['Stm_OBP'] = p.pOBP; p['Stm_SLG'] = p.pSLG; p['Stm_OPS'] = p.pOBP + p.pSLG
p['Diff_OPS'] = p.OPS - p.Stm_OPS; p['Blend_OBP'] = (p.OBP + p.Stm_OBP) / 2; p['Blend_SLG'] = (p.SLG + p.Stm_SLG) / 2; p['Blend_OPS'] = p.Blend_OBP + p.Blend_SLG
k = p[p.pOBP.notna() & ((p.PA_1.fillna(0) >= 50) | (p.MiLB_PA_2026 >= 200) | (p.pPA >= 150))].copy()
k['PA_2026'] = k.PA_1.fillna(0).astype(int); k['Age'] = k.age.round().astype('Int64'); k['Team'] = k.team.fillna('—'); k['Stm_PA'] = k.pPA.round().astype(int); k['MiLB_PA_2026'] = k.MiLB_PA_2026.astype(int)
k = k.sort_values('Blend_OPS', ascending=False).rename(columns={'PlayerName': 'Player'})
k = k[['Player', 'Team', 'Age', 'Bats', 'PA_2026', 'MiLB_PA_2026', 'Stm_PA', 'OBP', 'SLG', 'OPS', 'Stm_OBP', 'Stm_SLG', 'Stm_OPS', 'Diff_OPS', 'Blend_OBP', 'Blend_SLG', 'Blend_OPS', 'mlbam']]
for c in k.columns[7:17]: k[c] = k[c].round(3)
k.to_csv(f'{OUT}/bdl_projections_2027.csv', index=False); print(len(k))
r = k[k.Stm_PA >= 300]
for asc in (False, True): print(r.sort_values('Diff_OPS', ascending=asc).head(12)[['Player', 'Team', 'Age', 'PA_2026', 'OBP', 'SLG', 'OPS', 'Stm_OPS', 'Diff_OPS']].to_string(index=False))
