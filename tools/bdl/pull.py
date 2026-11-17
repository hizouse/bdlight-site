"""Pull raw inputs: FanGraphs MLB + MiLB batting, preseason Steamer/ZiPS history, Savant leaderboards."""
import os, json, time, subprocess, sys
RAW = os.path.join(os.path.dirname(__file__), '..', 'raw')
def get(url, out, min_bytes=500, tries=3):
    p = os.path.join(RAW, out)
    ok = lambda: os.path.exists(p) and os.path.getsize(p) > min_bytes and open(p,'rb').read(15).lstrip(b'\xef\xbb\xbf')[:1] != b'<'
    if ok(): return p
    for i in range(tries):
        subprocess.run(['curl', '-s', '-m', '180', url, '-o', p])
        if ok(): return p
        time.sleep(5)
    print('FAILED', out, file=sys.stderr); return None
FG = 'https://www.fangraphs.com/api'
for y in range(2012, 2027):
    get(f'{FG}/leaders/major-league/data?age=&pos=all&stats=bat&lg=all&qual=0&season={y}&season1={y}&ind=0&pageitems=5000&type=8', f'fg_bat_{y}.json')
    get(f'{FG}/projections?type=steamer_{y}&stats=bat&pos=all&team=0&players=0&lg=all', f'steamer_{y}.json')
    get(f'{FG}/projections?type=zips_{y}&stats=bat&pos=all&team=0&players=0&lg=all', f'zips_{y}.json')
    for lv in (1, 2, 3, 4):
        if y == 2020: continue
        get(f'{FG}/leaders/minor-league/data?pos=all&level={lv}&lg=2,4,5,6,7,8,9,10,11,14,12,13,15,16,17,18,30,32&stats=bat&qual=0&type=0&team=&season={y}&seasonEnd={y}&org=&ind=0&splitTeam=false', f'milb_{y}_L{lv}.json', min_bytes=200)
    time.sleep(1.5)
for t in ('steamer', 'steamer600', 'fangraphsdc'):
    get(f'{FG}/projections?type={t}&stats=bat&pos=all&team=0&players=0&lg=all', f'{t}_2027.json')
SV = 'https://baseballsavant.mlb.com/leaderboard'
sel = ('pa,ab,hit,single,double,triple,home_run,strikeout,walk,k_percent,bb_percent,batting_avg,slg_percent,on_base_percent,'
       'xba,xslg,woba,xwoba,xobp,xiso,wobacon,xwobacon,bacon,xbacon,exit_velocity_avg,launch_angle_avg,sweet_spot_percent,'
       'barrel_batted_rate,hard_hit_percent,avg_best_speed,avg_hyper_speed,z_swing_percent,oz_swing_percent,iz_contact_percent,'
       'oz_contact_percent,whiff_percent,swing_percent,pull_percent,straightaway_percent,opposite_percent,groundballs_percent,'
       'flyballs_percent,linedrives_percent,popups_percent,sprint_speed,hp_to_1b,batted_ball,poorlyunder_percent,poorlytopped_percent,'
       'poorlyweak_percent,solidcontact_percent,flareburner_percent,meatball_swing_percent,in_zone_percent,edge_percent,f_strike_percent')
for y in range(2015, 2027):
    get(f'{SV}/custom?year={y}&type=batter&filter=&min=1&selections={sel}&chart=false&csv=true', f'sv_custom_{y}.csv')
    get(f'{SV}/expected_statistics?type=batter&year={y}&position=&team=&min=1&csv=true', f'sv_xstats_{y}.csv')
    get(f'{SV}/statcast?type=batter&year={y}&position=&team=&min=1&csv=true', f'sv_ev_{y}.csv')
    get(f'{SV}/sprint_speed?year={y}&position=&team=&min=0&csv=true', f'sv_sprint_{y}.csv')
    pass #get(f'{SV}/batted-ball?type=batter&seasonStart={y}&seasonEnd={y}&minSwings=1&minGroupSwings=1&csv=true', f'sv_bbprofile_{y}.csv', min_bytes=300)
    if y >= 2023:
        get(f'{SV}/bat-tracking?attackZone=&batSide=&contactType=&count=&dateStart={y}-03-01&dateEnd={y}-11-30&gameType=R&isHardHit=&minSwings=1&minGroupSwings=1&pitchHand=&pitchType=&seasonStart={y}&seasonEnd={y}&team=&type=batter&csv=true', f'sv_bat_{y}.csv', min_bytes=300)
    time.sleep(1)
