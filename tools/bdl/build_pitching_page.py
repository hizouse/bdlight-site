"""Build projections_p.html (BDL P Projections: 2027 pitcher ERA) from tools/bdl/pitching/*.csv.
The CSVs come from the Baseball projections Project's pitching_era_study (scripts/project2027.py, copied here).
usage: python tools/bdl/build_pitching_page.py SITE_DIR "Nov 20"
Page styling and the MLB nav are taken from projections_h.html."""
import sys, re, json, csv, os
SITE, DAY = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__)); PD = f'{HERE}/pitching'
num = lambda v, f=float: None if v in ('', None) else f(v)

P = list(csv.DictReader(open(f'{PD}/bdl_pitcher_era_2027.csv', encoding='utf-8')))
T = list(csv.DictReader(open(f'{PD}/team_defense_2027.csv', encoding='utf-8')))
rows = []
for r in P:
    ip, gs = int(r['dc_IP']), int(r['steamer_GS'])
    st, bd = float(r['steamer_ERA']), float(r['BDL_ERA'])
    rows.append([0, r['Name'], r['Team'] or '', 'SP' if gs >= 5 else 'RP', ip, gs, num(r['steamer_FIP']), st, bd, round(bd - st, 2),
                 num(r['adj_stuff']), num(r['adj_shrink']), num(r['adj_defense']), num(r['Stuff+_reg']), num(r['Location+_reg']), int(r['prior_pitches'])])
col = lambda n, f, t, d='desc', g=False: {"n": n, "f": f, "t": t, "d": d, "g": g}
C = [col('Rk', 'int', 'Rank among the pitchers shown by the column you sorted (by BDL ERA when sorting by Rk or a text column)', 'asc'),
     col('Player', 'txt', 'Pitcher', 'asc'), col('Team', 'txt', 'FanGraphs Depth Charts team (blank = free agent)', 'asc'),
     col('Role', 'txt', 'SP = 5+ projected starts (Steamer), else RP', 'asc'),
     col('IP', 'int', '2027 innings, FanGraphs Depth Charts', g=True), col('GS', 'int', '2027 starts, Steamer'),
     col('Stmr FIP', 'f2', 'Steamer 2027 FIP', 'asc', True), col('Stmr ERA', 'f2', 'Steamer 2027 ERA', 'asc'),
     col('BDL ERA', 'f2', 'BDL 2027 ERA = Steamer ERA + the three adjustments to the right', 'asc'),
     col('Δ ERA', 'e2', 'BDL ERA minus Steamer ERA (green = BDL projects a lower ERA)', 'asc'),
     col('Stuff adj', 'e2', 'Adjustment from regressed 2025-26 Stuff+ and Location+ (FanGraphs pitch models)', 'asc', True),
     col('Avg adj', 'e2', 'Steamer’s distance from the league-average ERA, cut by 26% (pays off once Stuff+ is in)', 'asc'),
     col('Def adj', 'e2', 'Adjustment for his team’s projected defense (DRS of its Depth Charts fielders)', 'asc'),
     col('Stuff+', 'f1', 'Stuff+ for 2025-26 (2026 counts double), pitch-weighted and regressed toward 100 (600 pitches); 100 = no MLB data', g=True),
     col('Loc+', 'f1', 'Location+, same weighting and regression'), col('Pitches', 'int', 'MLB pitches behind the Stuff+ figure (2026 + half of 2025)')]
TD = sorted(([r['team'], round(float(r['def_runs_1450ip'])), float(r['def_r9'])] for r in T), key=lambda x: -x[1])
adj_by_team = {}
for r in P:
    if r['Team']: adj_by_team.setdefault(r['Team'], float(r['adj_defense']))
TD = [[i + 1, t, runs, adj_by_team.get(t)] for i, (t, runs, _) in enumerate(TD)]

hp = open(f'{SITE}/projections_h.html', encoding='utf-8').read()
css = hp[hp.index('<style>') + 7:hp.index('</style>')]
css = re.sub(r'[^{}]*nth-child[^{}]*\{[^{}]*\}', '', css)
css += ('.t th:nth-child(1),.t td:nth-child(1){position:sticky;left:0;width:44px;min-width:44px;max-width:44px;z-index:1;background:var(--bg)}'
        '.t th:nth-child(2),.t td:nth-child(2){position:sticky;left:44px;min-width:170px;z-index:1;text-align:left;background:var(--bg);box-shadow:inset -1px 0 0 var(--line)}'
        '.t thead th{position:sticky;top:0;z-index:2}.t thead th:nth-child(1),.t thead th:nth-child(2){z-index:3;background:var(--head)}'
        '.t tbody tr:nth-child(even) td:nth-child(1),.t tbody tr:nth-child(even) td:nth-child(2){background:var(--row)}'
        'tbody tr:nth-child(even){background:var(--row)}h2{font-size:1.15rem;margin:26px 0 8px}.wrap.narrow{max-width:520px}')
