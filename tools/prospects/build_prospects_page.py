"""Build minors_prospects.html (Prospect Ranks) from prospects_2026_scored.csv.
Model: see the Baseball projections Project, prospect_model/README.md."""
import json, re, pandas as pd, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
a=pd.read_csv(pathlib.Path(__file__).with_name('prospects_2026_scored.csv')).sort_values('y10',ascending=False).reset_index(drop=True)
css=re.search(r'<style>(.*?)</style>',(ROOT/'aaa.html').read_text(),re.S).group(1)
C=[dict(n='Rank',f='int',t='Rank by P(10+ career WAR)',d='asc'),dict(n='Player',f='txt',d='asc'),dict(n='Team',f='txt',t='MLB organization in 2026 (most PA first if he changed orgs)',d='asc'),
   dict(n='Pos',f='txt',t='2026 share of games by position (MLB Stats API). C, SS and CF get the biggest boosts.',d='asc'),
   dict(n='Level',f='txt',t='Levels whose stats are used (see Stats)',d='asc'),
   dict(n='Stats',f='txt',t='2026 = 150+ PA at one level; 2026 combined = 150+ PA in 2026 but split so no level reached 150 (levels pooled); 2025 = fewer than 150 PA in 2026 (usually injury): starts from his 2025 season, lowered for the missed time and adjusted for his limited 2026 hitting; Level, PA and the z columns are from 2025',d='asc'),
   dict(n='Age',f='f1',t='Age on July 1, 2026',d='asc'),dict(n='Age vs lg',f='f1s',t='Years older (+) or younger (−) than the PA-weighted average age of his league in the season used',d='asc'),
   dict(n='PA',f='int',t='PA in the season used (A, A+, AA and AAA only)'),dict(n='MLB AB',f='int',t='Career MLB at-bats through 2026 (must be under 130 to be listed)'),
   dict(n='10+ WAR',f='pct',g=1,t='Probability of 10+ career MLB fWAR'),dict(n='3+ WAR season',f='pct',t='Probability of at least one 3+ fWAR season'),
   dict(n='20+ WAR',f='pct',t='Probability of 20+ career fWAR'),dict(n='5+ WAR season',f='pct',t='Probability of at least one 5+ fWAR season'),
   dict(n='wOBA z',f='zc',g=1,t='Park-adjusted wOBA, SDs vs. his league-season'),dict(n='K% z',f='zr',t='Park-adjusted K%, SDs vs. league (negative = fewer strikeouts, good)'),
   dict(n='ISO z',f='zc',t='Park-adjusted ISO, SDs vs. league'),dict(n='BB% z',f='zc',t='Park-adjusted unintentional BB%, SDs vs. league'),
   dict(n='Spd z',f='zc',t='FanGraphs Speed Score, SDs vs. league'),dict(n='SwStr% z',f='zr',t='Swinging-strike rate, SDs vs. league (negative = fewer whiffs, good)')]
for c in C: c.setdefault('g',0); c.setdefault('t',''); c.setdefault('d','')
D=[[i+1,r['name'],r.team,r.pos26,r.levels,r.basis,round(r.age,1),round(r.agerel,1),int(r.PA),int(r.mlbab),round(r.y10*100,1),round(r.s3*100,1),round(r.y20*100,1),round(r.s5*100,1),
    round(r.wOBAa,2),round(r.Ka,2),round(r.ISOa,2),round(r.BBr,2),round(r.Spd,2),round(r.SwStr,2)] for i,r in a.iterrows()]
nav=('<nav><span class="lvl">MINORS</span><a href="aaa.html" class="">AAA Overview</a><a href="aaa_decisions.html" class="">AAA Decisions</a>'
     '<a href="aaa_contact.html" class="">AAA Contact</a><a href="aaa_power.html" class="">AAA Power</a><a href="minors_prospects.html" class="on">Prospect Ranks</a>'
     '<a class="jump" href="index.html">MLB &rarr;</a><a href="scoresheet.html">Scoresheet &rarr;</a></nav>')
explain=('<div class="explain">The chance each 2026 Low-A, High-A, AA, and AAA hitter (under 130 career MLB at-bats through 2026) becomes a 10+ career WAR player, has a 3+ WAR season, reaches 20+ career WAR, or has a 5+ WAR season.</div>')
method=('<div class="explain" style="margin-top:14px"><b>How it works:</b> a logistic regression trained on minor-league seasons at Low-A and above (2007–2014 seasons for career outcomes, 2007–2018 for single-season outcomes). '
 'Its raw probabilities are then <b>recalibrated</b>: the model is refit five times, each time leaving out a fifth of the players and predicting them, and the predictions for those unseen players are compared with what actually happened to them. A small correction curve is fit so that, for example, players given 20% really did succeed about 20% of the time. In practice it pulls the most extreme probabilities slightly toward the middle. '
 'Outcomes are total FanGraphs position-player WAR (fWAR: batting, baserunning, fielding, positional). Every stat is compared with the player\'s own league that season, and a player at two levels gets a PA-weighted blend.<br>'
 '<b>Major factors</b> (odds multiplier for 10+ WAR, all else equal): <b>age vs. league</b> (birthdate, July 1), ×2.4 per year younger; park-adjusted <b>wOBA</b>, ×1.9 per SD; park-adjusted <b>ISO</b>, ×1.4 per SD; <b>Speed Score</b>, ×1.35 per SD; park-adjusted <b>K%</b>, ×1.35 per SD fewer strikeouts; <b>share of games at each position</b>, for a full season at C or SS ×5.5, CF ×4, 3B ×1.9, 2B ×1.1 (vs. 1B/DH; LF/RF ≈ 1B/DH). '
 'For 20+ WAR and 5+ WAR seasons, <b>the prior season\'s wOBA</b> also counts about as much as the current one (×2 per SD).<br>'
 '<b>Minor factors:</b> park-adjusted BB%; SwStr%, Pull%, and GB/LD/FB rates; the prior season\'s age, K%, ISO, and BB%, level, and prior MLB at-bats.<br>'
 'Cross-validated accuracy (AUC): 10+ WAR .89, 3+ WAR season .89, 20+ WAR .92, 5+ WAR season .93 (AAA seasons alone: .88, .87, .90, .92). '
 'Caveat: a player who DHed because of an injury is treated like a 1B/DH.<br>'
 '<b>Who\'s covered:</b> hitters with 150+ PA in 2026 at Low-A or higher and fewer than 130 career MLB at-bats through 2026. '
 'A hitter with fewer than 150 such PA in 2026 (usually because of injury) is included if he had 150+ PA at a level in 2025 (Stats = “2025”). His probability starts from his 2025 season, is lowered to reflect how hitters who missed most of a season have historically fared, and is adjusted for how he hit in his limited 2026 PA; it never ends up higher than his 2025 season alone would give. '
 'Arizona Fall League and other off-season stats are not used.</div>')
