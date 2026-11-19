"""Map FanGraphs MiLB org labels (e.g. "Nationals (AA)") to that org's affiliate park factor for the season and level.
Source: milb_park_factors_1yr.csv (1-yr regressed factors from milb_park_factors/scripts/build_pf.py). -> data/milb_pf_map.csv"""
import pandas as pd, os, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
SRC = sys.argv[1] if len(sys.argv) > 1 else f'{D}/milb_park_factors_1yr.csv'
pf = pd.read_csv(SRC)
pf = pf[pf.level.isin(['AAA', 'AA', 'A+', 'A']) & pf.parent_org.notna() & (pf.parent_org != 'Office of the Commissioner')]
m = pd.read_pickle(f'{D}/milb.pkl')
orgs = sorted(set(m.Team.str.replace(r'\s*\(.*\)$', '', regex=True)) - {'- - -'})
rows = []
for o in orgs:
    hit = pf[pf.parent_org.str.contains(o, regex=False)]
    for (y, lv), g in hit.groupby(['season', 'level']):
        if len(g) != 1: print('ambiguous', o, y, lv, g.team.tolist())
        r = g.iloc[0]
        rows.append(dict(Season=y, lvl=lv, org=o, team=r.team, venue=r.venue, **{c: r[c] for c in pf.columns if c.startswith('pf_')}))
mp = pd.DataFrame(rows)[['Season', 'lvl', 'org', 'team', 'pf_HR', 'pf_2B', 'pf_3B', 'pf_BB', 'pf_SO', 'pf_AVG', 'pf_OBP', 'pf_SLG']].round(3)
mp.to_csv(f'{D}/milb_pf_map.csv', index=False)
chk = m.assign(org=m.Team.str.replace(r'\s*\(.*\)$', '', regex=True)).merge(mp[['Season', 'lvl', 'org']], on=['Season', 'lvl', 'org'], how='left', indicator=True)
print(mp.shape); print('unmatched non-multi lines:', chk[(chk._merge == 'left_only') & (chk.Team != '- - -')].groupby(['Season', 'lvl', 'org']).size().head(20))
