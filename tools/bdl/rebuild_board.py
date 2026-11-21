"""Rebuild the FT poach board's hitter values, position ranks, and bands from the current FT Hitters page (blend rankings).
Pitchers, protections, names, and anyone already listed stay as they are; hitters who newly qualify are added."""
import sys, re, json, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boardlib import *
SITE = sys.argv[1]; DAY = sys.argv[2] if len(sys.argv) > 2 else 'Nov 16'; b = open(f'{SITE}/scoresheet_ft.html').read(); rows, recs = parse_board(b)
L, ix, D = lines_by_pin(open(f'{SITE}/scoresheet_ft_hitters.html').read()); pr = posranks(D, ix)
SSC = ('#6B8E23', '#D4E79E', '#F4C64E', '#E8D5BE')
moved = []
for i, r in enumerate(recs):
    r['ord'] = i; r['ss'] = any(c in r['style'] for c in SSC); r['raw'] = r['val']
    if r['pin'] in L: r['team'] = L[r['pin']][0][ix['FT']]   # follow trades recorded on the FT Hitters page
    if r['kind'] == 'v' and r['pin'] in L:
        val, lab, best = hitter_value(L[r['pin']], ix, pr); tail = r['rest'][r['rest'].index(','):] if ',' in r['rest'] else ''
        moved.append((r['nm'], r['val'], round(val, 1))); r['raw'] = val; r['val'] = round(val, 1); r['rest'] = ' ' + lab + tail
        if r['prot'] and any(x[ix['Pos']] == 'SS' for x in L[r['pin']]): r['ss'] = False   # shade unused for protected cells
# newly qualifying hitters (2.6+ or top 12 at a fielding position), with board name, 2026 fWAR if 2.0+, age on Nov 1 2026
ADD = {'Casey Schmitt': ('', 27), 'Vinnie Pasquantino': ('', 29), 'Kody Clemens': (", '26 2.5", 30), 'Ryan Jeffers': (", '26 2.6", 29), 'Luke Adams': ('', 22)}
onboard = {r['pin'] for r in recs}
for pin, ls in L.items():
    if pin in onboard: continue
    val, lab, best = hitter_value(ls, ix, pr); nm = best[ix['Player']].split(' ', 1)[1]
    if best[ix['Pos']] == 'DH' and len(ls) == 1: continue
    if round(val, 1) >= 2.6 or any(pr[id(x)] <= 12 and x[ix['Pos']] != 'DH' for x in ls):
        if nm not in ADD: print('NEW QUALIFIER needs board name / fWAR / age in ADD:', nm, round(val, 1), lab); continue
        war, age = ADD[nm]
        recs.append(dict(team=best[ix['FT']], pin=pin, prot=False, style='', nm=nm, kind='v', val=round(val, 1), raw=val, rest=f' {lab}{war}, age {age}', ord=10000 + pin, ss=False)); print('added', nm, 'Team', best[ix['FT']], round(val, 1), lab)
def age(r):
    m = re.search(r'age (\d+)', r['rest']); return int(m.group(1)) if m else None
def band(r):
    v = r['val']
    if v is not None and v >= 3.6: return 1
    if v is not None and v >= 2.6: return 2
    return 4 if ('BA#' in r['rest'] or ', IP ' in r['rest'] or v is None) else 3
def style(r):
    if r['prot']: return ''
    bd = band(r); a = age(r); ss = r['ss']
    if bd == 1: return 'background:#6B8E23;color:#fff' if ss else 'background:#2E8B57;color:#fff'
    if bd == 2:
        if a is not None and a <= 27: return 'background:#D4E79E;color:#000' if ss else 'background:#A9DFBF;color:#000'
        return 'background:#F4C64E;color:#000' if ss else 'background:#FFE699;color:#000'
    if bd == 3: return 'background:#E8D5BE;color:#000' if ss else 'background:#D9D9D9;color:#000'
    return 'background:#FBE5D6;color:#7F3F00' if ', IP ' in r['rest'] else 'background:#F8CBAD;color:#000'
def key(r):
    if band(r) == 4:
        if 'BA#' in r['rest'] and ', IP ' not in r['rest']: return (0, int(re.search(r'BA#(\d+)', r['rest']).group(1)), 0)
        return (1, -(r['val'] if r['val'] is not None else -9), r['ord'])
    return (-r['val'], -r['raw'] if r['kind'] == 'v' else 0, r['ord'])
LAB = {1: {0: '3.6+', 1: 'VORP .070+'}, 2: {0: '2.6–3.5', 1: '&lt; age 28', 4: 'Age 28+'}, 3: {0: 'Others', 1: 'Top 12 at pos', 2: 'or already', 3: 'listed'}, 4: {0: 'BA Top 50,', 1: 'then SP under', 2: '100 IP'}}
def cell(r, gap):
    w = f"<span class=w>{r['kind']}{r['val']:.1f}</span>" if r['kind'] else ''
    cls = 'c' + (' gap' if gap else '') + (' prot' if r['prot'] else ''); st = style(r)
    return f'<td class="{cls}" data-pin="{r["pin"]}"' + (f' style="{st}"' if st else '') + f'><span class="nm">{r["nm"]}</span><span class="meta">{w}{r["rest"]}</span></td>'
out = []; nrows = {}
for bd in (1, 2, 3, 4):
    cols = {t: sorted([r for r in recs if r['team'] == t and band(r) == bd], key=key) for t in range(1, 25)}; n = max(len(c) for c in cols.values()); nrows[bd] = n
    for i in range(n):
        gap = i == 0; tds = [f'<td class="lbl{" gap" if gap else ""}">{LAB[bd].get(i, "")}</td>']
        for t in range(1, 25): tds.append(cell(cols[t][i], gap) if i < len(cols[t]) else f'<td class="empty{" gap" if gap else ""}"></td>')
        out.append('<tr>' + ''.join(tds) + '</tr>')
cnt = ''.join(f'<td class="gap cnt">Protected {sum(r["prot"] for r in recs if r["team"] == t)}<br>Unprotected 2.6+: {sum((not r["prot"]) and band(r) <= 2 for r in recs if r["team"] == t)}</td>' for t in range(1, 25))
out.append('<tr><td class="lbl gap">Counts</td>' + cnt + '</tr>')
t0 = b.index('<table'); body = b.index('<tbody>', t0) + 7; poached = b.index('<tr class="poached">', t0)
assert b[body:poached].count('<tr') > 0
old_n = b[body:poached].count('data-pin')
b = b[:body] + ''.join(out) + b[poached:]
m = re.search(r'(\d+) players\. Built Nov \d+, 2026', b); assert m and int(m.group(1)) == old_n, (m and m.group(0), old_n)
b = b.replace(m.group(0), f'{len(recs)} players. Built {DAY}, 2026')
old_txt = 'bdlight.net Scoresheet 2027 VORP 20 (current rankings) on the WAR scale'   # first-run text swap; no-op once done
b = b.replace(old_txt, 'bdlight.net Scoresheet 2027 VORP 20 (current rankings, which use the Steamer600/BDL blend from the <a href="projections_h.html">BDL H Projections</a> page) on the WAR scale')
open(f'{SITE}/scoresheet_ft.html', 'w').write(b)
print('cells', old_n, '->', len(recs), 'rows per band', nrows, '| hitters revalued', len(moved), 'changed', sum(a != c for _, a, c in moved))
