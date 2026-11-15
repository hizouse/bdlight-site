"""Build scoresheet_depth.html (MLB depth charts in the layout of Matt's preseason depth-chart spreadsheet) from FanGraphs RosterResource.

Usage (from the repo root):  python3 tools/depth_charts.py            # fetch all 30 RosterResource pages, write the page
                             python3 tools/depth_charts.py --cache DIR  # reuse/keep downloaded pages in DIR
Needs network access to www.fangraphs.com. Data: each RosterResource depth-chart page embeds its roster as JSON (__NEXT_DATA__).
"""
import html as H, json, os, re, sys, urllib.request, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUG = {'BAL': 'orioles', 'BOS': 'red-sox', 'NYY': 'yankees', 'TBR': 'rays', 'TOR': 'blue-jays', 'CHW': 'white-sox', 'CLE': 'guardians', 'DET': 'tigers',
        'KCR': 'royals', 'MIN': 'twins', 'HOU': 'astros', 'LAA': 'angels', 'ATH': 'athletics', 'SEA': 'mariners', 'TEX': 'rangers',
        'ATL': 'braves', 'MIA': 'marlins', 'NYM': 'mets', 'PHI': 'phillies', 'WSN': 'nationals', 'CHC': 'cubs', 'CIN': 'reds', 'MIL': 'brewers',
        'PIT': 'pirates', 'STL': 'cardinals', 'ARI': 'diamondbacks', 'COL': 'rockies', 'LAD': 'dodgers', 'SDP': 'padres', 'SFG': 'giants'}
# row labels as in the spreadsheet (Scoresheet-style abbreviations)
LABEL = {'NYY': 'NYA', 'TBR': 'TB', 'CHW': 'CHA', 'KCR': 'KC', 'WSN': 'WSH', 'ARI': 'ARZ', 'SDP': 'SD', 'SFG': 'SF'}
DIVS = {'AL': [('AL East', ['BAL', 'BOS', 'NYY', 'TBR', 'TOR']), ('AL Central', ['CHW', 'CLE', 'DET', 'KCR', 'MIN']), ('AL West', ['HOU', 'LAA', 'ATH', 'SEA', 'TEX'])],
        'NL': [('NL East', ['ATL', 'MIA', 'NYM', 'PHI', 'WSN']), ('NL Central', ['CHC', 'CIN', 'MIL', 'PIT', 'STL']), ('NL West', ['ARI', 'COL', 'LAD', 'SDP', 'SFG'])]}
PCOLS = ['SP1', 'SP2', 'SP3', 'SP4', 'SP5', 'CL', 'SU8th', 'SU7th', 'MID1', 'MID2', 'MID3', 'MID4', 'MID5/LR/SP6']
HCOLS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH', 'Bench C', 'Bench IF', 'Bench IF/OF', 'Bench OF']
BENCH = {'C': 'Bench C', 'INF': 'Bench IF', '1B': 'Bench IF', '3B': 'Bench IF', '2B': 'Bench IF', 'SS': 'Bench IF', '1B/3B': 'Bench IF',
         'INF/OF': 'Bench IF/OF', 'OF/INF': 'Bench IF/OF', 'UTL': 'Bench IF/OF', '1B/OF': 'Bench IF/OF', 'OF/1B': 'Bench IF/OF', 'OF': 'Bench OF', 'DH': 'Bench OF'}


def fetch(abb, cache):
    path = os.path.join(cache, SLUG[abb] + '.html') if cache else None
    if path and os.path.exists(path) and '--refetch' not in sys.argv:
        t = open(path, encoding='utf-8').read()
    else:
        req = urllib.request.Request(f'https://www.fangraphs.com/roster-resource/depth-charts/{SLUG[abb]}', headers={'User-Agent': 'Mozilla/5.0 (bdlight.net depth charts)'})
        t = urllib.request.urlopen(req, timeout=90).read().decode('utf-8')
        if path: open(path, 'w', encoding='utf-8').write(t)
    d = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S).group(1))
    q = [x for x in d['props']['pageProps']['dehydratedState']['queries'] if x['queryKey'][0] == 'depth-charts-all'][0]['state']['data']
    return q['dataRoster']


def cell(r, kind):
    nm = H.escape(r['player'])
    hand = r.get('throws') if kind == 'P' else r.get('bats')
    tags = [x for x in [hand, (r.get('platoon') or '').strip()] if x]
    tip = '; '.join(x for x in [r.get('position1'), r.get('notes'), r.get('injurynotes')] if x)
    t = f' title="{H.escape(tip)}"' if tip else ''
    return f'<span class="p"{t}>{nm}' + (f' <small>{" ".join(H.escape(x) for x in tags)}</small>' if tags else '') + '</span>'


