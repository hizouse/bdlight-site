"""Build minors_stabilization.html: stabilization points used by the Prospect Ranks model (v6).
Source: Baseball projections Project, prospect_model/stabilization_v6.md and scripts/p_stab.py."""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
css = re.search(r'<style>(.*?)</style>', (ROOT / 'aaa.html').read_text(), re.S).group(1)
nav = ('<nav><span class="lvl">MINORS</span><a href="aaa.html" class="">AAA Overview</a><a href="aaa_decisions.html" class="">AAA Decisions</a>'
       '<a href="aaa_contact.html" class="">AAA Contact</a><a href="aaa_power.html" class="">AAA Power</a><a href="minors_prospects.html" class="on">Prospect Ranks</a>'
       '<a class="jump" href="index.html">MLB &rarr;</a><a href="scoresheet.html">Scoresheet &rarr;</a></nav>')
# stat, used, noise-math, halves, season-to-season ceiling, note
R = [('K%', 60, '53', '69', '128', ''), ('SwStr%', 65, '(23)', '—', '192', 'rough: counted per pitch, and pitches within a plate appearance aren\'t independent, so the noise math runs low'),
     ('FB%', 95, '95', '—', '220', ''), ('GB%', 100, '102', '—', '197', ''), ('BB%', 120, '108', '150', '232', ''),
     ('Speed Score', 150, '—', '—', '174', 'rough: only the season-to-season ceiling is available'), ('Pull%', 180, '181', '—', '319', ''),
     ('ISO', 200, '—', '198', '293', ''), ('wOBA', 400, '—', '390', '822', ''), ('LD%', 550, '547', '—', '1,940', '')]
rel = lambda n, m: f'{100 * n / (n + m):.0f}%'
rows = ''.join(f'<tr><td>{s}</td><td class="num"><b>{m}</b></td><td class="num">{a}</td><td class="num">{b}</td><td class="num">{c}</td>'
               + ''.join(f'<td class="num">{rel(n, m)}</td>' for n in (50, 150, 400)) + f'<td>{note}</td></tr>' for s, m, a, b, c, note in R)
html = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stabilization Points</title><style>{css}
table.st{{border-collapse:collapse;margin:10px 0 18px;font-size:.9rem}} table.st th,table.st td{{padding:5px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
table.st td.num,table.st th.num{{text-align:right;font-variant-numeric:tabular-nums}} .narrow{{max-width:900px}} .narrow p{{line-height:1.5}}</style></head><body>
{nav}
<h1>Stabilization Points</h1><p class="sub">How quickly minor-league hitting stats become trustworthy, and how Prospect Ranks uses that</p>
<div class="narrow">
<p>A hitter's stat line is part skill and part luck. The <b>stabilization point</b> is the number of plate appearances at which a stat is half skill and half noise. After <i>n</i> PA, the share that is skill is <i>n</i> ÷ (<i>n</i> + stabilization point). <a href="minors_prospects.html">Prospect Ranks</a> uses these numbers to pull each stat toward league average before scoring a hitter: a stat that stabilizes at 400 PA, seen over 400 PA, keeps half of its distance from average; over 150 PA, about a quarter.</p>
<table class="st"><thead><tr><th>Stat</th><th class="num">Used (PA)</th><th class="num">Noise math</th><th class="num">1st vs. 2nd half</th><th class="num">Season to season (ceiling)</th><th class="num">Skill share at 50 PA</th><th class="num">at 150 PA</th><th class="num">at 400 PA</th><th>Note</th></tr></thead><tbody>{rows}</tbody></table>
<p><b>Data:</b> Low-A, High-A, Double-A, and Triple-A hitters, 2006–2026 (pitchers hitting excluded). Batted-ball rates are counted per ball in play and swinging strikes per pitch; both are converted to PA (0.68 balls in play and 3.11 pitches per PA).</p>
<p><b>How they were found</b>, three ways:</p>
<ul>
<li><b>Noise math</b> (about 39,000 hitter-seasons with 100+ of the stat's denominator): pure luck in <i>n</i> chances spreads a rate by a known amount. The spread among hitters beyond that is real skill, and the stabilization point is where the two are equal. This works for stats that are simple rates: K%, BB%, and the batted-ball rates.</li>
<li><b>First half vs. second half</b> (13,333 hitters with 100+ PA at the same level in each half of a season, from the MLB Stats API): how well a hitter's first-half stat predicts his second-half stat. This covers ISO and wOBA too. It runs a little high, since some hitters really do change during a season.</li>
<li><b>Season to season</b> (hitters with 250+ PA in consecutive seasons): this mixes real development in with the noise, so it only gives a ceiling. It's the only estimate available for Speed Score.</li>
</ul>
<p>The values used are rounded from the first two methods where they agree. Level barely matters (K% stabilizes at about 50 PA in Low-A and 55 in Triple-A; BB% at 100 and 114), so one set is used for all four levels. The order matches the usual MLB rules of thumb: strikeouts settle fastest, then walks, then power, then results on balls in play (BABIP, about 850 PA, isn't a model input).</p>
<p><b>Does it help?</b> Yes, modestly. Refitting the model with the regressed stats improved accuracy on players it wasn't trained on for all five outcomes (10+ WAR AUC .900 → .902, beating the old version in 88–98% of resamples). Halving or doubling every stabilization point gave nearly the same result. Each level's stats are regressed by that level's PA: regressing by the season's total PA tested worse, because a short stint at a new level says less than the same PA spent at one level.</p>
<p><b>How it's applied:</b> both seasons the model uses are regressed, each by its own PA. A hitter who missed most of 2026 is scored from his regressed 2025 season, then adjusted for his limited 2026 hitting as the Prospect Ranks page describes.</p>
</div></body></html>'''
(ROOT / 'minors_stabilization.html').write_text(html); print('ok', len(html))
