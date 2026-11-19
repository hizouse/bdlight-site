"""Assemble player-season tables from raw pulls -> data/*.pkl"""
import json, re, glob, os, numpy as np, pandas as pd
R = os.path.join(os.path.dirname(__file__), '..', 'raw'); D = os.path.join(os.path.dirname(__file__), '..', 'data'); os.makedirs(D, exist_ok=True)
strip = lambda s: re.sub('<[^>]+>', '', s) if isinstance(s, str) else s
YEARS = range(2012, 2027)
# ---------- MLB batting (FanGraphs, includes Statcast columns)
keep = ['xMLBAMID','playerid','PlayerName','Team','Season','Age','Bats','position','G','AB','PA','H','1B','2B','3B','HR','BB','IBB','SO','HBP','SF','SH',
        'GB','FB','LD','IFFB','Pitches','OBP','SLG','wOBA','Spd','O-Swing%','Z-Swing%','Swing%','O-Contact%','Z-Contact%','Contact%','Zone%','SwStr%',
        'Pull%','Oppo%','Soft%','Hard%','xwOBA','xAVG','xSLG','Events','EV','LA','Barrels','Barrel%','maxEV','HardHit%','EV90',
        'AvgBatSpeed','SquaredUpContact%','BlastContact%','SwingLength','CompetitiveSwings','scZ-Contact%','scO-Swing%','scZ-Swing%']
rows = []
for y in YEARS:
    d = json.load(open(f'{R}/fg_bat_{y}.json'))['data']
    for r in d: rows.append({k: r.get(k) for k in keep})
b = pd.DataFrame(rows)
b['Team'] = b.Team.map(strip); b = b.rename(columns={'xMLBAMID': 'mlbam'})
b = b[b.mlbam.notna() & (b.PA > 0)].copy(); b['mlbam'] = b.mlbam.astype(int); b['Season'] = b.Season.astype(int)
num = [c for c in b.columns if c not in ('PlayerName','Team','Bats','position','playerid')]
b[num] = b[num].apply(pd.to_numeric, errors='coerce')
# Savant custom leaderboard extras
sv = []
for y in range(2015, 2027):
    s = pd.read_csv(f'{R}/sv_custom_{y}.csv', encoding='utf-8-sig'); s['Season'] = y; sv.append(s)
sv = pd.concat(sv).rename(columns={'player_id': 'mlbam'})
svk = ['xba','xslg','xwoba','xobp','xiso','xwobacon','wobacon','sweet_spot_percent','avg_best_speed','avg_hyper_speed','whiff_percent','iz_contact_percent',
       'oz_swing_percent','z_swing_percent','sprint_speed','popups_percent','batted_ball','pull_percent','groundballs_percent','flyballs_percent',
       'linedrives_percent','solidcontact_percent','poorlyunder_percent','poorlytopped_percent','flareburner_percent','meatball_swing_percent','exit_velocity_avg','barrel_batted_rate','hard_hit_percent']
b = b.merge(sv[['mlbam','Season'] + svk], on=['mlbam','Season'], how='left')
b.to_pickle(f'{D}/mlb.pkl')
rows = []
for y in range(2015, 2027):
    for r in json.load(open(f'{R}/fg_h2_{y}.json'))['data']: rows.append({k: r.get(k) for k in keep})
h = pd.DataFrame(rows).rename(columns={'xMLBAMID': 'mlbam'}); h['Team'] = h.Team.map(strip); h = h[h.mlbam.notna() & (h.PA > 0)].copy(); h['mlbam'] = h.mlbam.astype(int); h['Season'] = h.Season.astype(int)
h[num] = h[num].apply(pd.to_numeric, errors='coerce')
for c in svk: h[c] = np.nan
h.to_pickle(f'{D}/mlb_h2.pkl'); print('h2', h.shape, h.groupby('Season').PA.sum().to_dict()); print('mlb', b.shape, b.groupby('Season').PA.sum().round().to_dict())
# ---------- MiLB  (Team = parent org + level, e.g. "Nationals (AA)"; "- - -" = more than one org at that level; used for MiLB park factors)
LV = {1: 'AAA', 2: 'AA', 3: 'A+', 4: 'A'}; rows = []
mk = ['xMLBAMID','PlayerName','Team','Season','Age','PA','AB','H','1B','2B','3B','HR','BB','IBB','SO','HBP','SF','OBP','SLG','GB%','FB%','LD%','Pull%','SwStr%','Spd','ISO','BABIP']
for f in glob.glob(f'{R}/milb_*_L*.json'):
    y, lv = re.search(r'milb_(\d+)_L(\d)', f).groups()
    for r in json.load(open(f)):
        x = {k: r.get(k) for k in mk}; x['lvl'] = LV[int(lv)]; x['Season'] = int(y); rows.append(x)