def team_rows(R):
    P = {c: [] for c in PCOLS}; Hh = {c: [] for c in HCOLS}; IL = {'P': [], 'H': [], 'RL': []}
    for r in [x for x in R if x['type'] == 'mlb-sp']:
        P[r['role'] if r['role'] in P else 'MID5/LR/SP6'].append(cell(r, 'P'))
    mids = 0
    for r in [x for x in R if x['type'] == 'mlb-bp']:
        role = r['role']
        if role == 'CL': P['CL'].append(cell(r, 'P'))
        elif role == 'SU8': P['SU8th'].append(cell(r, 'P'))
        elif role == 'SU7': P['SU7th'].append(cell(r, 'P'))
        elif role == 'MID' and mids < 4: mids += 1; P[f'MID{mids}'].append(cell(r, 'P'))
        else: P['MID5/LR/SP6'].append(cell(r, 'P') + (' <small class="r">LR</small>' if role == 'LR' else ''))
    for r in [x for x in R if x['type'] == 'mlb-sl']:
        Hh[r['position'] if r['position'] in Hh else 'DH'].append(cell(r, 'H'))
    for r in [x for x in R if x['type'] == 'mlb-bn']:
        Hh[BENCH.get(r['position'], 'Bench IF/OF')].append(cell(r, 'H'))
    for r in [x for x in R if x['type'].startswith('il')]:
        k = 'RL' if r['type'] == 'il-rl' else 'H' if r['type'] == 'il-pp' else 'P'
        note = (r.get('injurynotes') or r.get('notes') or '').strip()
        IL[k].append(cell(r, 'P' if k == 'P' else 'H') + (f' <small class="inj">{H.escape(note)}</small>' if note else ''))
    return P, Hh, IL


def table(lg, cols, data, title, cls=''):
    out = [f'<h2>{title}</h2><div class="wrap"><table class="dc {cls}"><thead><tr><th class="tm">Team</th>' + ''.join(f'<th>{H.escape(c)}</th>' for c in cols) + '</tr></thead><tbody>']
    for dname, teams in DIVS[lg]:
        out.append(f'<tr class="div"><td colspan="{len(cols) + 1}">{dname}</td></tr>')
        for a in teams:
            D = data[a]
            out.append(f'<tr><td class="tm"><a href="https://www.fangraphs.com/roster-resource/depth-charts/{SLUG[a]}" target="_blank" rel="noopener">{LABEL.get(a, a)}</a></td>'
                       + ''.join(f'<td>{"<br>".join(D[c]) if D[c] else ""}</td>' for c in cols) + '</tr>')
    return ''.join(out) + '</tbody></table></div>'