nav = re.search(r'<nav>.*?</nav>', hp).group(0).replace('class="on"', 'class=""').replace('href="projections_p.html" class=""', 'href="projections_p.html" class="on"')
teams = sorted({r[2] for r in rows if r[2]})
best, worst = TD[0], TD[-1]
html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BDL 2027 Pitcher Projections</title><style>{css}</style></head>
<body><main>
{nav}
<h1>BDL 2027 Pitcher Projections</h1><p class="sub">Steamer ERA adjusted for Stuff+ and projected team defense · {len(rows)} pitchers on FanGraphs Depth Charts</p>
<div class="explain"><b>BDL ERA</b> starts from Steamer&rsquo;s 2027 ERA and adds three adjustments: <b>Stuff</b> (about &minus;0.03 ERA per point of regressed Stuff+ above average; Location+ adds almost nothing), <b>Avg</b> (Steamer&rsquo;s distance from league average is cut by 26%, which only helps once Stuff+ is in), and <b>Def</b> (&minus;0.8 ERA per run per 9 innings of projected team defense: each fielder&rsquo;s regressed 2024&ndash;26 DRS times his Depth Charts playing time; a +30-run defense is worth about &minus;0.15 ERA). Free agents get league-average defense until they sign. The average projected ERA is unchanged from Steamer&rsquo;s.<br>
<b>Backtest.</b> Each season from 2021 to 2026 was projected with weights fit on the other seasons and graded on every pitcher with a preseason Steamer projection and 30+ MLB innings (2,812 pitcher-seasons; IP-weighted ERA error, both systems shifted to each season&rsquo;s average). Steamer 1.065, BDL 1.055, better in 100% of bootstrap resamples; using only earlier seasons to fit, 1.057 &rarr; 1.051. For pitchers with 60+ IP, the Stuff and Avg adjustments alone cut the error from 0.943 to 0.931. Single-season ERA is mostly noise, so these are small gains: Steamer explains about 17% of the spread in pitcher ERA and BDL about 18%. Steamer does not account for team defense; DRS beat Statcast OAA and Fielding Run Value as the defense measure, and Pitching+, PitchingBot, and plain stats (K&minus;BB%, SIERA, xFIP) added less than Stuff+.<br>
<b>Caveats.</b> FanGraphs computes Stuff+ for past seasons with its current model, which may flatter the backtest a little. Extreme Stuff+ relievers (sidearmers especially) get large adjustments; treat those with some skepticism. Pitchers with no MLB pitch data get essentially no Stuff adjustment.</div>
<div class="controls"><input type="search" id="q" placeholder="Search pitcher…"><label>Team <select id="tm"><option value="">All</option><option value="-">Free agents</option>{''.join(f'<option>{t}</option>' for t in teams)}</select></label><label>Role <select id="ro"><option value="">All</option><option>SP</option><option>RP</option></select></label><label>Min IP <select id="mi"><option value="0">0</option><option value="20" selected>20</option><option value="50">50</option><option value="100">100</option><option value="150">150</option></select></label><span id="count"></span></div>
<div class="wrap dense"><table class="t" id="t"><thead><tr></tr></thead><tbody></tbody></table></div>
<h2 id="defense">Projected team defense</h2>
<p class="sub">Depth Charts fielders&rsquo; regressed DRS, in runs per 1,450 innings (about a season), and the ERA adjustment it gives that team&rsquo;s pitchers. Best: {best[1]} {best[2]:+d}; worst: {worst[1]} {worst[2]:+d}.</p>
<div class="wrap dense narrow"><table class="t" id="tt"><thead><tr><th data-k="0" title="Rank by projected defense" class="">Rk</th><th data-k="1" class="l" title="Team">Team</th><th data-k="2" title="Projected defensive runs saved per 1,450 innings">Def runs</th><th data-k="3" title="ERA adjustment for this team’s pitchers">ERA adj</th></tr></thead><tbody></tbody></table></div>
<footer>Click a header to sort; click again to reverse. Sources: Steamer 2027 and 2014&ndash;26 preseason Steamer and ZiPS pitcher projections, FanGraphs Depth Charts 2027, FanGraphs pitching (Stuff+, Location+, Pitching+, PitchingBot) and fielding (DRS, OAA, Fielding Run Value) 2014&ndash;26. Built {DAY}, 2026.<p class="credit">Built with help from Claude (Anthropic).</p></footer>
<script>
const C={json.dumps(C, ensure_ascii=False)};
const D={json.dumps(rows, ensure_ascii=False, separators=(',', ':'))};
const TD={json.dumps(TD, ensure_ascii=False, separators=(',', ':'))};
const fmt=(v,f)=>v==null?'':f==='int'?String(v):f==='f1'?v.toFixed(1):f==='f2'?v.toFixed(2):(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(2);
const tb=document.querySelector('#t tbody'),q=document.getElementById('q'),tm=document.getElementById('tm'),ro=document.getElementById('ro'),mi=document.getElementById('mi'),cnt=document.getElementById('count');
const NI=1,TI=2,RI=3,II=4,BI=C.findIndex(c=>c.n==='BDL ERA');let key=BI,dir=1;
document.querySelector('#t thead tr').innerHTML=C.map((c,i)=>`<th data-k="${{i}}" class="${{c.f==='txt'?'l':''}} ${{c.g?'grp':''}}" title="${{c.t}}">${{c.n}}</th>`).join('');
const cmp=(k,d)=>(a,b)=>{{const x=a[k],y=b[k];if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;return (typeof x==='string'?x.localeCompare(y):x-y)*d}};
const fold=x=>String(x).normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
function render(){{const s=fold(q.value.trim()),t=tm.value,r=ro.value,m=+mi.value;
 const rows=D.filter(x=>(!s||fold(x[NI]).includes(s))&&(!t||(t==='-'?!x[TI]:x[TI]===t))&&(!r||x[RI]===r)&&x[II]>=m);
 let k=key;if(k===0||C[k].f==='txt')k=BI;const R=new Map();rows.slice().sort(cmp(k,C[k].d==='asc'?1:-1)).forEach((x,i)=>R.set(x,i+1));
 const val=(x,i)=>i===0?R.get(x):x[i];
 rows.sort((a,b)=>{{const x=val(a,key),y=val(b,key);if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;return (typeof x==='string'?x.localeCompare(y):x-y)*dir}});
 tb.innerHTML=rows.map(x=>'<tr>'+C.map((c,i)=>{{const v=val(x,i);const cl=[c.f==='txt'?'l':'',c.g?'grp':'',c.f==='e2'&&v?(v<0?'pos':'neg'):''].join(' ');return `<td class="${{cl}}"${{i===NI?` title="${{v}}"`:''}}>${{c.f==='txt'?v:fmt(v,c.f)}}</td>`}}).join('')+'</tr>').join('');
 cnt.textContent=rows.length+' pitchers';
 document.querySelectorAll('#t th').forEach(th=>th.setAttribute('aria-sort',+th.dataset.k===key?(dir>0?'ascending':'descending'):'none'));}}
document.querySelectorAll('#t th').forEach(th=>th.addEventListener('click',()=>{{const k=+th.dataset.k;if(k===key)dir=-dir;else{{key=k;dir=(C[k].d==='asc')?1:-1}}render()}}));
[q,tm,ro,mi].forEach(e=>e.addEventListener(e===q?'input':'change',render));render();
const ttb=document.querySelector('#tt tbody');let tk=0,td=1;
function rt(){{const o=TD.slice().sort(cmp(tk,td));ttb.innerHTML=o.map(x=>`<tr><td>${{x[0]}}</td><td class="l">${{x[1]}}</td><td class="${{x[2]>0?'pos':x[2]<0?'neg':''}}">${{x[2]>0?'+':x[2]<0?'−':''}}${{Math.abs(x[2])}}</td><td class="${{x[3]<0?'pos':x[3]>0?'neg':''}}">${{fmt(x[3],'e2')}}</td></tr>`).join('');
 document.querySelectorAll('#tt th').forEach(th=>th.setAttribute('aria-sort',+th.dataset.k===tk?(td>0?'ascending':'descending'):'none'));}}
document.querySelectorAll('#tt th').forEach(th=>th.addEventListener('click',()=>{{const k=+th.dataset.k;if(k===tk)td=-td;else{{tk=k;td=(k===1||k===0||k===3)?1:-1}}rt()}}));rt();
</script></body></html>
'''
open(f'{SITE}/projections_p.html', 'w', encoding='utf-8').write(html)
print('projections_p.html:', len(rows), 'pitchers,', len(TD), 'teams')