ctrl=('<div class="controls"><input type="search" id="q" placeholder="Filter by player or team…" aria-label="Filter by player or team">'
 '<span class="lvls">Level <label><input type="checkbox" class="lvck" value="AAA" checked> AAA</label><label><input type="checkbox" class="lvck" value="AA" checked> AA</label><label><input type="checkbox" class="lvck" value="A+" checked> High-A</label><label><input type="checkbox" class="lvck" value="A" checked> Low-A</label></span>'
 '<label>Position <select id="ps"><option value="">All</option>'+''.join(f'<option value="{p}">{p}</option>' for p in ['C','1B','2B','3B','SS','LF/RF','CF','DH'])+'</select></label>'
 '<span id="count" style="color:var(--muted)"></span></div>')
foot=('<footer>Hover over a column header for its definition. Click a header to sort; click again to reverse. A player shows if any of his 2026 levels is checked; the position filter matches any listed position. '
 'Data: FanGraphs minor- and major-league leaderboards; birthdates from the Chadwick Bureau register; games by position from the MLB Stats API; park factors built from MLB Stats API home/road splits. Pulled Nov 2026.'
 '<p class="credit">Built with help from Claude (Anthropic).</p></footer>')
js=r"""const tb=document.querySelector('#t tbody'),q=document.getElementById('q'),lvs=[...document.querySelectorAll('.lvck')],ps=document.getElementById('ps'),cnt=document.getElementById('count');
const f2=x=>(x>0?'+':'')+x.toFixed(2);
const fmt=(v,f)=>v==null?'':f==='int'?v.toLocaleString():f==='pct'?v.toFixed(1)+'%':f==='f1'?v.toFixed(1):f==='f1s'?(v>0?'+':'')+v.toFixed(1):f2(v);
document.querySelector('#t thead tr').innerHTML=C.map((c,i)=>`<th data-k="${i}" class="${c.f==='txt'?'l':''} ${c.g?'grp':''}" title="${c.t||''}">${c.n}</th>`).join('');
function render(){const s=q.value.trim().toLowerCase();
 const rows=D.filter(r=>(!s||r[1].toLowerCase().includes(s)||r[2].toLowerCase().includes(s))&&(()=>{const on=lvs.filter(x=>x.checked).map(x=>x.value);return r[4].split('/').some(l=>on.includes(l))})()&&(!ps.value||r[3].split(', ').some(x=>x.startsWith(ps.value+' '))))
  .sort((a,b)=>{const x=a[key],y=b[key];return (typeof x==='string'?x.localeCompare(y):x-y)*dir});
 tb.innerHTML=rows.map(r=>'<tr>'+C.map((c,i)=>{const v=r[i];const cl=[c.f==='txt'?'l':'',c.g?'grp':'',c.f==='zc'?(v>=0?'pos':'neg'):'',c.f==='zr'?(v<=0?'pos':'neg'):''].join(' ');return `<td class="${cl}">${c.f==='txt'?v:fmt(v,c.f==='zr'?'zc':c.f)}</td>`}).join('')+'</tr>').join('');
 cnt.textContent=rows.length+' hitters';
 document.querySelectorAll('th').forEach(th=>th.setAttribute('aria-sort',+th.dataset.k===key?(dir>0?'ascending':'descending'):'none'));}
document.querySelectorAll('th').forEach(th=>th.addEventListener('click',()=>{const k=+th.dataset.k;if(k===key)dir=-dir;else{key=k;dir=(C[k].d==='asc')?1:-1}render()}));
q.addEventListener('input',render);lvs.forEach(x=>x.addEventListener('change',render));ps.addEventListener('change',render);
render();"""
html=('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'
 f'<title>2026 Prospect Ranks</title><style>{css}\n.lvls{{display:inline-flex;gap:10px;align-items:center}}.lvls label{{display:inline-flex;gap:4px;align-items:center}}</style></head>\n<body><main>\n{nav}\n'
 '<h1>2026 Prospect Ranks</h1><p class="sub">Chance of MLB success from 2026 Low-A through Triple-A stats</p>\n'
 f'{explain}\n{ctrl}\n<div class="wrap dense"><table id="t"><thead><tr></tr></thead><tbody></tbody></table></div>\n{method}\n{foot}\n'
 f'</main><script>const D={json.dumps(D,ensure_ascii=False,separators=(",",":"))},C={json.dumps(C)};let key=10,dir=-1;\n{js}</script></body></html>\n')
(ROOT/'minors_prospects.html').write_text(html)
print(len(D),'rows',len(html),'bytes')
