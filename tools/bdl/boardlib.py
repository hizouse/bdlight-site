import re, json, subprocess, unicodedata
def cd(h):
    C = json.loads(re.search(r'const C=(\[.*?\]);\n', h, re.S).group(1)); D = json.loads(re.search(r'const D=(\[.*?\]);\n', h, re.S).group(1))
    return C, D, {c['n']: i for i, c in enumerate(C)}
def parse_board(b):
    t = b[b.index('<table'):b.index('</table>')]; rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S); recs = []
    for ri, r in enumerate(rows):
        tds = re.findall(r'<td([^>]*)>(.*?)</td>', r, re.S)
        for ci, (a, inner) in enumerate(tds):
            if 'data-pin' not in a: continue
            cls = re.search(r'class="([^"]*)"', a).group(1).split(); sty = re.search(r'style="([^"]*)"', a)
            nm = re.search(r'<span class="nm">(.*?)</span><span class="meta">', inner, re.S).group(1); meta = inner[inner.index('<span class="meta">') + 19:-7]
            w = re.search(r'<span class=w>([vrp])(-?[\d.]+)</span>', meta); rest = meta[w.end():] if w else meta
            recs.append(dict(row=ri, team=ci, pin=int(re.search(r'data-pin="(\d+)"', a).group(1)), prot='prot' in cls, style=sty.group(1) if sty else '', nm=nm, kind=w.group(1) if w else '', val=float(w.group(2)) if w else None, rest=rest, inner=inner))
    return rows, recs
def lines_by_pin(fth):
    C, D, ix = cd(fth); PIN = json.loads(re.search(r'const PIN=(\[.*?\]);', fth, re.S).group(1)); out = {}
    for n, r in enumerate(D):
        if PIN[n] is not None: out.setdefault(PIN[n], []).append(r)
    return out, ix, D
def posranks(D, ix):
    """Pos Rk by Adj OPS within position, as the rankings page shows by default."""
    pr = {}; cnt = {}
    for r in sorted(D, key=lambda r: -r[ix['Adj OPS']]):
        p = r[ix['Pos']]; cnt[p] = cnt.get(p, 0) + 1; pr[id(r)] = cnt[p]
    return pr
def hitter_value(lines, ix, pr):
    best = max(lines, key=lambda r: r[ix['VORP 20']]); v = best[ix['VORP 20']]
    val = 2.1 + 21.5 * v * (0.75 if best[ix['Pos']] == 'C' else 1)
    others = [f"{r[ix['Pos']]}#{pr[id(r)]}" for r in sorted(lines, key=lambda r: pr[id(r)]) if r is not best and pr[id(r)] <= 12]
    return val, f"{best[ix['Pos']]}#{pr[id(best)]}" + ''.join('/' + o for o in others), best