def main():
    cache = sys.argv[sys.argv.index('--cache') + 1] if '--cache' in sys.argv else None
    if cache: os.makedirs(cache, exist_ok=True)
    pit, hit, il, loads = {}, {}, {}, []
    for a in SLUG:
        R = fetch(a, cache)
        loads += [r['loaddate'] for r in R if r.get('loaddate')]
        pit[a], hit[a], il[a] = team_rows(R)
    asof = max(loads)[:10] if loads else datetime.date.today().isoformat()
    asof_txt = datetime.date.fromisoformat(asof).strftime('%b %-d, %Y')
    built = datetime.date.today().strftime('%b %-d, %Y')
    sec = {}
    for lg in ('AL', 'NL'):
        ild = {a: {'Pitchers': il[a]['P'], 'Position players': il[a]['H'], 'Restricted list': il[a]['RL']} for a in il}
        sec[lg] = (table(lg, PCOLS, pit, 'Pitchers', 'pit') + table(lg, HCOLS, hit, 'Lineups and benches', 'hit')
                   + table(lg, ['Pitchers', 'Position players', 'Restricted list'], ild, 'Injured and restricted lists', 'il'))
    nal = open(os.path.join(ROOT, 'scoresheet_nal_waivers.html'), encoding='utf-8').read()
    css = nal[nal.index('<style>') + 7:nal.index('</style>')]
    css = css[:css.index('.board{')] if '.board{' in css else css
    nav = re.search(r'<nav>.*?</nav>', open(os.path.join(ROOT, 'scoresheet.html'), encoding='utf-8').read(), re.S).group(0)
    nav = nav.replace(' class="on"', '').replace('<a href="scoresheet_depth.html">', '<a href="scoresheet_depth.html" class="on">')
    css += ('.dc{border-collapse:separate;border-spacing:0;font-size:.8rem;min-width:100%}'
            '.dc th{position:sticky;top:0;z-index:2;background:var(--head);color:#fff;padding:6px 8px;text-align:left;white-space:nowrap;cursor:default}'
            '.dc td{vertical-align:top;padding:5px 8px;border-top:1px solid var(--line);border-left:1px solid var(--line);min-width:118px;line-height:1.3;text-align:left;white-space:normal}'
            '.dc .tm{position:sticky;left:0;z-index:1;background:var(--bg);min-width:52px;width:52px;font-weight:700}.dc thead th.tm{z-index:3;background:var(--head)}'
            '.dc td.tm a{color:var(--fg);text-decoration:none}.dc td.tm a:hover{text-decoration:underline}'
            '.dc tr.div td{background:var(--row);color:var(--muted);font-size:.7rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:4px 8px;position:static}'
            '.dc tbody tr:nth-child(even){background:none}.dc .p{display:inline-block;white-space:nowrap}.dc small{color:var(--muted);font-size:.7rem;margin-left:2px}'
            '.dc small.inj{display:block;margin:0 0 3px}.dc.il td{min-width:260px}.dc.il td.tm{min-width:52px}'
            'h2{font-size:1.05rem;margin:26px 0 8px}.lgtabs{display:flex;gap:6px;margin:0 0 6px}'
            '.lgtabs button{font:inherit;padding:5px 16px;border:1px solid var(--line);border-radius:999px;background:none;color:var(--muted);cursor:pointer}'
            '.lgtabs button.on{background:var(--head);border-color:var(--head);color:#fff;font-weight:600}'
            '.wrap{overflow:auto;border:1px solid var(--line);border-radius:8px;max-height:none}')
    js = ("const sel=lg=>{document.querySelectorAll('.lg').forEach(s=>s.hidden=s.id!==lg);document.querySelectorAll('.lgtabs button').forEach(b=>b.classList.toggle('on',b.dataset.lg===lg));"
          "try{localStorage.setItem('dc_lg',lg)}catch(e){}};document.querySelectorAll('.lgtabs button').forEach(b=>b.addEventListener('click',()=>sel(b.dataset.lg)));"
          "let s0='AL';try{const s=localStorage.getItem('dc_lg');if(s==='NL')s0=s}catch(e){}sel(s0);")
    page = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>MLB Depth Charts</title><style>{css}</style></head>\n<body><main>\n{nav}\n'
            '<h1>2027 MLB Depth Charts</h1>'
            f'<p class="sub">Rotations, bullpen roles, lineups, benches, and injured lists for all 30 teams, from FanGraphs RosterResource · as of {asof_txt}</p>\n'
            '<div class="lgtabs"><button data-lg="AL">AL</button><button data-lg="NL">NL</button></div>\n'
            f'<section class="lg" id="AL">{sec["AL"]}</section><section class="lg" id="NL" hidden>{sec["NL"]}</section>\n'
            '<div class="explain" style="margin-top:22px"><b>Source.</b> Every depth chart on this page comes from '
            '<a href="https://www.fangraphs.com/roster-resource/depth-charts" target="_blank" rel="noopener">FanGraphs RosterResource</a>; '
            'all credit for the depth charts, roles, and injury notes goes to RosterResource. Click a team to open its RosterResource page. '
            '<b>Layout</b> follows Matt&rsquo;s preseason depth-chart spreadsheet. Small letters after a name: bats (hitters) or throws (pitchers), then any platoon role '
            '(vsR = starts against right-handers, vsL = against left-handers). Hover a name for positions and notes. '
            'Bullpen columns use RosterResource&rsquo;s roles: several names in CL, SU8th, or SU7th mean RosterResource lists a committee; '
            'the last column holds the fifth and later middle relievers, long relievers (LR), and any sixth starter. '
            'In the offseason, these are RosterResource&rsquo;s projected 2027 roles and will change with signings and trades. Refreshed weekly until Opening Day.</div>\n'
            f'<footer>Data: FanGraphs RosterResource, as of {asof_txt}. Page built {built}.'
            '<p class="credit">Built with help from Claude (Anthropic).</p></footer>\n'
            f'<script>{js}</script></main></body></html>')
    open(os.path.join(ROOT, 'scoresheet_depth.html'), 'w', encoding='utf-8').write(page)
    n = sum(len(v) for t in pit.values() for v in t.values()) + sum(len(v) for t in hit.values() for v in t.values())
    print(f'wrote scoresheet_depth.html: {n} depth-chart entries, data as of {asof}')


if __name__ == '__main__':
    main()
