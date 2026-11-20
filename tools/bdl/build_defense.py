"""Build scoresheet_defense.html (range, error, and catcher SB/CS projections) from the Rankings page data.
It has its own Defense tab in the Scoresheet nav (the hitting projections moved to projections_h.html under MLB)."""
import sys, re, json, numpy as np; sys.path.insert(0, '/home/claude/proj/site')
from boardlib import cd
SITE = sys.argv[1]; rk = open(f'{SITE}/scoresheet.html').read(); C, D, ix = cd(rk)
g = lambda r, n: r[ix[n]]
# position averages implied by the page: Def adj = (range - avg + err adj) x .54 OPS per 1.00 range
avg = {}
for p in ('1B', '2B', '3B', 'SS', 'OF'):
    v = [g(r, 'Proj Rng') + g(r, 'Err adj') - g(r, 'Def adj') / 0.54 for r in D if g(r, 'Pos') == p and g(r, 'Proj Rng') is not None]; avg[p] = float(np.median(v))
    print(p, 'implied average range %.3f (spread %.3f)' % (avg[p], np.std(v)), len(v))
F = [[0, g(r, 'Player').split(' ', 1)[1], g(r, 'Team'), g(r, 'Age'), g(r, 'Pos'), g(r, 'Other Pos'), g(r, 'Proj Rng'), round(g(r, 'Proj Rng') - avg[g(r, 'Pos')], 2), g(r, 'Err adj'), g(r, 'Def adj')]
     for r in D if g(r, 'Pos') in avg and g(r, 'Proj Rng') is not None]
K = [[0, g(r, 'Player').split(' ', 1)[1], g(r, 'Team'), g(r, 'Age'), g(r, 'C SB'), g(r, 'C CS'), g(r, 'C def'), g(r, 'Err adj'), g(r, 'Def adj')] for r in D if g(r, 'Pos') == 'C']
F.sort(key=lambda r: -r[9]); K.sort(key=lambda r: -(r[8] or 0)); print(len(F), 'fielder lines', len(K), 'catchers', sum(1 for r in D if g(r, 'Pos') in avg and g(r, 'Proj Rng') is None), 'fielder lines without a range')
col = lambda n, f, t, d='desc': {"n": n, "f": f, "t": t, "d": d}
CF = [col('Rk', 'int', 'Rank by the column you sorted (by Def adj when sorting by a text column)', 'asc'), col('Player', 'txt', 'Player', 'asc'), col('Team', 'txt', 'Steamer team (blank = free agent)', 'asc'), col('Age', 'int', '2027 MLB season age', 'asc'),
      col('Pos', 'txt', 'Position for this line (20+ games there in 2026, or his listed position)', 'asc'), col('Other Pos', 'txt', 'Other positions where he also has a line', 'asc'),
      col('Proj Rng', 'f2', 'Projected 2027 Scoresheet range at this position. OF ranges of 2.16+ are highlighted: above the ~2.15 average center fielder'),
      col('vs Avg', 's2', 'Projected range minus the position average used on the Rankings tab (' + ', '.join(f'{p} {avg[p]:.2f}' for p in avg) + ')'),
      col('Err adj', 'sz3', 'Error adjustment in range units (+ = fewer errors than average; 1 extra error per 10 games = -0.07)'),
      col('Def adj', 'sz3', 'Total defensive value in OPS points: (range vs average + error adjustment) at 0.10 range = .054 OPS. This is what the Rankings tab adds at OBP weight 1.0')]
CK = [col('Rk', 'int', 'Rank by the column you sorted (by Def adj when sorting by a text column)', 'asc'), col('Player', 'txt', 'Player', 'asc'), col('Team', 'txt', 'Steamer team (blank = free agent)', 'asc'), col('Age', 'int', '2027 MLB season age', 'asc'),
      col('SB', 'f2', 'Projected 2027 Scoresheet SB-allowed rating for his league (lower = better)', 'asc'), col('CS', 'f2', 'Projected 2027 Scoresheet CS rating (higher = better)'),
      col('SB/CS value', 'sz3', 'SB/CS ratings in OPS points (SB +0.20, CS -0.42 runs; scaled to 70% steal volume)'), col('Err adj', 'sz3', 'Catcher error adjustment (+ = fewer errors than average)'),
      col('Def adj', 'sz3', 'Total catcher defensive value in OPS points: SB/CS value plus the error adjustment. This is what the Rankings tab adds at OBP weight 1.0')]
