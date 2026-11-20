"""2027 ERA: Steamer + Stuff+/Location+ + projected team DRS (FanGraphs Depth Charts rosters and playing time).
Coefficients are refit on all 2021-26 backtest seasons (same spec as the backtest's preseason-proxy model)."""
import json, numpy as np, pandas as pd
import features as FT
from evalx import X0, prep, run, wmean

COLS = ['x_stuff', 'x_loc', 'pERA_c', 'd_sdc_st_DRS']
X = prep(X0, years=range(2021, 2027))
_, _, _, _, b = run(X, COLS)
print('coefficients', {k: round(v, 4) for k, v in b.items()})

# ---- 2027 team defense from Depth Charts hitters ----
dcb = pd.DataFrame([(str(r['playerid']), r.get('teamid'), r.get('PA') or 0, r['PlayerName']) for r in json.load(open(FT.RAWDIR + '/fangraphsdc_bat_2027.json'))],
                   columns=['playerid', 'teamid', 'pPA', 'name'])
dcb = dcb[dcb.teamid.between(1, 30)]
pr = FT.player_proj(2027, 3000)
inn_s = FT.PS.set_index(['playerid', 'Season']).Inn
pin = sum(inn_s.reindex(list(zip(dcb.playerid, [2027 - l] * len(dcb)))).fillna(0).values for l in (1, 2, 3))
ppa = sum(FT.BPA.reindex(list(zip(dcb.playerid, [2027 - l] * len(dcb)))).fillna(0).values for l in (1, 2, 3))
frac = np.where(ppa > 100, np.clip(pin / np.maximum(ppa, 1) / FT.INN_PER_PA, 0, 1), 0.9)
dcb['einn'] = dcb.pPA * FT.INN_PER_PA * frac
dcb['rate'] = dcb.playerid.map(pr.DRS).fillna(0)
team = pd.DataFrame({'def_r9': 72 * (dcb.rate * dcb.einn).groupby(dcb.teamid).sum() / dcb.einn.groupby(dcb.teamid).sum()})
abb = {v: k for k, v in FT.ABB.items() if k != 'OAK'}
team['team'] = team.index.map(abb); team['def_runs_1450ip'] = team.def_r9 * 1450 / 9

# ---- pitchers ----
st = pd.DataFrame([(str(r['playerid']), r.get('xMLBAMID'), r['PlayerName'], r.get('IP') or 0, r.get('ERA'), r.get('FIP'), r.get('GS') or 0)
                   for r in json.load(open(FT.RAWDIR + '/steamer_pit_2027.json'))],
                  columns=['playerid', 'mlbam', 'Name', 'steamer_IP', 'steamer_ERA', 'steamer_FIP', 'steamer_GS'])
dcp = pd.DataFrame([(str(r['playerid']), r.get('teamid'), r.get('IP') or 0) for r in json.load(open(FT.RAWDIR + '/fangraphsdc_pit_2027.json'))],
                   columns=['playerid', 'dc_teamid', 'dc_IP']).drop_duplicates('playerid')
P = st.merge(dcp, on='playerid', how='left')
P = P[(P.dc_IP > 0) | (P.steamer_IP >= 10)].copy()
P['Team'] = P.dc_teamid.where(P.dc_teamid.between(1, 30)).map(abb)
for k, (c, base) in {'stuff': ('sp_stuff', 100), 'loc': ('sp_location', 100)}.items():
    v, n = FT.regressed(2027, c, 600, base)
    P[f'x_{k}'] = P.playerid.map(v).fillna(0)
P['prior_pitches'] = P.playerid.map(FT.regressed(2027, 'sp_stuff', 600, 100)[1]).fillna(0)
P['d_sdc_st_DRS'] = P.dc_teamid.map(team.def_r9)            # free agents / no DC team -> league average
P['pERA_c'] = P.steamer_ERA
# center like the backtest: IP-weighted mean over the MLB pool (pitchers on Depth Charts, weighted by DC IP)
pool = P[P.dc_IP > 0]; w = pool.dc_IP
mu = {c: wmean(pool[c].fillna(pool[c].mean() if c != 'd_sdc_st_DRS' else 0), w) for c in COLS}
P['d_sdc_st_DRS'] = P.d_sdc_st_DRS.fillna(mu['d_sdc_st_DRS'])
parts = {c: b[c] * (P[c] - mu[c]) for c in COLS}
P['adj_stuff'] = parts['x_stuff'] + parts['x_loc']
P['adj_shrink'] = parts['pERA_c']
P['adj_defense'] = parts['d_sdc_st_DRS']
P['BDL_ERA'] = P.steamer_ERA + P.adj_stuff + P.adj_shrink + P.adj_defense
P['Stuff+_reg'] = 100 + P.x_stuff; P['Location+_reg'] = 100 + P.x_loc
out = P[['Name', 'Team', 'playerid', 'mlbam', 'dc_IP', 'steamer_IP', 'steamer_GS', 'steamer_FIP', 'steamer_ERA', 'BDL_ERA',
         'adj_stuff', 'adj_shrink', 'adj_defense', 'Stuff+_reg', 'Location+_reg', 'prior_pitches']].copy()
out = out.sort_values(['dc_IP', 'steamer_IP'], ascending=False)
for c in ('dc_IP', 'steamer_IP', 'steamer_GS', 'prior_pitches'): out[c] = out[c].fillna(0).round(0).astype(int)
for c in ('steamer_FIP', 'steamer_ERA', 'BDL_ERA', 'adj_stuff', 'adj_shrink', 'adj_defense'): out[c] = out[c].round(2)
for c in ('Stuff+_reg', 'Location+_reg'): out[c] = out[c].round(1)
out.to_csv('/home/claude/pit/out/bdl_pitcher_era_2027.csv', index=False)
team.sort_values('def_r9', ascending=False).round(3).to_csv('/home/claude/pit/out/team_defense_2027.csv')
print(len(out), 'pitchers;', (out.dc_IP > 0).sum(), 'on Depth Charts')
print('IP-wtd mean ERA, DC pool: steamer', round(wmean(pool.steamer_ERA, w), 3), 'BDL', round(wmean(P.loc[pool.index, 'BDL_ERA'], w), 3))
print(team.sort_values('def_r9', ascending=False).round(3).to_string())