m = pd.DataFrame(rows).rename(columns={'xMLBAMID': 'mlbam'}); m = m[m.mlbam.notna() & (m.PA > 0)].copy(); m['mlbam'] = m.mlbam.astype(int)
m['Team'] = m.Team.map(strip)
m.to_pickle(f'{D}/milb.pkl'); print('milb', m.shape, m.groupby('lvl').PA.sum().to_dict())
# ---------- Preseason projections
rows = []
for sysn in ('steamer', 'zips'):
    for y in range(2013, 2028):
        f = f'{R}/{sysn}_{y}.json'
        if not os.path.exists(f): continue
        for r in json.load(open(f)):
            if r.get('xMLBAMID') is None or not r.get('PA'): continue
            rows.append(dict(sys=sysn, Season=y, mlbam=int(r['xMLBAMID']), name=r['PlayerName'], pteam=r.get('ProjAbbName') or r.get('Team'), curteam=r.get('Team'),
                             pPA=r['PA'], pOBP=r['OBP'], pSLG=r['SLG'], pBB=r.get('BB%'), pK=r.get('K%'), pISO=r.get('ISO'), pBABIP=r.get('BABIP'), pwOBA=r.get('wOBA')))
p = pd.DataFrame(rows).drop_duplicates(['sys','Season','mlbam']); p.to_pickle(f'{D}/proj.pkl'); print('proj', p.groupby(['sys','Season']).size().unstack(0).T)
# ---------- Park factors (Savant, 3-yr rolling). Player effect = half of park index deviation.
CLUB = {'Angels':'LAA','Astros':'HOU','Athletics':'ATH','Blue Jays':'TOR','Braves':'ATL','Brewers':'MIL','Cardinals':'STL','Cubs':'CHC','D-backs':'ARI','Dodgers':'LAD',
        'Giants':'SFG','Guardians':'CLE','Indians':'CLE','Mariners':'SEA','Marlins':'MIA','Mets':'NYM','Nationals':'WSN','Orioles':'BAL','Padres':'SDP','Phillies':'PHI',
        'Pirates':'PIT','Rangers':'TEX','Rays':'TBR','Red Sox':'BOS','Reds':'CIN','Rockies':'COL','Royals':'KCR','Tigers':'DET','Twins':'MIN','White Sox':'CHW','Yankees':'NYY'}
rows = []
for y in range(2015, 2027):
    h = open(f'{R}/svpf_{y}.html').read(); d = json.loads(re.search(r'var data = (\[.*?\]);', h, re.S).group(1))
    for r in d:
        g = lambda k: float(r[k]) / 100
        # SLG index from hit-type indices at league-typical shares of total bases (1B .40, 2B .21, 3B .02, HR .37)
        slg = .40 * g('index_1b') + .21 * g('index_2b') + .02 * g('index_3b') + .37 * g('index_hr')
        rows.append(dict(pfyear=y, club=r['name_display_club'], Team=CLUB.get(r['name_display_club']), pf_obp=g('index_obp'), pf_slg=slg, pf_hr=g('index_hr'), pf_woba=g('index_woba'), n=float(r['n_pa'])))
# temporary parks Savant leaves out of the 3-year table: Sutter Health (A's 2025-26) and Steinbrenner (Rays 2025); short samples, so shrink toward neutral
def short(y, r, club, shrink):
    h = open(f'{R}/svpf_{y}_r{r}.html').read(); d = json.loads(re.search(r'var data = (\[.*?\]);', h, re.S).group(1)); x = [q for q in d if q['name_display_club'] == club][0]
    g = lambda k: 1 + shrink * (float(x[k]) / 100 - 1)
    return dict(pfyear=y, club=club, Team=CLUB[club], pf_obp=g('index_obp'), pf_slg=.40 * g('index_1b') + .21 * g('index_2b') + .02 * g('index_3b') + .37 * g('index_hr'), pf_hr=g('index_hr'), pf_woba=g('index_woba'), n=float(x['n_pa']))
rows += [short(2025, 1, 'Athletics', 0.5), short(2026, 2, 'Athletics', 0.75), short(2025, 1, 'Rays', 0.5)]
pf = pd.DataFrame(rows); print(pf[pf.Team.isna()].club.unique()); pf.to_pickle(f'{D}/pf.pkl')
print(pf[pf.pfyear == 2025].sort_values('pf_slg').round(3).to_string())
print(b.position.value_counts().head(15)); print(sorted(b[b.Season==2026].Team.unique()))