pj = open(f'{SITE}/projections_h.html').read()   # styling only
SUBCSS = ''
nav = re.search(r'<nav>.*?</nav>', rk).group(0).replace(' class="on"', '').replace('<a href="scoresheet_defense.html">', '<a href="scoresheet_defense.html" class="on">')
assert 'scoresheet_defense.html" class="on"' in nav
css = pj[pj.index('<style>') + 7:pj.index('</style>')]
css = re.sub(r'[^{}]*nth-child[^{}]*\{[^{}]*\}', '', css); css = css.replace('#t thead th', '.t thead th')
css += '.t th:nth-child(1),.t td:nth-child(1){position:sticky;left:0;width:48px;min-width:48px;max-width:48px;z-index:1;background:var(--bg)}.t th:nth-child(2),.t td:nth-child(2){position:sticky;left:48px;min-width:170px;z-index:1;text-align:left;background:var(--bg);box-shadow:inset -1px 0 0 var(--line)}.t thead th:nth-child(1),.t thead th:nth-child(2){z-index:3;background:var(--head)}.t tbody tr:nth-child(even){background:var(--row)}.t tbody tr:nth-child(even) td:nth-child(1),.t tbody tr:nth-child(even) td:nth-child(2){background:var(--row)}'
css += 'td.cf{color:#b45309;font-weight:700}@media (prefers-color-scheme:dark){td.cf{color:#f5a524}}h2{font-size:1.15rem;margin:26px 0 8px}.wrap{max-height:80vh}'
html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scoresheet 2027 Defense Projections</title><style>{css}</style></head>
<body><main>
{nav}
<h1>Scoresheet 2027 Defense Projections</h1><p class="sub">Projected range and errors for {len(F)} fielder lines, and SB/CS ratings for {len(K)} catchers · hitters on the Rankings tab · <a href="#catchers" style="color:inherit">jump to catchers</a></p>
<div class="explain"><b>Range.</b> The projected 2027 Scoresheet range comes from 2025&ndash;26 DRS and OAA with errors backed out, lowered for heavy DH use at OF and 1B, and held within &plusmn;.07 of the 2026 range, as Scoresheet did for 2026. Players get one line per position where they played 20+ games in 2026. <span style="color:#b45309;font-weight:700">Highlighted</span> OF ranges of 2.16+ are above the ~2.15 average center fielder, whose range counts about 1.4&times; in the sim.<br>
<b>Errors.</b> Projected from each player&rsquo;s MLB errors per chance over recent seasons, weighted toward the latest and regressed heavily toward the position average, then converted to errors per game at the position&rsquo;s average chances. Err adj is in range units: one extra error per 10 games = &minus;0.07 range.<br>
<b>Def adj</b> is the total in OPS points, as added on the <a href="scoresheet.html">2027 Rankings</a> at OBP weight 1.0: range minus the position average plus the error adjustment, at 0.10 range = .027 OBP + .027 SLG.<br>
<b>Catchers</b> have no Scoresheet range. Their projected SB and CS ratings are valued at SB +0.20 and CS &minus;0.42 runs, scaled to the sim&rsquo;s lower steal volume (70% of MLB), plus a catcher error adjustment.</div>
<h2>Range and errors</h2>
<div class="controls"><input type="search" id="q" placeholder="Search player…"><label>Position <select id="lg"><option value="">All</option><option>1B</option><option>2B</option><option>3B</option><option>SS</option><option>OF</option></select></label><span id="count"></span></div>
<div class="wrap dense"><table class="t" id="tf"><thead><tr></tr></thead><tbody></tbody></table></div>
<h2 id="catchers">Catchers: SB/CS allowed</h2>
<div class="controls"><input type="search" id="qk" placeholder="Search catcher…"><span id="countk"></span></div>
<div class="wrap dense"><table class="t" id="tk"><thead><tr></tr></thead><tbody></tbody></table></div>
<footer>Click a header to sort; click again to reverse. Sources: FanGraphs fielding and catcher data 2024&ndash;26, Scoresheet player files and 2022&ndash;26 league results; range, error, and catcher models fitted to Scoresheet&rsquo;s published 2026 ratings. Same projections as the Rankings tab. Built Nov 16, 2026.<p class="credit">Built with help from Claude (Anthropic).</p></footer>
<script>
const CF={json.dumps(CF, ensure_ascii=False)};
const DF={json.dumps(F, ensure_ascii=False, separators=(',', ':'))};
const CK={json.dumps(CK, ensure_ascii=False)};
const DK={json.dumps(K, ensure_ascii=False, separators=(',', ':'))};
const fmt=(v,f)=>v==null?'':f==='int'?String(v):f==='f2'?v.toFixed(2):f==='s2'?(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(2):(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(3).replace(/^0/,'');
function table(id,C,D,qid,cid,word,sel){{
 const t=document.getElementById(id),tb=t.querySelector('tbody'),q=document.getElementById(qid),cnt=document.getElementById(cid),ps=sel?document.getElementById(sel):null;
 const NI=1,PI=C.findIndex(c=>c.n==='Pos'),RI=C.findIndex(c=>c.n==='Proj Rng'),AI=C.findIndex(c=>c.n==='Def adj');let key=0,dir=1;
 t.querySelector('thead tr').innerHTML=C.map((c,i)=>`<th data-k="${{i}}" class="${{c.f==='txt'?'l':''}}" title="${{c.t}}">${{c.n}}</th>`).join('');
 const fold=x=>String(x).normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
 function render(){{const s=fold(q.value.trim()),p=ps?ps.value:'';
  let k=key;if(k===0||C[k].f==='txt')k=AI;const d=C[k].d==='asc'?1:-1;
  const pool=D.filter(r=>!p||r[PI]===p);const R=new Map();pool.slice().sort((a,b)=>{{const x=a[k],y=b[k];if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;return (x-y)*d}}).forEach((r,i)=>R.set(r,i+1));
  const val=(r,i)=>i===0?R.get(r):r[i];
  const rows=pool.filter(r=>!s||fold(r[NI]).includes(s)).sort((a,b)=>{{const x=val(a,key),y=val(b,key);if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;return (typeof x==='string'?x.localeCompare(y):x-y)*dir}});
  tb.innerHTML=rows.map(r=>'<tr>'+C.map((c,i)=>{{const v=val(r,i);const cl=[c.f==='txt'?'l':'',(c.f==='sz3'||c.f==='s2')&&v!=null&&v!==0?(v>0?'pos':'neg'):'',(i===RI&&r[PI]==='OF'&&v!=null&&v>=2.155)?'cf':''].join(' ');return `<td class="${{cl}}">${{c.f==='txt'?(v||''):fmt(v,c.f)}}</td>`}}).join('')+'</tr>').join('');
  cnt.textContent=rows.length+' '+word;
  t.querySelectorAll('th').forEach(th=>th.setAttribute('aria-sort',+th.dataset.k===key?(dir>0?'ascending':'descending'):'none'));}}
 t.querySelectorAll('th').forEach(th=>th.addEventListener('click',()=>{{const k=+th.dataset.k;if(k===key)dir=-dir;else{{key=k;dir=(C[k].d==='asc')?1:-1}}render()}}));
 q.addEventListener('input',render);if(ps)ps.addEventListener('change',render);render();}}
table('tf',CF,DF,'q','count','lines','lg');table('tk',CK,DK,'qk','countk','catchers',null);
</script></body></html>'''
open(f'{SITE}/scoresheet_defense.html', 'w').write(html)
