"""Build minors_prospects.html (Prospect Ranks) from prospects_2026_scored.csv.
Model: see the Baseball projections Project, prospect_model/README.md."""
import json, re, pandas as pd, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
a=pd.read_csv(pathlib.Path(__file__).with_name('prospects_2026_scored.csv')).sort_values('y10',ascending=False).reset_index(drop=True)
css=re.search(r'<style>(.*?)</style>',(ROOT/'aaa.html').read_text(),re.S).group(1)
C=[dict(n='Rank',f='int',t='Rank by P(10+ career WAR)',d='asc'),dict(n='Player',f='txt',d='asc'),dict(n='Team',f='txt',t='MLB organization in 2026 (most PA first if he changed orgs)',d='asc'),
   dict(n='Pos',f='txt',t='2026 share of games by position (MLB Stats API). C, SS and CF get the biggest boosts.',d='asc'),
   dict(n='Level',f='txt',t='2026 levels with 150+ PA',d='asc'),
   dict(n='Age',f='f1',t='Age on July 1, 2026',d='asc'),dict(n='Age vs lg',f='f1s',t='Years older (+) or younger (−) than the PA-weighted average age of his league',d='asc'),
   dict(n='PA',f='int',t='2026 PA at A, A+, AA and AAA (levels with 150+ PA)'),
   dict(n='10+ WAR',f='pct',g=1,t='Probability of 10+ career MLB fWAR'),dict(n='3+ WAR season',f='pct',t='Probability of at least one 3+ fWAR season'),
   dict(n='20+ WAR',f='pct',t='Probability of 20+ career fWAR'),dict(n='5+ WAR season',f='pct',t='Probability of at least one 5+ fWAR season'),
   dict(n='wOBA z',f='zc',g=1,t='Park-adjusted wOBA, SDs vs. his league-season'),dict(n='K% z',f='zr',t='Park-adjusted K%, SDs vs. league (negative = fewer strikeouts, good)'),
   dict(n='ISO z',f='zc',t='Park-adjusted ISO, SDs vs. league'),dict(n='BB% z',f='zc',t='Park-adjusted unintentional BB%, SDs vs. league'),
   dict(n='Spd z',f='zc',t='FanGraphs Speed Score, SDs vs. league'),dict(n='SwStr% z',f='zr',t='Swinging-strike rate, SDs vs. league (negative = fewer whiffs, good)')]
for c in C: c.setdefault('g',0); c.setdefault('t',''); c.setdefault('d','')
D=[[i+1,r['name'],r.team,r.pos26,r.levels,round(r.age,1),round(r.agerel,1),int(r.PA),round(r.y10*100,1),round(r.s3*100,1),round(r.y20*100,1),round(r.s5*100,1),
    round(r.wOBAa,2),round(r.Ka,2),round(r.ISOa,2),round(r.BBr,2),round(r.Spd,2),round(r.SwStr,2)] for i,r in a.iterrows()]
nav=('<nav><span class="lvl">MINORS</span><a href="aaa.html" class="">AAA Overview</a><a href="aaa_decisions.html" class="">AAA Decisions</a>'
     '<a href="aaa_contact.html" class="">AAA Contact</a><a href="aaa_power.html" class="">AAA Power</a><a href="minors_prospects.html" class="on">Prospect Ranks</a>'
     '<a class="jump" href="index.html">MLB &rarr;</a><a href="scoresheet.html">Scoresheet &rarr;</a></nav>')
explain=('<div class="explain">The chance each 2026 Low-A, High-A, AA, and AAA hitter (150+ PA at a level, under 130 career MLB at-bats before 2026) becomes a 10+ career WAR player, has a 3+ WAR season, reaches 20+ career WAR, or has a 5+ WAR season. '
 'A logistic regression trained on 2007–2014 seasons (career outcomes) and 2007–2018 seasons (single-season outcomes), then recalibrated; outcomes are total FanGraphs position-player WAR (fWAR: batting, baserunning, fielding, positional). '
 'Inputs, each compared with the player\'s own league that season: <b>age vs. league</b> (birthdate, July 1), park-adjusted <b>wOBA, K%, ISO, BB%</b>, plus <b>Speed Score</b>, <b>SwStr%</b>, <b>Pull%</b>, and GB/LD/FB rates; '
 'the prior season\'s age and stats; level; prior MLB at-bats; and <b>share of games at each position</b>. A player at two levels gets a PA-weighted blend.<br>'
 'Biggest factors for 10+ WAR (odds multiplier, all else equal): each year younger than league ×2.4; +1 SD wOBA ×1.9; +1 SD ISO ×1.4; +1 SD Speed ×1.3; 1 SD fewer strikeouts ×1.35; a full season at C or SS ×5.5, CF ×4 (vs. 1B/DH).<br>'
 'Cross-validated accuracy (AUC): 10+ WAR .89, 3+ WAR season .89, 20+ WAR .92, 5+ WAR season .93 (AAA seasons alone: .88, .87, .90, .92). '
 'Caveat: a player who DHed because of an injury is treated like a 1B/DH. Hitters with 130+ MLB at-bats before 2026 aren\'t included.</div>')
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
 f'{explain}\n{ctrl}\n<div class="wrap dense"><table id="t"><thead><tr></tr></thead><tbody></tbody></table></div>\n{foot}\n'
 f'</main><script>const D={json.dumps(D,ensure_ascii=False,separators=(",",":"))},C={json.dumps(C)};let key=8,dir=-1;\n{js}</script></body></html>\n')
(ROOT/'minors_prospects.html').write_text(html)
print(len(D),'rows',len(html),'bytes')
